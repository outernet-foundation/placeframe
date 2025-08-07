import json
from typing import List

from pulumi import Config, Output, ResourceOptions
from pulumi_aws.ecr import Repository
from pulumi_aws.iam import OpenIdConnectProvider, Role
from pulumi_github import ActionsSecret, Provider

from components.secret import Secret


def create_oidc(config: Config, database_connection_secret: Secret, image_repos: List[Repository]) -> None:
    github_org = config.require("github-org")
    github_repo = config.require("github-repo")

    github_oidc_provider = OpenIdConnectProvider(
        "github-oidc-provider",
        url="https://token.actions.githubusercontent.com",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],  # GitHub OIDC thumbprint
    )

    github_assume_role_policy = github_oidc_provider.arn.apply(
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
                                f"repo:{github_org}/{github_repo}:ref:refs/heads/{config.require('github-branch')}"
                            )
                        },
                        "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
                    },
                }
            ],
        })
    )

    github_actions_db_migrations_role = Role(
        "github-actions-db-migrations-role",
        assume_role_policy=github_assume_role_policy,
        inline_policies=[
            {
                "name": "db-secret-policy",
                "policy": database_connection_secret.arn.apply(
                    lambda arn: json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [
                            {"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": arn}
                        ],
                    })
                ),
            }
        ],
    )

    github_actions_docker_role = Role(
        "github-actions-docker-role",
        assume_role_policy=github_assume_role_policy,
        inline_policies=[
            {
                "name": "ecr-policy",
                "policy": json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:InitiateLayerUpload",
                                "ecr:UploadLayerPart",
                                "ecr:CompleteLayerUpload",
                                "ecr:PutImage",
                            ],
                            "Resource": Output.all(*[repo.arn for repo in image_repos]),
                        }
                    ],
                }),
            }
        ],
    )

    github_provider = Provider(
        "github-provider",
        app_auth={
            "id": config.require("github-app-id"),
            "installation_id": config.require("github-app-installation-id"),
            "pem_file": config.require_secret("github-app-private-key"),
        },
        owner=github_org,
    )

    ActionsSecret(
        "github-actions-db-migrations-role-arn",
        secret_name="DB_MIGRATIONS_ROLE_ARN",
        repository=github_repo,
        plaintext_value=github_actions_db_migrations_role.arn,
        opts=ResourceOptions(provider=github_provider),
    )

    ActionsSecret(
        "github-actions-docker-role-arn",
        secret_name="DOCKER_ROLE_ARN",
        repository=github_repo,
        plaintext_value=github_actions_docker_role.arn,
        opts=ResourceOptions(provider=github_provider),
    )
