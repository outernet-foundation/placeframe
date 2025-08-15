from pulumi import ComponentResource, Config, Output, ResourceOptions, StackReference, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.rds import Instance
from pulumi_aws.route53 import Record
from pulumi_aws.s3 import Bucket
from pulumi_awsx.ecs import FargateService

from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.repository import Repository
from components.role import Role, ecs_assume_role_policy
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


class Api(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        core_stack: StackReference,
        vpc: Vpc,
        cluster: Cluster,
        s3_bucket: Bucket,
        postgres_security_group: SecurityGroup,
        postgres_instance: Instance,
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

        # Secrets
        postgres_password_secret = Secret(
            "postgres-password", secret_string=config.require_secret("postgres-password"), opts=self._child_opts
        )

        # Image repos
        api_image_repo = Repository(
            "api-repo",
            "api",
            opts=ResourceOptions.merge(
                self._child_opts,
                ResourceOptions(retain_on_delete=True),
                # ResourceOptions(import_="api")
            ),
        )
        prepare_deploy_role.allow_image_repo_actions([api_image_repo])
        export("api-image-repo-url", api_image_repo.url)

        # Security groups
        api_security_group = SecurityGroup(
            "api-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            rules=[{"to_security_group": postgres_security_group, "ports": [5432]}],
            opts=self._child_opts,
        )

        load_balancer_security_group = SecurityGroup(
            "api-load-balancer-security-group",
            vpc=vpc,
            rules=[
                {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
                {"to_security_group": api_security_group, "ports": [8000]},
            ],
            opts=self._child_opts,
        )

        # Load balancer
        load_balancer = LoadBalancer(
            "api-loadbalancer",
            "api",
            vpc=vpc,
            securityGroup=load_balancer_security_group,
            certificate_arn=core_stack.require_output("certificate-arn"),
            port=8000,
            opts=self._child_opts,
        )

        # DNS Records
        domain = Output.concat("api.", core_stack.require_output("zone-name"))
        Record(
            "api-domain-record",
            zone_id=core_stack.require_output("zone-id"),
            name=domain,
            type="A",
            aliases=[
                {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = Role("api-execution-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts)
        execution_role.allow_secret_get([postgres_password_secret])
        execution_role.attach_ecs_task_execution_role_policy()

        # Task role
        task_role = Role("api-task-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts)
        task_role.allow_s3(s3_bucket)

        digest = api_image_repo.locked_digest()

        if not digest:
            return

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
                        "image": digest,
                        "log_configuration": log_configuration(api_log_group),
                        "port_mappings": [
                            {"container_port": 8000, "host_port": 8000, "target_group": load_balancer.target_group}
                        ],
                        "secrets": [{"name": "POSTGRES_PASSWORD", "value_from": postgres_password_secret.arn}],
                        "environment": [
                            {"name": "POSTGRES_USER", "value": postgres_instance.username},
                            {"name": "POSTGRES_HOST", "value": postgres_instance.address},
                            {"name": "_POSTGRES_PASSWORD_VERSION", "value": postgres_password_secret.version_id},
                        ],
                    }
                },
            },
            opts=self._child_opts,
        )

        # Allow the deployment role to deploy this service
        deploy_role.allow_service_deployment("api", [service.service.arn], [execution_role.arn, task_role.arn])
