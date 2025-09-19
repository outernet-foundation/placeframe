from pulumi import ComponentResource, Config, Input, ResourceOptions, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.lambda_ import Function

from components.efs import EFS
from components.rds import RDSInstance
from components.repository import Repository
from components.role import Role
from components.roles import lambda_role
from components.security_group import SecurityGroup
from components.vpc import Vpc


class DatabaseManager(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        vpc: Vpc,
        efs: EFS,
        rds: RDSInstance,
        ecs_cluster_arn: Input[str],
        cloudbeaver_service_arn: Input[str] | None,
        prepare_deploy_role: Role,
        deploy_role: Role,
        *,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__("custom:DatabaseManager", resource_name, opts=opts)

        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        log_group = LogGroup(
            "database-manager-log-group",
            name="/aws/lambda/database-manager",
            retention_in_days=14,
            opts=self._child_opts,
        )

        repo = Repository("database-manager-image-repo", name="database-manager", opts=self._child_opts)
        prepare_deploy_role.allow_image_repo_actions("database-manager", [repo])

        # Security group
        security_group = SecurityGroup(
            "database-management-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "ecs", "secretsmanager", "logs", "sts", "s3"],
            rules=[
                {"to_security_group": efs.security_group, "ports": [2049]},
                {"to_security_group": rds.security_group, "ports": [5432]},
            ],
            opts=self._child_opts,
        )

        # Role
        self.role = lambda_role("database-manager-role", opts=self._child_opts)
        self.role.allow_secret_get("database-managersecrets", [rds.password_secret])
        export("database-manager-role-name", self.role.name)
        export("database-manager-role-arn", self.role.arn)

        if config.require_bool("deploy-database-manager") and cloudbeaver_service_arn is not None:
            self.role.allow_service_restart(
                "database-manager-cloudbeaver-restart", services_arns=[cloudbeaver_service_arn]
            )

            self.function = Function(
                "database-manager-function",
                name="database-manager",
                package_type="Image",
                image_uri=repo.locked_digest(),
                role=self.role.arn,
                timeout=900,
                memory_size=512,
                vpc_config={"security_group_ids": [security_group.id], "subnet_ids": vpc.private_subnet_ids},
                file_system_config={"arn": efs.access_point.arn, "local_mount_path": "/mnt/efs"},
                environment={
                    "variables": {
                        "BACKEND": "aws",
                        "POSTGRES_HOST": rds.address,
                        "POSTGRES_ADMIN_USER": config.require("postgres-user"),
                        "POSTGRES_ADMIN_PASSWORD_SECRET_ARN": rds.password_secret.arn,
                        "ECS_CLUSTER_ARN": ecs_cluster_arn,
                        "CLOUDBEAVER_SERVICE_ID": cloudbeaver_service_arn,
                        "POSTGRES_PASSWORD_VERSION_": rds.password_secret.version_id,
                    }
                },
                opts=ResourceOptions.merge(self._child_opts, ResourceOptions(depends_on=[log_group])),
            )

            export("database-manager-function-arn", self.function.arn)

            deploy_role.allow_lambda_deployment(resource_name, [self.function])

        self.register_outputs({})
