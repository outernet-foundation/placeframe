from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import pulumi_aws as aws
from pulumi import AssetArchive, FileArchive


def create_lambda_role(*, resource_name: str = "lambdaExecutionRole") -> aws.iam.Role:
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
        resource_name="lambdaBasicExecutionAttachment",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    return role


def create_api_lambda(
    *,
    lambda_role: aws.iam.Role,
    code_path: Union[str, Path],
    handler: str = "main.handler",
    memory_size: int = 512,
    timeout_seconds: int = 30,
) -> aws.lambda_.Function:
    code_dir = Path(code_path).resolve()
    if not code_dir.is_dir():
        raise FileNotFoundError(f"Lambda code directory not found: {code_dir}")

    fn = aws.lambda_.Function(
        resource_name="apiLambdaFunction",
        role=lambda_role.arn,
        runtime="python3.12",
        handler=handler,
        code=AssetArchive({".": FileArchive(str(code_dir))}),
        timeout=timeout_seconds,
        memory_size=memory_size,
    )
    return fn
