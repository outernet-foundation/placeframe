import json

from pulumi import Config, ResourceOptions
from pulumi_aws.iam import OpenIdConnectProvider, Role, RolePolicy
from pulumi_github import ActionsSecret, Provider

from components.secret import Secret


def create_oidc(config: Config, database_connection_secret: Secret) -> None:
    github_oidc = OpenIdConnectProvider(
        "githubOidcProvider",
        url="https://token.actions.githubusercontent.com",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],
    )

    github_oidc_role = Role(
        "githubActionsRole",
        assume_role_policy=github_oidc.arn.apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Federated": arn},
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringLike": {
                                "token.actions.githubusercontent.com:sub": f"repo:{config.require('github-repo')}:ref:refs/heads/{config.require('github-branch')}"
                            },
                            "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
                        },
                    }
                ],
            })
        ),
    )

    RolePolicy(
        "ci-db-secret-policy",
        role=github_oidc_role.id,
        policy=database_connection_secret.arn.apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": arn}],
            })
        ),
    )

    github_provider = Provider(
        "github-provider",
        app_auth={
            "id": config.require("github-app-id"),
            "installation_id": config.require("github-app-installation-id"),
            "pem_file": config.require_secret("github-app-private-key"),
        },
        owner=config.require("github-org"),
    )

    ActionsSecret(
        "github-actions-role-arn",
        secret_name="OIDC_ROLE_ARN",
        repository=config.require("github-repo"),
        plaintext_value=github_oidc_role.arn,
        opts=ResourceOptions(provider=github_provider),
    )
