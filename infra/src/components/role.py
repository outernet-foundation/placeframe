from __future__ import annotations

import json
from typing import TYPE_CHECKING, Iterable, List, NamedTuple, overload

from pulumi import ComponentResource, Input, Output, ResourceOptions
from pulumi_aws import iam
from pulumi_aws.ecs import Service
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

    def attach_ec2_instance_role_policy(self):
        RolePolicy(
            f"{self._resource_name}-ec2-instance-role",
            role=self.name,
            policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ecs:DiscoverPollEndpoint",
                            "ecs:Poll",
                            "ecs:RegisterContainerInstance",
                            "ecs:DeregisterContainerInstance",
                            "ecs:Submit*",
                            "ecs:StartTelemetrySession",
                            "ecs:UpdateContainerInstancesState",
                            "ecs:Describe*",
                            "ecs:List*",
                        ],
                        "Resource": "*",
                    },
                    {"Effect": "Allow", "Action": ["ec2:Describe*"], "Resource": "*"},
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "logs:DescribeLogStreams",
                            "logs:DescribeLogGroups",
                        ],
                        "Resource": "*",
                    },
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
                            "batch:Describe*",
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

    def attach_lambda_basic_execution_role_policy(self):
        RolePolicy(
            f"{self._resource_name}-lambda-basic-execution-role",
            role=self.name,
            policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                        "Resource": "*",
                    }
                ],
            }),
            opts=self._child_opts,
        )

    def attach_lambda_vpc_access_execution_role_policy(self):
        RolePolicy(
            f"{self._resource_name}-lambda-vpc-access-execution-role",
            role=self.name,
            policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ec2:CreateNetworkInterface",
                            "ec2:DescribeNetworkInterfaces",
                            "ec2:DeleteNetworkInterface",
                            "ec2:AssignPrivateIpAddresses",
                            "ec2:UnassignPrivateIpAddresses",
                        ],
                        "Resource": "*",
                    }
                ],
            }),
            opts=self._child_opts,
        )

    def allow_service_deployment(
        self, deployment_name: str, passroles: Iterable[Role], services: Iterable[Service | Output[Service]]
    ):
        self.attach_policy(
            f"allow-ecs-service-deploy-{deployment_name}",
            Output.json_dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {"Effect": "Allow", "Action": ["iam:PassRole"], "Resource": [role.arn for role in passroles]},
                    {
                        "Effect": "Allow",
                        "Action": ["ecs:UpdateService"],
                        "Resource": [service.arn for service in services],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["ecs:RegisterTaskDefinition", "ecs:DeregisterTaskDefinition"],
                        "Resource": "*",
                    },
                ],
            }),
        )

    def allow_batch_job_definition_update(
        self,
        deployment_name: str,
        passroles: Iterable[Role],
        job_definitions: Iterable[BatchJobDefinition | Output[BatchJobDefinition]],
    ):
        self.attach_policy(
            f"allow-batch-job-definition-update-{deployment_name}",
            Output.json_dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {"Effect": "Allow", "Action": ["iam:PassRole"], "Resource": [role.arn for role in passroles]},
                    {
                        "Effect": "Allow",
                        "Action": ["batch:RegisterJobDefinition"],
                        "Resource": [job_definition.arn_prefix for job_definition in job_definitions],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["batch:DeregisterJobDefinition"],
                        "Resource": [
                            Output.concat(job_definition.arn_prefix, ":*") for job_definition in job_definitions
                        ],
                    },
                ],
            }),
        )

    def allow_image_repo_actions(self, deployment_name: str, repos: Iterable[Repository]):
        self.attach_policy(
            f"allow-image-repo-actions-{deployment_name}",
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

    def allow_secret_get(self, policy_suffix: str, secrets: Iterable[Secret]):
        self.attach_policy(
            f"allow-secret-get-{policy_suffix}",
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
                        "Resource": Output.concat(s3_bucket.arn, "/*"),
                    }
                ],
            }),
        )

    def allow_batch_job_submission(
        self, job_environment: BatchJobEnvironment, job_definitions: List[BatchJobDefinition]
    ) -> None:
        policy_json = Output.json_dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["batch:SubmitJob"],
                    "Resource": [job_environment.job_queue_arn]
                    + [job_definition.arn_prefix for job_definition in job_definitions],
                },
                {"Effect": "Allow", "Action": ["batch:DescribeJobs"], "Resource": "*"},
                {
                    "Effect": "Allow",
                    "Action": ["iam:PassRole"],
                    "Resource": (
                        [job_definition.execution_role.arn for job_definition in job_definitions]
                        + [job_definition.job_role.arn for job_definition in job_definitions]
                    ),
                },
            ],
        })
        self.attach_policy(f"{self._resource_name}-allow-batch-job-submission", policy_json)
