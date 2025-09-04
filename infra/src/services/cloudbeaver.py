from pulumi import ComponentResource, Config, Input, Output, ResourceOptions, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.rds import Instance
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.efs import EFS
from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.oauth import Oauth
from components.repository import Repository
from components.role import Role
from components.roles import ecs_execution_role, ecs_role
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


class Cloudbeaver(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        zone_name: Input[str],
        zone_id: Input[str],
        certificate_arn: Input[str],
        vpc: Vpc,
        postgres_security_group: SecurityGroup,
        db: Instance,
        cluster: Cluster,
        prepare_deploy_role: Role,
        deploy_role: Role,
        oauth: Oauth,
        *,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:Cloudbeaver", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Log groups
        cloudbeaver_log_group = LogGroup(
            "cloudbeaver-log-group", name="/ecs/cloudbeaver", retention_in_days=7, opts=self._child_opts
        )
        cloudbeaver_init_log_group = LogGroup(
            "cloudbeaver-init-log-group", name="/ecs/cloudbeaver-init", retention_in_days=7, opts=self._child_opts
        )

        # Secrets
        postgres_password_secret = Secret(
            "postgres-secret", secret_string=config.require_secret("postgres-password"), opts=self._child_opts
        )
        cloudbeaver_password_secret = Secret(
            "cloudbeaver-secret", secret_string=config.require_secret("cloudbeaver-password"), opts=self._child_opts
        )

        # Image repos
        cloudbeaver_init_image_repo = Repository(
            "cloudbeaver-init-repo",
            name="cloudbeaver-init",
            opts=ResourceOptions.merge(
                self._child_opts, ResourceOptions(retain_on_delete=True, import_="cloudbeaver-init")
            ),
        )
        cloudbeaver_image_repo = Repository(
            "cloudbeaver-repo",
            name="dockerhub/dbeaver/cloudbeaver",
            opts=ResourceOptions.merge(
                self._child_opts, ResourceOptions(retain_on_delete=True, import_="dockerhub/dbeaver/cloudbeaver")
            ),
        )
        prepare_deploy_role.allow_image_repo_actions([cloudbeaver_init_image_repo, cloudbeaver_image_repo])
        export("cloudbeaver-init-image-repo-url", cloudbeaver_init_image_repo.url)
        export("cloudbeaver-image-repo-url", cloudbeaver_image_repo.url)

        # EFS
        efs = EFS("cloudbeaver-efs", vpc=vpc, opts=self._child_opts)

        # Security Groups
        cloudbeaver_security_group = SecurityGroup(
            "cloudbeaver-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            rules=[
                {"to_security_group": efs.security_group, "ports": [2049]},
                {"to_security_group": postgres_security_group, "ports": [5432]},
            ],
            opts=self._child_opts,
        )

        load_balancer_security_group = SecurityGroup(
            "load-balancer-security-group",
            vpc=vpc,
            rules=[
                {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
                {"to_security_group": cloudbeaver_security_group, "ports": [4181]},
            ],
            opts=self._child_opts,
        )

        # Load balancer
        load_balancer = LoadBalancer(
            "cloudbeaver-loadbalancer",
            "cloudbeaver",
            vpc=vpc,
            securityGroup=load_balancer_security_group,
            certificate_arn=certificate_arn,
            port=4181,
            opts=self._child_opts,
            health_check={
                "path": "/ping",
                "protocol": "HTTP",
                "interval": 15,
                "healthy_threshold": 2,
                "unhealthy_threshold": 10,
            },
        )

        # DNS Records
        domain = Output.concat("cloudbeaver.", zone_name)
        Record(
            "cloudbeaver-domain-record",
            zone_id=zone_id,
            name=domain,
            type="A",
            aliases=[
                {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = ecs_execution_role("cloudbeaver-execution-role", opts=self._child_opts)
        execution_role.allow_secret_get(
            "cloudbeaver-secrets",
            [
                cloudbeaver_password_secret,
                postgres_password_secret,
                oauth.client_id_secret,
                oauth.client_secret_secret,
                oauth.cookie_secret_secret,
            ],
        )
        execution_role.allow_repo_pullthrough([cloudbeaver_image_repo])

        # Task role
        task_role = ecs_role("cloudbeaver-task-role", opts=self._child_opts)

        # Service
        cloudbeaver_service = FargateService(
            "cloudbeaver-service",
            name="cloudbeaver-service",
            cluster=cluster.arn,
            desired_count=1,
            network_configuration={
                "subnets": vpc.private_subnet_ids,
                "security_groups": [cloudbeaver_security_group.id],
            },
            task_definition_args={
                "execution_role": {"role_arn": execution_role.arn},
                "task_role": {"role_arn": task_role.arn},
                "volumes": [
                    {
                        "name": "efs",
                        "efs_volume_configuration": {
                            "file_system_id": efs.id,
                            "transit_encryption": "ENABLED",
                            "root_directory": "/",
                        },
                    }
                ],
                "containers": {
                    "oauth2-proxy": oauth.proxy_task_definition(
                        config=config,
                        zone_name=zone_name,
                        log_group=cloudbeaver_log_group,
                        proxy_upstreams="http://127.0.0.1:8978/",
                    ),
                    "oauth2-reverse-proxy": oauth.reverse_proxy_task_definition(
                        log_group=cloudbeaver_log_group, load_balancer=load_balancer
                    ),
                    "cloudbeaver-init": {
                        "name": "cloudbeaver-init",
                        "image": cloudbeaver_init_image_repo.locked_digest(),
                        "essential": False,
                        "log_configuration": log_configuration(cloudbeaver_init_log_group),
                        "mount_points": [{"source_volume": "efs", "container_path": "/opt/cloudbeaver/workspace"}],
                        "secrets": [
                            {"name": "POSTGRES_PASSWORD", "value_from": postgres_password_secret.arn},
                            {"name": "CB_ADMIN_PASSWORD", "value_from": cloudbeaver_password_secret.arn},
                        ],
                        "environment": [
                            {"name": "POSTGRES_USER", "value": config.require("postgres-user")},
                            {"name": "POSTGRES_HOST", "value": db.address},
                            {"name": "POSTGRES_PORT", "value": "5432"},
                            {"name": "POSTGRES_DB", "value": "postgres"},
                            {"name": "CB_ADMIN_NAME", "value": config.require("cloudbeaver-user")},
                            {"name": "_CB_ADMIN_NAME_VERSION", "value": cloudbeaver_password_secret.version_id},
                            {"name": "_POSTGRES_PASSWORD_VERSION", "value": postgres_password_secret.version_id},
                        ],
                    },
                    "cloudbeaver": {
                        "name": "cloudbeaver",
                        "depends_on": [{"container_name": "cloudbeaver-init", "condition": "SUCCESS"}],
                        "image": cloudbeaver_image_repo.locked_digest(),
                        "log_configuration": log_configuration(cloudbeaver_log_group),
                        "mount_points": [{"source_volume": "efs", "container_path": "/opt/cloudbeaver/workspace"}],
                    },
                },
            },
            opts=self._child_opts,
        )

        deploy_role.allow_service_deployment(
            "cloudbeaver", passroles=[execution_role, task_role], services=[cloudbeaver_service.service]
        )
