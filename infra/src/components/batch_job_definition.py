from __future__ import annotations

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_aws.batch import JobDefinition
from pulumi_aws.cloudwatch import LogGroup

from components.assume_role_policies import ecs_assume_role_policy
from components.log import log_configuration
from components.repository import Repository
from components.role import Role


class BatchJobDefinition(ComponentResource):
    def __init__(self, resource_name: str, image_repo: Repository, *, opts: ResourceOptions | None = None):
        super().__init__("custom:BatchJob", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        self.log_group = LogGroup(f"{resource_name}-log-group", retention_in_days=7, opts=self._child_opts)

        self.execution_role = Role(
            f"{resource_name}-execution-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts
        )
        self.execution_role.attach_ecs_task_execution_role_policy()

        self.job_role = Role(
            f"{resource_name}-job-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts
        )

        self.job_definition = JobDefinition(
            f"{resource_name}-job-definition",
            type="container",
            container_properties=Output.secret(
                Output.json_dumps({
                    "image": image_repo.locked_digest(),
                    "executionRoleArn": self.execution_role.arn,
                    "jobRoleArn": self.job_role.arn,
                    "resourceRequirements": [
                        {"type": "VCPU", "value": "1"},
                        {"type": "GPU", "value": "1"},
                        {"type": "MEMORY", "value": "1024"},
                    ],
                    "logConfiguration": log_configuration(self.log_group),
                })
            ),
            opts=self._child_opts,
        )

        self.arn = self.job_definition.arn

        self.register_outputs({
            "arn": self.arn,
            "execution_role_arn": self.execution_role.arn,
            "job_role_arn": self.job_role.arn,
        })
