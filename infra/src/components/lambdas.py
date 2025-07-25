from __future__ import annotations

import json
from pathlib import Path

import pulumi_docker as docker
from pulumi import Config, Input, Output, export
from pulumi_aws.ec2 import SecurityGroup, VpcEndpoint
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.iam import Role, RolePolicy, RolePolicyAttachment
from pulumi_aws.lambda_ import Function
from pulumi_aws.vpc import SecurityGroupEgressRule
from pulumi_awsx.ec2 import Vpc

from util import add_egress_to_dns_rule, add_reciprocal_security_group_rules


def create_lambda(
    config: Config,
    environment_vars: dict[str, Input[str]],
    s3_bucket_arn: Input[str],
    vpc: Vpc,
    lambda_security_group: SecurityGroup,
    postgres_security_group: SecurityGroup,
    logs_security_group: SecurityGroup,
    sts_security_group: SecurityGroup,
    s3_endpoint: VpcEndpoint,
    memory_size: int = 512,
    timeout_seconds: int = 30,
    resource_name: str = "apiLambdaFunction",
) -> Function:
    # Allow Postgres ingress from the Lambda and allow Lambda egress to Postgres
    add_reciprocal_security_group_rules(
        to_resource_name="postgres",
        from_resource_name="lambda",
        from_security_group=lambda_security_group,
        to_security_group=postgres_security_group,
        ports=[5432],
    )

    # Allow logs ingress from the Lambda and allow Lambda egress to CloudWatch Logs
    add_reciprocal_security_group_rules(
        from_resource_name="lambda",
        to_resource_name="cloudwatch-logs",
        from_security_group=lambda_security_group,
        to_security_group=logs_security_group,
        ports=[443],
    )

    # Allow STS ingress from the Lambda and allow Lambda egress to STS
    add_reciprocal_security_group_rules(
        from_resource_name="lambda",
        to_resource_name="sts",
        from_security_group=lambda_security_group,
        to_security_group=sts_security_group,
        ports=[443],
    )

    # Allow Lambda egress to S3 (via VPC endpoint)
    SecurityGroupEgressRule(
        "lambda-egress-to-s3",
        security_group_id=lambda_security_group.id,
        ip_protocol="tcp",
        from_port=443,
        to_port=443,
        prefix_list_id=s3_endpoint.prefix_list_id,
    )

    # Allow Lambda egress VPC Resolve for DNS queries
    add_egress_to_dns_rule("lambda", lambda_security_group, vpc)

    repo = Repository("lambda-repo", force_delete=config.require_bool("devMode"))

    # Create a basic Lambda execution role (logs only).
    role = Role(
        resource_name=resource_name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }),
    )

    RolePolicyAttachment(
        "lambdaVpcAccessPolicy",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    )

    RolePolicy(
        "lambdaS3Access",
        role=role.id,
        policy=Output.all(s3_bucket_arn).apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": f"{arn}/*"}],
            })
        ),
    )

    RolePolicyAttachment(
        resource_name=f"{resource_name}-basicExecution",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
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
    image = docker.Image(
        "apiImage",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=image_name,
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    # 5) Lambda from image
    fn = Function(
        resource_name=resource_name,
        package_type="Image",
        image_uri=image.repo_digest,  # Output[str]
        role=role.arn,
        timeout=timeout_seconds,
        memory_size=memory_size,
        environment={
            "variables": {
                **environment_vars,
                "S3_BUCKET_ARN": s3_bucket_arn,  # Pass S3 bucket ARN to Lambda
            }
        },
        vpc_config={"subnet_ids": vpc.private_subnet_ids, "security_group_ids": [lambda_security_group.id]},
    )

    # Convenience export (optional)
    export("apiImageUri", image.image_name)

    return fn
