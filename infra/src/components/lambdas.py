from __future__ import annotations

import json
from pathlib import Path

import pulumi_docker as docker
from pulumi import Config, Input, Output, export
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.iam import Role, RolePolicy, RolePolicyAttachment
from pulumi_aws.lambda_ import Function

from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_lambda(
    config: Config,
    environment_vars: dict[str, Input[str]],
    s3_bucket_arn: Output[str],
    vpc: Vpc,
    lambda_security_group: SecurityGroup,
    postgres_security_group: SecurityGroup,
    memory_size: int = 512,
    timeout_seconds: int = 30,
    resource_name: str = "apiLambdaFunction",
) -> Function:
    # Allow connections to required services
    postgres_security_group.allow_ingress(from_security_group=lambda_security_group, ports=[5432])

    # For each VPC endpoint, allow Lambda to access it
    for service_name in ["ecr.api", "ecr.dkr", "logs", "sts"]:
        vpc.interface_security_groups[service_name].allow_ingress(
            from_security_group=lambda_security_group, ports=[443]
        )

    # Allow Lambda egress to S3 bucket
    lambda_security_group.allow_egress_prefix_list(
        prefix_list_name="s3", prefix_list_id=vpc.s3_endpoint_prefix_list_id, ports=[443]
    )

    # Allow egress to VPC CIDR for DNS resolution
    lambda_security_group.allow_egress_cidr(cidr_name="vpc-cidr", cidr=vpc.cidr_block, ports=[53])
    lambda_security_group.allow_egress_cidr(cidr_name="vpc-cidr", cidr=vpc.cidr_block, ports=[53], protocol="udp")

    repo = Repository("lambda-repo", force_delete=config.require_bool("devMode"))

    # Create a basic Lambda execution role (logs only).
    role = Role(
        f"{resource_name}-lambda-role",
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow"}
            ],
        }),
    )

    RolePolicyAttachment(
        "lambda-basic-exec",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    )

    RolePolicyAttachment(
        "lambda-vpc-access",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    RolePolicy(
        "lambdaS3Access",
        role=role.id,
        policy=s3_bucket_arn.apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": f"{arn}/*"}],
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
