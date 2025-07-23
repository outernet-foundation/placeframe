"""
Lambda component helpers.

Builds a container image (multi-stage Dockerfile in `image_context`) with
pulumi-docker, pushes it to ECR, and creates an IMAGE-type Lambda that runs your
FastAPI+Mangum app.

Python note: the pulumi-docker provider’s nested input objects (`DockerBuild`,
`Registry`, etc.) are *not* imported as symbols at the top level in Python; pass
them as dicts as shown below (this is the pattern used in Pulumi’s official
Python examples).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import pulumi
import pulumi_aws as aws
import pulumi_docker as docker  # top-level module (we'll pass dicts for inputs)
from pulumi import Config, Input, Output

# ---------------------------------------------------------------------------
# Container-image FastAPI Lambda
# ---------------------------------------------------------------------------


def create_lambda(
    config: Config,
    environment_vars: dict[str, Input[str]],
    s3_bucket_arn: Input[str],
    vpc_subnet_ids: Input[Sequence[Input[str]]],
    vpc_security_group_ids: Input[Sequence[Input[str]]],
    image_tag: str = "latest",
    memory_size: int = 512,
    timeout_seconds: int = 30,
    resource_name: str = "apiLambdaFunction",
) -> aws.lambda_.Function:
    """
    Build & deploy the FastAPI+Mangum Lambda from a Docker image.
    """
    repo = aws.ecr.Repository("ecr-repo", force_delete=config.require_bool("devMode"))


    # Create a basic Lambda execution role (logs only).
    role = aws.iam.Role(
        resource_name=resource_name,
        assume_role_policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )

    aws.iam.RolePolicyAttachment(
        "lambdaVpcAccessPolicy",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    )

    aws.iam.RolePolicy(
        "lambdaS3Access",
        role=role.id,
        policy=Output.all(s3_bucket_arn).apply(
            lambda arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject", "s3:PutObject"],
                            "Resource": f"{arn}/*",
                        }
                    ],
                }
            )
        ),
    )

    aws.iam.RolePolicyAttachment(
        resource_name=f"{resource_name}-basicExecution",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    # Validate build context early; helps surface mis-path errors during preview.
    dockerfile = Path(config.require("lambdaDockerfile")).resolve()
    if not dockerfile.is_file():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")

    # 2) Credentials for pushing to ECR (no registry_id arg; avoids Output→str type mismatch)
    creds = aws.ecr.get_authorization_token()

    # 3) Build fully-qualified image name as an Output[str]
    #    repo.repository_url is Output[str]; concat returns Output[str]
    image_name = Output.concat(repo.repository_url, ":", image_tag)

    # 4) Build & push the image (dict style inputs: see Pulumi docs Python examples)
    image = docker.Image(
        "apiImage",
        build={
            "dockerfile": str(dockerfile),
            "context": str(dockerfile.parent),
            "platform": "linux/amd64",
        },
        image_name=image_name,
        registry={
            "server": creds.proxy_endpoint,
            "username": creds.user_name,
            "password": creds.password,
        },
    )

    # 5) Lambda from image
    fn = aws.lambda_.Function(
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
        vpc_config={
            "subnet_ids": vpc_subnet_ids,
            "security_group_ids": vpc_security_group_ids,
        },
    )

    # Convenience export (optional)
    pulumi.export("apiImageUri", image.image_name)

    return fn
