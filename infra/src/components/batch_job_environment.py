from pulumi import ComponentResource, ResourceOptions
from pulumi_aws.batch import ComputeEnvironment, JobQueue

from components.assume_role_policies import ecs_assume_role_policy
from components.role import Role
from components.security_group import SecurityGroup
from components.vpc import Vpc


class BatchJobEnvironment(ComponentResource):
    def __init__(self, resource_name: str, vpc: Vpc, *, opts: ResourceOptions | None = None):
        super().__init__("custom:BatchJobEnvironment", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        self.security_group = SecurityGroup(
            f"{resource_name}-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            opts=self._child_opts,
        )

        self.compute_environment = ComputeEnvironment(
            f"{resource_name}-compute-environment",
            type="MANAGED",
            compute_resources={
                "type": "EC2",
                "min_vcpus": 0,
                "max_vcpus": 32,
                "instance_types": ["g5.xlarge"],
                "subnets": vpc.private_subnet_ids,
                "security_group_ids": [self.security_group.id],
            },
            state="ENABLED",
            opts=self._child_opts,
        )

        self.job_queue = JobQueue(
            f"{resource_name}-job-queue",
            state="ENABLED",
            priority=1,
            compute_environment_orders=[{"order": 1, "compute_environment": self.compute_environment.arn}],
            opts=self._child_opts,
        )

        self.execution_role = Role(
            f"{resource_name}-execution-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts
        )
        self.execution_role.attach_ecs_task_execution_role_policy()

        self.queue_arn = self.job_queue.arn

        self.register_outputs({"queue_arn": self.queue_arn})
