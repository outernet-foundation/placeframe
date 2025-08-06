from __future__ import annotations

import json
from pathlib import Path

from pulumi import Config, Output, StackReference, export
from pulumi_aws.apigatewayv2 import Api, ApiMapping, DomainName, Integration, Route, Stage
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.iam import Role, RolePolicy, RolePolicyAttachment
from pulumi_aws.lambda_ import Function, Permission
from pulumi_aws.route53 import Record
from pulumi_docker import Image

from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_api(
    config: Config,
    core_stack: StackReference,
    s3_bucket_arn: Output[str],
    vpc: Vpc,
    postgres_security_group: SecurityGroup,
    postgres_connection_secret: Secret,
    memory_size: int = 512,
    timeout_seconds: int = 30,
):
    # Get zone and certificate info from core stack
    zone_id = core_stack.require_output("zone-id")
    zone_name = core_stack.require_output("zone-name")
    certificate_arn = core_stack.require_output("certificate-arn")

    lambda_security_group = SecurityGroup("lambda-security-group", vpc_id=vpc.id)

    # Allow connections to required services
    lambda_security_group.allow_egress_reciprocal(to_security_group=postgres_security_group, ports=[5432])

    vpc.allow_endpoint_access(
        security_group=lambda_security_group, endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"]
    )

    # Allow egress to VPC CIDR for DNS resolution
    lambda_security_group.allow_egress_cidr(cidr_name="vpc-cidr", cidr=vpc.cidr_block, ports=[53])
    lambda_security_group.allow_egress_cidr(cidr_name="vpc-cidr", cidr=vpc.cidr_block, ports=[53], protocol="udp")

    # LogGroup("api-lambda-log-group", name="/aws/lambda/api-lambda", retention_in_days=7)

    repo = Repository("lambda-repo", force_delete=config.require_bool("devMode"))

    # Create a basic Lambda execution role (logs only).
    role = Role(
        "api-lambda-role",
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow"}
            ],
        }),
    )

    RolePolicyAttachment(
        "lambda-vpc-access",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    )

    RolePolicyAttachment(
        "lambda-basic-exec",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    RolePolicy(
        "lambdaS3Access",
        role=role.id,
        policy=Output.all(
            s3_bucket_arn=s3_bucket_arn, postgres_connection_secret_arn=postgres_connection_secret.base_arn
        ).apply(
            lambda args: json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:PutObject"],
                        "Resource": f"{args['s3_bucket_arn']}/*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["secretsmanager:GetSecretValue"],
                        "Resource": f"{args['postgres_connection_secret_arn']}",
                    },
                ],
            })
        ),
    )

    # Validate build context early; helps surface mis-path errors during preview.
    dockerfile = Path(config.require("lambdaDockerfile")).resolve()
    if not dockerfile.is_file():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")

    # 2) Credentials for pushing to ECR (no registry_id arg; avoids Output→str type mismatch)
    creds = get_authorization_token()

    # 3) Build fully-qualified image name as an Output[str]
    #    repo.repository_url is Output[str]; concat returns Output[str]
    image_name = Output.concat(repo.repository_url, ":", "latest")

    # 4) Build & push the image (dict style inputs: see Pulumi docs Python examples)
    image = Image(
        "apiImage",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=image_name,
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    # 5) Lambda from image
    fn = Function(
        name="api-lambda",
        resource_name="api-lambda",
        package_type="Image",
        image_uri=image.repo_digest,
        role=role.arn,
        timeout=timeout_seconds,
        memory_size=memory_size,
        environment={
            "variables": {"S3_BUCKET_ARN": s3_bucket_arn, "POSTGRES_DSN_ARN": postgres_connection_secret.versioned_arn}
        },
        vpc_config={"subnet_ids": vpc.private_subnet_ids, "security_group_ids": [lambda_security_group.id]},
    )

    api = Api(resource_name="httpApi", protocol_type="HTTP")

    integration = Integration(
        resource_name="lambdaProxyIntegration",
        api_id=api.id,
        integration_type="AWS_PROXY",
        integration_uri=fn.invoke_arn,
        payload_format_version="2.0",
    )

    Route(
        resource_name="catchAllRoute",
        api_id=api.id,
        route_key="$default",
        target=integration.id.apply(lambda iid: f"integrations/{iid}"),
    )

    log_group = LogGroup("httpApiLogs", retention_in_days=7)

    stage = Stage(
        resource_name="defaultStage",
        api_id=api.id,
        name="$default",
        auto_deploy=True,
        access_log_settings={
            "destination_arn": log_group.arn,
            "format": json.dumps({
                "requestId": "$context.requestId",
                "routeKey": "$context.routeKey",
                "status": "$context.status",
                "errorMessage": "$context.error.message",
                "integrationError": "$context.integrationErrorMessage",
                "integrationStatus": "$context.integrationStatus",
                "path": "$context.path",
                "latency": "$context.integrationLatency",
            }),
        },
    )

    domain_name = zone_name.apply(lambda zone_name: f"api.{zone_name}")

    domain = DomainName(
        "api-domain",
        domain_name=domain_name,
        domain_name_configuration={
            "certificate_arn": certificate_arn,
            "endpoint_type": "REGIONAL",
            "security_policy": "TLS_1_2",
        },
    )

    ApiMapping(resource_name="api-mapping", api_id=api.id, domain_name=domain.domain_name, stage=stage.name)

    Record(
        "api-domain-record",
        name=domain_name,
        type="A",
        zone_id=zone_id,
        aliases=[
            {
                "name": domain.domain_name_configuration.target_domain_name,
                "zone_id": domain.domain_name_configuration.hosted_zone_id,
                "evaluate_target_health": False,
            }
        ],
    )

    # ← NEW: allow API Gateway to invoke the Lambda
    Permission(
        resource_name="apiGatewayPermission",
        action="lambda:InvokeFunction",
        function=fn.name,
        principal="apigateway.amazonaws.com",
        source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
    )

    export("api-url", domain.domain_name.apply(lambda domain_name: f"https://{domain_name}"))
