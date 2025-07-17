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

import pulumi
import pulumi_aws as aws
import pulumi_docker as docker  # top-level module (we'll pass dicts for inputs)

# ---------------------------------------------------------------------------
# IAM Role
# ---------------------------------------------------------------------------


def create_lambda_role(*, resource_name: str = "lambdaExecutionRole") -> aws.iam.Role:
    """Create a basic Lambda execution role (logs only)."""
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
        resource_name=f"{resource_name}-basicExecution",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    return role


# ---------------------------------------------------------------------------
# Container-image FastAPI Lambda
# ---------------------------------------------------------------------------


def create_api_lambda(
    *,
    lambda_role: aws.iam.Role,
    image_context: str = "../api",  # path to folder with Dockerfile
    image_tag: str = "latest",
    memory_size: int = 512,
    timeout_seconds: int = 30,
    resource_name: str = "apiLambdaFunction",
) -> aws.lambda_.Function:
    """
    Build & deploy the FastAPI+Mangum Lambda from a Docker image.
    """

    # Validate build context early; helps surface mis-path errors during preview.
    ctx_path = Path(image_context).resolve()
    if not ctx_path.is_dir():
        raise FileNotFoundError(f"Docker build context not found: {ctx_path}")

    # 1) ECR repository for the image
    repo = aws.ecr.Repository("apiEcrRepo")

    # 2) Credentials for pushing to ECR (no registry_id arg; avoids Output→str type mismatch)
    creds = aws.ecr.get_authorization_token()

    # 3) Build fully-qualified image name as an Output[str]
    #    repo.repository_url is Output[str]; concat returns Output[str]
    image_name = pulumi.Output.concat(repo.repository_url, ":", image_tag)

    # 4) Build & push the image (dict style inputs: see Pulumi docs Python examples)
    image = docker.Image(
        "apiImage",
        build={"context": str(ctx_path)},  # minimal; Dockerfile default is "Dockerfile"
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
        image_uri=image.image_name,  # Output[str]
        role=lambda_role.arn,
        timeout=timeout_seconds,
        memory_size=memory_size,
    )

    # Convenience export (optional)
    pulumi.export("apiImageUri", image.image_name)

    return fn
