from __future__ import annotations

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_aws import get_region_output
from pulumi_aws.batch import JobDefinition
from pulumi_aws.cloudwatch import LogGroup

from components.repository import Repository
from components.roles import ecs_execution_role, ecs_role


class BatchJobDefinition(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        image_repo: Repository,
        *,
        require_gpu: bool = False,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:BatchJobDefinition", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        self.log_group = LogGroup(f"{resource_name}-log-group", retention_in_days=7, opts=self._child_opts)

        self.execution_role = ecs_execution_role(f"{resource_name}-execution-role", opts=self._child_opts)
        self.job_role = ecs_role(f"{resource_name}-job-role", opts=self._child_opts)

        resource_requirements = [{"type": "VCPU", "value": "1"}, {"type": "MEMORY", "value": "1024"}]
        if require_gpu:
            resource_requirements.append({"type": "GPU", "value": "1"})

        self.job_definition = JobDefinition(
            f"{resource_name}-job-definition",
            type="container",
            container_properties=Output.json_dumps({
                "image": image_repo.locked_digest(),
                "executionRoleArn": self.execution_role.arn,
                "jobRoleArn": self.job_role.arn,
                "resourceRequirements": resource_requirements,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": self.log_group.name,
                        "awslogs-region": get_region_output().region,
                        "awslogs-stream-prefix": "ecs",
                    },
                },
            }),
            opts=self._child_opts,
        )

        self.arn = self.job_definition.arn
        self.arn_prefix = self.job_definition.arn_prefix

        self.register_outputs({
            "arn": self.arn,
            "arn_prefix": self.arn_prefix,
            "execution_role_arn": self.execution_role.arn,
            "job_role_arn": self.job_role.arn,
        })
