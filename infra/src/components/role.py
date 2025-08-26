from __future__ import annotations

import json
from typing import TYPE_CHECKING, Iterable, List, NamedTuple, overload

from pulumi import ComponentResource, Input, Output, ResourceOptions
from pulumi_aws import iam
from pulumi_aws.iam import RolePolicy
from pulumi_aws.s3 import Bucket

if TYPE_CHECKING:
    from components.batch_job_definition import BatchJobDefinition
    from components.batch_job_environment import BatchJobEnvironment
from components.repository import Repository
from components.secret import Secret


class JobDefArns(NamedTuple):
    jobdef_arn: str
    exec_role_arn: str
    job_role_arn: str


class Role(ComponentResource):
    @overload
    def __init__(
        self, resource_name: str, *, assume_role_policy: Input[str] | None = None, opts: ResourceOptions | None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        resource_name: str,
        *,
        name: Input[str] | None = None,
        arn: Input[str] | None = None,
        opts: ResourceOptions | None = None,
    ) -> None: ...

    def __init__(
        self,
        resource_name: str,
        *,
        assume_role_policy: Input[str] | None = None,
        name: Input[str] | None = None,
        arn: Input[str] | None = None,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__("custom:Role", resource_name, opts=opts)

        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))
        self._resource_name = resource_name

        if assume_role_policy:
            self._role = iam.Role(resource_name, assume_role_policy=assume_role_policy, opts=self._child_opts)
            self.arn = self._role.arn
            self.name = self._role.name
        elif name and arn:
            self.arn = Output.from_input(arn)
            self.name = Output.from_input(name)
        else:
            raise ValueError("Either assume_role_policy or both name and arn must be provided")

        self.register_outputs({"name": self._resource_name, "arn": self.arn})

    # CAUTION: Do not use RolePolicyAttachment until this bug is fixed: https://github.com/pulumi/pulumi-aws/issues/4235
    # That bug is why we are manually writing inline policies that could be existing managed policies instead

    def attach_policy(self, policy_name: str, policy_json: Input[str]):
        RolePolicy(
            f"{self._resource_name}-{policy_name}-attachment", role=self.name, policy=policy_json, opts=self._child_opts
        )

    def attach_ecs_task_execution_role_policy(self):
        RolePolicy(
            f"{self._resource_name}-ecs-task-execution-role",
            role=self.name,
            policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ecr:GetAuthorizationToken",
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:GetDownloadUrlForLayer",
                            "ecr:BatchGetImage",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                        ],
                        "Resource": "*",
                    }
                ],
            }),
            opts=self._child_opts,
        )

    def attach_read_only_access_role_policy(self):
        RolePolicy(
            f"{self._resource_name}-read-only-access",
            role=self.name,
            policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "ReadOnlyCoreInfra",
                        "Effect": "Allow",
                        "Action": [
                            "ec2:Describe*",
                            "elasticloadbalancing:Describe*",
                            "ecs:Describe*",
                            "ecs:List*",
                            "ecr:DescribeRepositories",
                            "ecr:DescribeImages",
                            "ecr:GetRepositoryPolicy",
                            "ecr:ListImages",
                            "ecr:ListTagsForResource",
                            "cloudwatch:Describe*",
                            "cloudwatch:Get*",
                            "cloudwatch:List*",
                            "logs:DescribeLogGroups",
                            "logs:DescribeLogStreams",
                            "logs:GetLogEvents",
                            "logs:FilterLogEvents",
                        ],
                        "Resource": "*",
                    }
                ],
            }),
            opts=self._child_opts,
        )

    def allow_service_deployment(
        self,
        service_name: str,
        ecs_service_arns: Iterable[str | Output[str]],
        passrole_arns: Iterable[str | Output[str]],
    ):
        # No apply: feed Inputs directly, Pulumi will resolve them inside Output.json_dumps
        self.attach_policy(
            f"allow-ecs-service-deploy-{service_name}",
            Output.json_dumps({
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
                    {"Effect": "Allow", "Action": ["ecs:UpdateService"], "Resource": list(ecs_service_arns)},
                    {"Effect": "Allow", "Action": ["iam:PassRole"], "Resource": list(passrole_arns)},
                ],
            }),
        )

    def allow_image_repo_actions(self, repos: Iterable[Repository]):
        self.attach_policy(
            f"allow-image-repo-actions-{'-'.join(repo.resource_name for repo in repos)}",
            Output.json_dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {"Effect": "Allow", "Action": ["ecr:GetAuthorizationToken"], "Resource": "*"},
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ecr:BatchImportUpstreamImage",
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
                        "Resource": [repo.arn for repo in repos],
                    },
                ],
            }),
        )

    def allow_repo_pullthrough(self, repos: Iterable[Repository]):
        self.attach_policy(
            f"allow-repo-pullthrough-{'-'.join(repo.resource_name for repo in repos)}",
            Output.json_dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["ecr:BatchImportUpstreamImage"],
                        "Resource": [repo.arn for repo in repos],
                    }
                ],
            }),
        )

    def allow_secret_get(self, secrets: Iterable[Secret]):
        self.attach_policy(
            f"allow-secret-get-{'-'.join(secret._name for secret in secrets)}",
            Output.json_dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["secretsmanager:GetSecretValue"],
                        "Resource": [secret.arn for secret in secrets],
                    }
                ],
            }),
        )

    def allow_s3(self, s3_bucket: Bucket):
        self.attach_policy(
            f"allow-s3-{s3_bucket._name}",
            Output.json_dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:PutObject"],
                        # Use concat to avoid .apply; this yields "<bucket-arn>/*"
                        "Resource": Output.concat(s3_bucket.arn, "/*"),
                    }
                ],
            }),
        )

    def allow_batch_job_submission(
        self, job_environment: BatchJobEnvironment, job_definitions: List[BatchJobDefinition]
    ) -> None:
        # Output.json_dumps resolves queue ARN and all job/role ARNs without apply
        policy_json = Output.json_dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["batch:SubmitJob"],
                    "Resource": [job_environment.queue_arn] + [jd.arn for jd in job_definitions],
                },
                {"Effect": "Allow", "Action": ["batch:DescribeJobs"], "Resource": "*"},
                {
                    "Effect": "Allow",
                    "Action": ["iam:PassRole"],
                    "Resource": (
                        [jd.execution_role.arn for jd in job_definitions] + [jd.job_role.arn for jd in job_definitions]
                    ),
                },
            ],
        })
        self.attach_policy(f"{self._resource_name}-allow-batch-job-submission", policy_json)
