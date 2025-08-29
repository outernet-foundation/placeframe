from pulumi import ComponentResource, ResourceOptions
from pulumi_aws.batch import ComputeEnvironment, JobQueue
from pulumi_aws.iam import InstanceProfile

from components.roles import ec2_role
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
            vpc_endpoints=[
                "ecr.api",
                "ecr.dkr",
                "secretsmanager",
                "logs",
                "sts",
                "s3",
                "ec2",
                "ecs",
                "ecs-agent",
                "ecs-telemetry",
                "batch",
                # "ssm",
                # "ssmmessages",
                # "ec2messages",
            ],
            rules=[{"cidr_name": "imds", "to_cidr": "169.254.169.254/32", "ports": [80, 443], "protocols": ["tcp"]}],
            opts=self._child_opts,
        )

        self.instance_role = ec2_role(f"{resource_name}-instance-role", opts=self._child_opts)
        self.instance_profile = InstanceProfile(
            f"{resource_name}-instance-profile", role=self.instance_role.name, opts=self._child_opts
        )

        self.cpu_compute_environment = ComputeEnvironment(
            f"{resource_name}-cpu-compute-environment",
            type="MANAGED",
            compute_resources={
                "type": "EC2",
                "min_vcpus": 0,
                "max_vcpus": 32,
                "instance_types": ["c7i-flex.large"],
                "instance_role": self.instance_profile.arn,
                "subnets": vpc.private_subnet_ids,
                "security_group_ids": [self.security_group.id],
                "ec2_configurations": [{"image_type": "ECS_AL2"}],
            },
            state="ENABLED",
            opts=self._child_opts,
        )

        self.gpu_compute_environment = ComputeEnvironment(
            f"{resource_name}-gpu-compute-environment",
            type="MANAGED",
            compute_resources={
                "type": "EC2",
                "min_vcpus": 0,
                "max_vcpus": 32,
                "instance_types": ["g5.xlarge"],
                "instance_role": self.instance_profile.arn,
                "subnets": vpc.private_subnet_ids,
                "security_group_ids": [self.security_group.id],
                "ec2_configurations": [{"image_type": "ECS_AL2_NVIDIA"}],
            },
            state="ENABLED",
            opts=self._child_opts,
        )

        self.job_queue = JobQueue(
            f"{resource_name}-job-queue",
            state="ENABLED",
            priority=1,
            compute_environment_orders=[
                {"order": 1, "compute_environment": self.cpu_compute_environment.arn},
                {"order": 2, "compute_environment": self.gpu_compute_environment.arn},
            ],
            opts=self._child_opts,
        )

        self.job_queue_arn = self.job_queue.arn

        self.register_outputs({"job_queue_arn": self.job_queue_arn})
