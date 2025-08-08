import json
from typing import Dict, List

from pulumi import Config, Output
from pulumi_aws.ecr import Repository
from pulumi_aws.iam import Role
from pulumi_aws.s3 import Bucket

from components.secret import Secret


def create_github_actions_role(
    name: str, config: Config, github_oidc_provider_arn: Output[str], policies: Dict[str, Output[str]]
):
    return Role(
        name,
        assume_role_policy=github_oidc_provider_arn.apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Federated": arn},
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringLike": {
                                "token.actions.githubusercontent.com:sub": (
                                    f"repo:{config.require('github-org')}/{config.require('github-repo')}:ref:refs/heads/main"
                                )
                            },
                            "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
                        },
                    }
                ],
            })
        ),
        inline_policies=[{"name": policy[0], "policy": policy[1]} for policy in policies.items()],
    )


def allow_repo_push(repos: List[Repository]):
    return Output.all(*[repo.arn for repo in repos]).apply(
        lambda arns: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["ecr:GetAuthorizationToken"], "Resource": "*"},
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                        "ecr:PutImage",
                    ],
                    "Resource": arns,
                },
            ],
        })
    )


def allow_repo_pullthrough(repos: List[Repository]):
    return Output.all(*[repo.arn for repo in repos]).apply(
        lambda arns: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": ["ecr:BatchImportUpstreamImage"], "Resource": arns}],
        })
    )


def allow_secret_get(secrets: List[Secret]):
    return Output.all(*[secret.arn for secret in secrets]).apply(
        lambda arns: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": arns}],
        })
    )


def allow_s3(s3_bucket: Bucket):
    return s3_bucket.arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": f"{arn}/*"}],
        })
    )
