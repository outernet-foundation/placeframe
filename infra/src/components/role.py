import json
from typing import Iterable, overload

from pulumi import ComponentResource, Config, Input, Output, ResourceOptions
from pulumi_aws import iam
from pulumi_aws.iam import Policy, RolePolicyAttachment, get_role_output
from pulumi_aws.s3 import Bucket

from components.repository import Repository
from components.secret import Secret


def github_actions_assume_role_policy(config: Config, github_oidc_provider_arn: Output[str], environment: str):
    repo = f"{config.require('github-org')}/{config.require('github-repo')}"
    return github_oidc_provider_arn.apply(
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
    )


def ecs_assume_role_policy():
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    })


class Role(ComponentResource):
    @overload
    def __init__(
        self, resource_name: str, *, assume_role_policy: Input[str] | None = None, opts: ResourceOptions | None = None
    ) -> None: ...

    @overload
    def __init__(
        self, resource_name: str, *, name: Input[str] | None = None, opts: ResourceOptions | None = None
    ) -> None: ...

    def __init__(
        self,
        resource_name: str,
        *,
        assume_role_policy: Input[str] | None = None,
        name: Input[str] | None = None,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__("custom:Role", resource_name, opts=opts)

        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))
        self._resource_name = resource_name

        if assume_role_policy:
            self._role = iam.Role(resource_name, assume_role_policy=assume_role_policy, opts=self._child_opts)
        else:
            self._role = get_role_output(name=name)

        self.arn = self._role.arn
        self.name = self._role.name

        self.register_outputs({"name": self._resource_name, "arn": self.arn})

    def attach_policy(self, policy_name: str, policy_json: Input[str]):
        policy = Policy(f"{self._resource_name}-{policy_name}", policy=policy_json, opts=self._child_opts)
        RolePolicyAttachment(
            f"{self._resource_name}-{policy_name}-attachment",
            role=self._role.name,
            policy_arn=policy.arn,
            opts=self._child_opts,
        )

    def allow_service_deployment(
        self, service_name: str, ecs_service_arns: Iterable[str | Output[str]], passrole_arns: Iterable[str | Output[str]]
    ):
        self.attach_policy(
            f"allow-ecs-service-deploy-{service_name}",
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

    def allow_image_repo_actions(self, repos: Iterable[Repository]):
        self.attach_policy(
            f"allow-image-repo-actions-{"-".join(repo.resource_name for repo in repos)}",
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

    def allow_repo_pullthrough(self, repos: Iterable[Repository]):
        self.attach_policy(
            f"allow-repo-pullthrough-{"-".join(repo.resource_name for repo in repos)}",
            Output.all(*[repo.arn for repo in repos]).apply(
                lambda arns: json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{"Effect": "Allow", "Action": ["ecr:BatchImportUpstreamImage"], "Resource": arns}],
                })
            ),
        )

    def allow_secret_get(self, secrets: Iterable[Secret]):
        self.attach_policy(
            f"allow-secret-get-{"-".join(secret._name for secret in secrets)}",
            Output.all(*[secret.arn for secret in secrets]).apply(
                lambda arns: json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": arns}],
                })
            ),
        )

    def allow_s3(self, s3_bucket: Bucket):
        self.attach_policy(
            f"allow-s3-{s3_bucket._name}",
            s3_bucket.arn.apply(
                lambda arn: json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": f"{arn}/*"}
                    ],
                })
            ),
        )
