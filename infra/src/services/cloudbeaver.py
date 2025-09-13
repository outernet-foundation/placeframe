from pulumi import ComponentResource, Config, Input, Output, ResourceOptions
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.efs import AccessPoint
from pulumi_aws.lambda_ import Function
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.efs import EFS
from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.oauth import Oauth
from components.rds import RDSInstance
from components.repository import Repository
from components.role import Role
from components.roles import ecs_execution_role, ecs_role, lambda_role
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
        rds: RDSInstance,
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
        initialize_cloudbeaver_log_group = LogGroup(
            "initialize-cloudbeaver-log-group",
            name="/ecs/initialize-cloudbeaver",
            retention_in_days=7,
            opts=self._child_opts,
        )

        # Secrets
        self.password_secret = Secret(
            "cloudbeaver-secret", secret_string=config.require_secret("cloudbeaver-password"), opts=self._child_opts
        )

        # Image repos
        initialize_cloudbeaver_image_repo = Repository(
            "initialize-cloudbeaver-repo",
            name="initialize-cloudbeaver",
            opts=ResourceOptions.merge(self._child_opts, ResourceOptions(retain_on_delete=True)),
        )
        cloudbeaver_image_repo = Repository(
            "cloudbeaver-repo",
            name="dockerhub/dbeaver/cloudbeaver",
            opts=ResourceOptions.merge(self._child_opts, ResourceOptions(retain_on_delete=True)),
        )
        create_database_image_repo = Repository(
            "create-database-repo",
            name="create-database",
            opts=ResourceOptions.merge(self._child_opts, ResourceOptions(retain_on_delete=True)),
        )
        delete_database_image_repo = Repository(
            "delete-database-repo",
            name="delete-database",
            opts=ResourceOptions.merge(self._child_opts, ResourceOptions(retain_on_delete=True)),
        )
        prepare_deploy_role.allow_image_repo_actions(
            "cloudbeaver",
            [
                initialize_cloudbeaver_image_repo,
                cloudbeaver_image_repo,
                create_database_image_repo,
                delete_database_image_repo,
            ],
        )

        # Load balancer
        self.load_balancer = LoadBalancer(
            "cloudbeaver-loadbalancer",
            "cloudbeaver",
            vpc=vpc,
            certificate_arn=certificate_arn,
            target_port=4181,
            ingress_cidr="0.0.0.0/0",
            opts=self._child_opts,
            health_check={
                "path": "/ping",
                "protocol": "HTTP",
                "interval": 15,
                "healthy_threshold": 2,
                "unhealthy_threshold": 10,
            },
        )

        # EFS
        efs = EFS("cloudbeaver-efs", vpc=vpc, opts=self._child_opts)

        # Security group
        cloudbeaver_security_group = SecurityGroup(
            "cloudbeaver-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            rules=[
                {"from_security_group": self.load_balancer.security_group, "ports": [4181]},
                {"to_security_group": efs.security_group, "ports": [2049]},
                {"to_security_group": rds.security_group, "ports": [5432]},
            ],
            opts=self._child_opts,
        )

        # DNS Records
        domain = Output.concat("cloudbeaver.", zone_name)
        Record(
            "cloudbeaver-domain-record",
            zone_id=zone_id,
            name=domain,
            type="A",
            aliases=[
                {
                    "name": self.load_balancer.dns_name,
                    "zone_id": self.load_balancer.zone_id,
                    "evaluate_target_health": True,
                }
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = ecs_execution_role("cloudbeaver-execution-role", opts=self._child_opts)
        execution_role.allow_secret_get(
            "cloudbeaver-secrets",
            [
                self.password_secret,
                rds.password_secret,
                oauth.client_id_secret,
                oauth.client_secret_secret,
                oauth.cookie_secret_secret,
            ],
        )
        execution_role.allow_repo_pullthrough([cloudbeaver_image_repo])

        # Task role
        task_role = ecs_role("cloudbeaver-task-role", opts=self._child_opts)

        if config.require_bool("deploy-cloudbeaver"):
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
                            log_group=cloudbeaver_log_group, load_balancer=self.load_balancer
                        ),
                        "initialize-cloudbeaver": {
                            "name": "initialize-cloudbeaver",
                            "image": initialize_cloudbeaver_image_repo.locked_digest(),
                            "essential": False,
                            "log_configuration": log_configuration(initialize_cloudbeaver_log_group),
                            "mount_points": [{"source_volume": "efs", "container_path": "/opt/cloudbeaver/workspace"}],
                            "secrets": [
                                {"name": "POSTGRES_PASSWORD", "value_from": rds.password_secret.arn},
                                {"name": "CB_ADMIN_PASSWORD", "value_from": self.password_secret.arn},
                            ],
                            "environment": [
                                {"name": "POSTGRES_USER", "value": config.require("postgres-user")},
                                {"name": "POSTGRES_HOST", "value": rds.address},
                                {"name": "POSTGRES_PORT", "value": "5432"},
                                {"name": "POSTGRES_DB", "value": "postgres"},
                                {"name": "CB_ADMIN_NAME", "value": config.require("cloudbeaver-user")},
                                {"name": "_CB_ADMIN_NAME_VERSION", "value": self.password_secret.version_id},
                                {"name": "_POSTGRES_PASSWORD_VERSION", "value": rds.password_secret.version_id},
                            ],
                        },
                        "cloudbeaver": {
                            "name": "cloudbeaver",
                            "depends_on": [{"container_name": "initialize-cloudbeaver", "condition": "SUCCESS"}],
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

            # Database management Lambdas

            # Security group
            database_management_security_group = SecurityGroup(
                "database-management-security-group",
                vpc=vpc,
                vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
                rules=[
                    {"to_security_group": efs.security_group, "ports": [2049]},
                    {"to_security_group": rds.security_group, "ports": [5432]},
                ],
                opts=self._child_opts,
            )

            # EFS Access Point
            efs_access_point = AccessPoint(
                "database-management-efs-access-point",
                file_system_id=efs.id,
                posix_user={"uid": 1000, "gid": 1000},
                root_directory={
                    "path": "/opt/cloudbeaver/workspace",
                    "creation_info": {"owner_uid": 1000, "owner_gid": 1000, "permissions": "0775"},
                },
                opts=self._child_opts,
            )

            # Role
            database_management_role = lambda_role("cloudbeaver-lambda-role", opts=self._child_opts)
            database_management_role.allow_secret_get("cloudbeaver-lambda-secrets", [rds.password_secret])
            # role.allow_service_deployment() ? needs to be able to bounce cloudbeaver

            def DatabaseManagementLambda(resource_name: str, name: str, image_repo: Repository):
                log_group = LogGroup(
                    f"{resource_name}-log-group",
                    name=f"/aws/lambda/{name}",
                    retention_in_days=14,
                    opts=self._child_opts,
                )

                function = Function(
                    resource_name,
                    name=name,
                    package_type="Image",
                    image_uri=image_repo.locked_digest(),
                    role=database_management_role.arn,
                    timeout=900,
                    memory_size=512,
                    vpc_config={
                        "security_group_ids": [database_management_security_group.id],
                        "subnet_ids": vpc.private_subnet_ids,
                    },
                    file_system_config={"arn": efs_access_point.arn, "local_mount_path": "/mnt/efs"},
                    environment={
                        "variables": {
                            "BACKEND": "aws",
                            "POSTGRES_HOST": rds.address,
                            "POSTGRES_ADMIN_USER": config.require("postgres-user"),
                            "POSTGRES_ADMIN_PASSWORD_SECRET_ARN": rds.password_secret.arn,
                            "ECS_CLUSTER_ARN": cluster.arn,
                            "CLOUDBEAVER_SERVICE_ARN": cloudbeaver_service.service.arn,
                            "_POSTGRES_PASSWORD_VERSION": rds.password_secret.version_id,
                        }
                    },
                    opts=ResourceOptions.merge(
                        self._child_opts, ResourceOptions(depends_on=[log_group, database_management_security_group])
                    ),
                )

                deploy_role.allow_lambda_deployment(resource_name, [function])

            if config.require_bool("deploy-create-database"):
                DatabaseManagementLambda("create-database-lambda", "create-database", create_database_image_repo)

            if config.require_bool("deploy-delete-database"):
                DatabaseManagementLambda("delete-database-lambda", "delete-database", delete_database_image_repo)

        self.register_outputs({})
