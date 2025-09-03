from pulumi import ComponentResource, Config, Output, ResourceOptions, StackReference, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.efs import FileSystem, MountTarget
from pulumi_aws.rds import Instance
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.load_balancer import LoadBalancer
from components.log import log_configuration
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
        core_stack: StackReference,
        vpc: Vpc,
        postgres_security_group: SecurityGroup,
        db: Instance,
        cluster: Cluster,
        prepare_deploy_role: Role,
        deploy_role: Role,
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

        # Security Groups
        efs_security_group = SecurityGroup("cloudbeaver-efs-security-group", vpc=vpc, opts=self._child_opts)

        cloudbeaver_security_group = SecurityGroup(
            "cloudbeaver-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            rules=[
                {"to_security_group": efs_security_group, "ports": [2049]},
                {"to_security_group": postgres_security_group, "ports": [5432]},
            ],
            opts=self._child_opts,
        )

        load_balancer_security_group = SecurityGroup(
            "load-balancer-security-group",
            vpc=vpc,
            rules=[
                {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
                {"to_security_group": cloudbeaver_security_group, "ports": [4180]},
            ],
            opts=self._child_opts,
        )

        # EFS
        efs = FileSystem("cloudbeaver-efs", opts=self._child_opts)
        mount_targets = vpc.private_subnet_ids.apply(
            lambda subnet_ids: [
                MountTarget(
                    f"efs-mount-{subnet_id[-8:]}",
                    file_system_id=efs.id,
                    subnet_id=subnet_id,
                    security_groups=[efs_security_group.id],
                    opts=self._child_opts,
                )
                for subnet_id in subnet_ids
            ]
        )

        # Load balancer
        load_balancer = LoadBalancer(
            "cloudbeaver-loadbalancer",
            "cloudbeaver",
            vpc=vpc,
            securityGroup=load_balancer_security_group,
            certificate_arn=core_stack.require_output("certificate-arn"),
            port=4180,
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
        domain = Output.concat("cloudbeaver.", core_stack.require_output("zone-name"))
        Record(
            "cloudbeaver-domain-record",
            zone_id=core_stack.require_output("zone-id"),
            name=domain,
            type="A",
            aliases=[
                {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = ecs_execution_role("cloudbeaver-execution-role", opts=self._child_opts)
        execution_role.allow_secret_get([cloudbeaver_password_secret, postgres_password_secret])
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
                            "root_directory":
                            # Ensure all mount targets are created before using the EFS
                            mount_targets.apply(lambda mts: Output.all(*[mt.id for mt in mts]).apply(lambda _: "/")),
                        },
                    }
                ],
                "containers": {
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
                            {"name": "POSTGRES_HOST", "value": db.address},
                            {"name": "POSTGRES_PORT", "value": "5432"},
                            {"name": "POSTGRES_DB", "value": "postgres"},
                            {"name": "POSTGRES_USER", "value": config.require("postgres-user")},
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
                        # "port_mappings": [
                        #     {"container_port": 8978, "host_port": 8978, "target_group": load_balancer.target_group}
                        # ],
                        "secrets": [
                            {"name": "CLOUDBEAVER_DB_PASSWORD", "value_from": postgres_password_secret.arn},
                            {"name": "CB_ADMIN_PASSWORD", "value_from": cloudbeaver_password_secret.arn},
                        ],
                        "environment": [
                            {"name": "CB_SERVER_NAME", "value": "CloudBeaver"},
                            {"name": "CB_SERVER_URL", "value": domain.apply(lambda d: f"https://{d}")},
                            {"name": "CB_ADMIN_NAME", "value": config.require("cloudbeaver-user")},
                            {"name": "CLOUDBEAVER_DB_DRIVER", "value": "postgres-jdbc"},
                            {
                                "name": "CLOUDBEAVER_DB_URL",
                                "value": Output.concat(
                                    "jdbc:postgresql://", db.address, ":", db.port.apply(str), "/postgres"
                                ),
                            },
                            {"name": "CLOUDBEAVER_DB_USER", "value": config.require("postgres-user")},
                            {"name": "CLOUDBEAVER_DB_SCHEMA", "value": "cloudbeaver"},
                            {"name": "CLOUDBEAVER_DB_USER_VERSION", "value": postgres_password_secret.version_id},
                            {
                                "name": "_CLOUDBEAVER_DB_PASSWORD_VERSION",
                                "value": cloudbeaver_password_secret.version_id,
                            },
                        ],
                    },
                    "oauth2-proxy": {
                        "name": "oauth2-proxy",
                        "image": oauth_image_repo.locked_digest(),
                        "log_configuration": log_configuration(cloudbeaver_log_group),
                        "port_mappings": [
                            {"container_port": 4180, "host_port": 4180, "target_group": load_balancer.target_group}
                        ],
                        "environment": [
                            {"name": "OAUTH2_PROXY_PROVIDER", "value": "github"},
                            # Central callback on auth.* (single OAuth App for all subdomains)
                            {
                                "name": "OAUTH2_PROXY_REDIRECT_URL",
                                "value": Output.concat(
                                    "https://", "auth.", core_stack.require_output("zone-name"), "/oauth2/callback"
                                ),
                            },
                            {"name": "OAUTH2_PROXY_UPSTREAMS", "value": "http://127.0.0.1:8978/"},
                            {"name": "OAUTH2_PROXY_EMAIL_DOMAINS", "value": "*"},
                            {"name": "OAUTH2_PROXY_COOKIE_SECURE", "value": "true"},
                            {"name": "OAUTH2_PROXY_COOKIE_SAMESITE", "value": "lax"},
                            {"name": "OAUTH2_PROXY_REVERSE_PROXY", "value": "true"},
                            {"name": "OAUTH2_PROXY_SET_XAUTHREQUEST", "value": "true"},
                            {"name": "OAUTH2_PROXY_PASS_AUTHORIZATION_HEADER", "value": "true"},
                            {"name": "OAUTH2_PROXY_PASS_HOST_HEADER", "value": "true"},
                            # Shared cookie scope across subdomains
                            {
                                "name": "OAUTH2_PROXY_COOKIE_DOMAINS",
                                "value": Output.concat(".", core_stack.require_output("zone-name")),
                            },
                            {
                                "name": "OAUTH2_PROXY_WHITELIST_DOMAIN",
                                "value": Output.concat(".", core_stack.require_output("zone-name")),
                            },
                            # IMPORTANT: listen on all interfaces for the ALB target
                            {"name": "OAUTH2_PROXY_HTTP_ADDRESS", "value": "0.0.0.0:4180"},
                            # Optional allow-list (reuse what you put on auth.*)
                            # {"name": "OAUTH2_PROXY_GITHUB_USER", "value": config.get("oauth-allowed-users") or ""},
                            # {"name": "OAUTH2_PROXY_GITHUB_ORG", "value": config.get("oauth-org") or ""},
                            # {"name": "OAUTH2_PROXY_GITHUB_TEAM", "value": config.get("oauth-team") or ""},
                        ],
                        "secrets": [
                            {"name": "OAUTH2_PROXY_CLIENT_ID", "value_from": github_client_id_secret.arn},
                            {"name": "OAUTH2_PROXY_CLIENT_SECRET", "value_from": github_client_secret_secret.arn},
                            {"name": "OAUTH2_PROXY_COOKIE_SECRET", "value_from": cookie_secret_secret.arn},
                        ],
                    },
                },
            },
            opts=self._child_opts,
        )

        deploy_role.allow_service_deployment(
            "cloudbeaver", passroles=[execution_role, task_role], services=[cloudbeaver_service.service]
        )
