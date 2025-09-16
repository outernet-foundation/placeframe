from pulumi import ComponentResource, Config, Input, Output, ResourceOptions
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.route53 import Record
from pulumi_aws.s3 import Bucket
from pulumi_awsx.ecs import FargateService

from components.batch_job_definition import BatchJobDefinition
from components.batch_job_environment import BatchJobEnvironment
from components.database import Database
from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.repository import Repository
from components.role import Role
from components.roles import ecs_execution_role, ecs_role
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


class Api(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        database_manager_role: Role,
        database_manager_function_arn: Input[str],
        zone_id: Input[str],
        zone_name: Input[str],
        certificate_arn: Input[str],
        vpc: Vpc,
        cluster: Cluster,
        s3_bucket: Bucket,
        rds_security_group: SecurityGroup,
        rds_address: Input[str],
        prepare_deploy_role: Role,
        deploy_role: Role,
        *,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:Api", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Log groups
        api_log_group = LogGroup("api-log-group", name="/ecs/api", retention_in_days=7, opts=self._child_opts)

        # Database
        api_database_user = config.require("api-database-user")
        api_database_password_secret = Secret(
            "api-database-password", secret_string=config.require_secret("api-database-password"), opts=self._child_opts
        )
        database = Database(
            "api-database",
            database_manager_role=database_manager_role,
            database_manager_function_arn=database_manager_function_arn,
            name=api_database_user,
            password_secret=api_database_password_secret,
        )

        # Image repos
        api_image_repo = Repository("api-image-repo", "api", opts=self._child_opts)
        reconstruction_task_image_repo = Repository(
            "run-reconstruction-image-repo", "run-reconstruction", opts=self._child_opts
        )
        features_task_image_repo = Repository(
            "extract-match-features-image-repo", "extract-match-features", opts=self._child_opts
        )
        prepare_deploy_role.allow_image_repo_actions(
            "api", [api_image_repo, reconstruction_task_image_repo, features_task_image_repo]
        )

        # Load balancer
        load_balancer = LoadBalancer(
            "api-loadbalancer",
            "api",
            vpc=vpc,
            certificate_arn=certificate_arn,
            target_port=8000,
            ingress_cidr="0.0.0.0/0",
            health_check={
                "path": "/health",
                "protocol": "HTTP",
                "interval": 15,
                "healthy_threshold": 2,
                "unhealthy_threshold": 10,
            },
            opts=self._child_opts,
        )

        # Security groups
        api_security_group = SecurityGroup(
            "api-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3", "batch"],
            rules=[
                {"from_security_group": load_balancer.security_group, "ports": [8000]},
                {"to_security_group": rds_security_group, "ports": [5432]},
            ],
            opts=self._child_opts,
        )

        # DNS Records
        domain = Output.concat("api.", zone_name)
        Record(
            "api-domain-record",
            zone_id=zone_id,
            name=domain,
            type="A",
            aliases=[
                {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}
            ],
            opts=self._child_opts,
        )

        # Batch jobs
        batch_job_environment = BatchJobEnvironment("api-batch-job-environment", vpc=vpc, opts=self._child_opts)

        features_batch_job_definition = BatchJobDefinition(
            "extract-match-features", image_repo=features_task_image_repo, require_gpu=True, opts=self._child_opts
        )
        features_batch_job_definition.job_role.allow_s3(s3_bucket)

        reconstruction_batch_job_definition = BatchJobDefinition(
            "run-reconstruction", image_repo=reconstruction_task_image_repo, opts=self._child_opts
        )
        reconstruction_batch_job_definition.job_role.allow_s3(s3_bucket)
        reconstruction_batch_job_definition.job_role.allow_batch_job_submission(
            job_environment=batch_job_environment, job_definitions=[features_batch_job_definition]
        )

        # Execution role
        execution_role = ecs_execution_role("api-execution-role", opts=self._child_opts)
        execution_role.allow_secret_get("api-secrets", [api_database_password_secret])

        # Task role
        task_role = ecs_role("api-task-role", opts=self._child_opts)
        task_role.allow_s3(s3_bucket)
        task_role.allow_batch_job_submission(
            job_environment=batch_job_environment, job_definitions=[reconstruction_batch_job_definition]
        )

        # Service
        service = FargateService(
            "api-service",
            name="api-service",
            cluster=cluster.arn,
            desired_count=1,
            network_configuration={"subnets": vpc.private_subnet_ids, "security_groups": [api_security_group.id]},
            task_definition_args={
                "execution_role": {"role_arn": execution_role.arn},
                "task_role": {"role_arn": task_role.arn},
                "containers": {
                    "api": {
                        "name": "api",
                        "image": api_image_repo.locked_digest(),
                        "log_configuration": log_configuration(api_log_group),
                        "port_mappings": [
                            {"container_port": 8000, "host_port": 8000, "target_group": load_balancer.target_group}
                        ],
                        "secrets": [{"name": "API_DATABASE_PASSWORD", "value_from": api_database_password_secret.arn}],
                        "environment": [
                            {"name": "BACKEND", "value": "aws"},
                            {"name": "API_DATABASE_USER", "value": "api"},
                            {"name": "API_DATABASE_HOST", "value": rds_address},
                            {"name": "JOB_QUEUE_ARN", "value": batch_job_environment.job_queue_arn},
                            {
                                "name": "RECONSTRUCTION_JOB_DEFINITION_ID",
                                "value": reconstruction_batch_job_definition.arn_prefix,
                            },
                            {"name": "FEATURES_JOB_DEFINITION_ID", "value": features_batch_job_definition.arn_prefix},
                            {
                                "name": "_API_DATABASE_PASSWORD_VERSION",
                                "value": api_database_password_secret.version_id,
                            },
                        ],
                    }
                },
            },
            opts=ResourceOptions.merge(self._child_opts, ResourceOptions(depends_on=[database])),
        )

        # Allow service deployment
        deploy_role.allow_service_deployment("api", passroles=[execution_role, task_role], services=[service.service])
        deploy_role.allow_batch_job_definition_update(
            "api",
            passroles=[
                features_batch_job_definition.job_role,
                features_batch_job_definition.execution_role,
                reconstruction_batch_job_definition.job_role,
                reconstruction_batch_job_definition.execution_role,
            ],
            job_definitions=[features_batch_job_definition, reconstruction_batch_job_definition],
        )
