import json
from typing import Iterable

from pulumi import Config, Input, Output
from pulumi_aws.ecr import Repository
from pulumi_aws.iam import Policy, Role, RolePolicyAttachment
from pulumi_aws.s3 import Bucket

from components.secret import Secret


def create_github_actions_role(name: str, config: Config, github_oidc_provider_arn: Output[str], environment: str):
    repo = f"{config.require('github-org')}/{config.require('github-repo')}"
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
                                "token.actions.githubusercontent.com:sub": [
                                    f"repo:{repo}:ref:{config.require('github-branch')}",
                                    f"repo:{repo}:environment:{environment}",
                                ]
                            },
                            "StringEquals": {
                                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                "token.actions.githubusercontent.com:repository": repo,
                                "token.actions.githubusercontent.com:environment": environment,
                            },
                        },
                    }
                ],
            })
        ),
    )


def create_ecs_role(name: str):
    return Role(
        name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }),
    )


def attach_policy(policy_name: str, role_name: Input[str], policy_json: Input[str]):
    policy = Policy(f"{role_name}-{policy_name}", policy=policy_json)

    # TODO fix bad string interpolation
    RolePolicyAttachment(f"{role_name}-{policy_name}-attachment", role=role_name, policy_arn=policy.arn)


def allow_service_deployment(
    role_name: Input[str], ecs_service_arns: Iterable[str | Output[str]], passrole_arns: Iterable[str | Output[str]]
):
    attach_policy(
        "allow-ecs-service-deploy",
        role_name,
        Output.all(service_arns=Output.all(*ecs_service_arns), passrole_arns=Output.all(*passrole_arns)).apply(
            lambda arns: json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ecs:RegisterTaskDefinition",
                            "ecs:DeregisterTaskDefinition",
                            "ecs:Describe*",
                            "ecs:List*",
                        ],
                        "Resource": "*",
                    },
                    {"Effect": "Allow", "Action": ["ecs:UpdateService"], "Resource": arns["service_arns"]},
                    {"Effect": "Allow", "Action": ["iam:PassRole"], "Resource": arns["passrole_arns"]},
                ],
            })
        ),
    )


def allow_image_repo_actions(role_name: Input[str], repos: Iterable[Repository]):
    attach_policy(
        "allow-image-repo-actions",
        role_name,
        Output.all(*[repo.arn for repo in repos]).apply(
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
                            "ecr:DescribeImages",
                            "ecr:PutImageTagMutability",
                        ],
                        "Resource": arns,
                    },
                ],
            })
        ),
    )


def allow_repo_pullthrough(role_name: Input[str], repos: Iterable[Repository]):
    attach_policy(
        "allow-repo-pullthrough",
        role_name,
        Output.all(*[repo.arn for repo in repos]).apply(
            lambda arns: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["ecr:BatchImportUpstreamImage"], "Resource": arns}],
            })
        ),
    )


def allow_secret_get(role_name: Input[str], secrets: Iterable[Secret]):
    attach_policy(
        "allow-secret-get",
        role_name,
        Output.all(*[secret.arn for secret in secrets]).apply(
            lambda arns: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": arns}],
            })
        ),
    )


def allow_s3(role_name: Input[str], s3_bucket: Bucket):
    attach_policy(
        "allow-s3",
        role_name,
        s3_bucket.arn.apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": f"{arn}/*"}],
            })
        ),
    )
