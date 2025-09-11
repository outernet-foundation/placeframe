from __future__ import annotations

from pulumi import ComponentResource, Config, Input, Output, ResourceOptions, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.lambda_ import Function as LambdaFunction
from pulumi_aws.lambda_ import Permission as LambdaPermission
from pulumi_aws.lb import TargetGroupAttachment

from components.load_balancer import LoadBalancer
from components.rds import RDSInstance
from components.repository import Repository
from components.roles import lambda_role
from components.security_group import SecurityGroup
from components.vpc import Vpc
from services.cloudbeaver import Cloudbeaver


class DatabaseManager(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        certificate_arn: Input[str],
        vpc: Vpc,
        rds: RDSInstance,
        cloudbeaver: Cloudbeaver,
        *,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:DatabaseManager", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Log group
        LogGroup(
            f"{resource_name}-logs",
            name=Output.concat("/aws/lambda/database-manager"),
            retention_in_days=7,
            opts=self._child_opts,
        )

        # Image repo
        database_manager_image_repo = Repository(
            "database-manager-repo", name="database-manager", opts=self._child_opts
        )
        export("database-manager-image-repo-url", database_manager_image_repo.url)

        # Load balancer
        load_balancer = LoadBalancer(
            f"{resource_name}-load-balancer",
            service_name="database-manager",
            vpc=vpc,
            certificate_arn=certificate_arn,
            ingress_cidr=vpc.cidr_block,
            internal=True,
            target_type="lambda",
            opts=self._child_opts,
        )

        # Security group
        security_group = SecurityGroup(
            "database-manager-security-group",
            vpc=vpc,
            vpc_endpoints=[],
            rules=[
                {"to_security_group": load_balancer.security_group, "ports": [443]},
                {"to_security_group": rds.security_group, "ports": [5432]},
                {"to_security_group": cloudbeaver.load_balancer.security_group, "ports": [443]},
            ],
            opts=self._child_opts,
        )

        # Role
        role = lambda_role(f"{resource_name}-lambda-role", opts=self._child_opts)

        # Service
        if config.require_bool("deploy-database-manager"):
            lambda_function = LambdaFunction(
                "database-manager-lambda-function",
                name="database-manager-lambda-function",
                role=role.arn,
                package_type="Image",
                image_uri=database_manager_image_repo.locked_digest(),  # <repo>@sha256:...
                architectures=["x86_64"],  # hardcoded
                memory_size=1024,  # hardcoded
                timeout=60,  # hardcoded
                vpc_config={"subnet_ids": vpc.private_subnet_ids, "security_group_ids": [security_group.id]},
                environment={
                    "variables": {
                        "POSTGRES_HOST": rds.address,
                        "POSTGRES_USER": config.require("postgres-user"),
                        "CLOUDBEAVER_URL": cloudbeaver.load_balancer.dns_name,
                        "CLOUDBEAVER_ADMIN_USER": config.require("cloudbeaver-user"),
                        "POSTGRES_PASSWORD_ARN": rds.password_secret.arn,
                        "CLOUDBEAVER_ADMIN_PASSWORD_ARN": cloudbeaver.password_secret.arn,
                        # Force redeployment when secrets change
                        "POSTGRES_PASSWORD_VERSION": rds.password_secret.version_id,
                        "CLOUDBEAVER_ADMIN_PASSWORD_VERSION": cloudbeaver.password_secret.version_id,
                    }
                },
                opts=self._child_opts,
            )

            permission = LambdaPermission(
                f"{resource_name}-invoke",
                action="lambda:InvokeFunction",
                function=lambda_function.name,
                principal="elasticloadbalancing.amazonaws.com",
                source_arn=load_balancer.target_group.arn,
                opts=self._child_opts,
            )

            TargetGroupAttachment(
                f"{resource_name}-tga",
                target_group_arn=load_balancer.target_group.arn,
                target_id=lambda_function.arn,
                opts=self._child_opts.merge(ResourceOptions(depends_on=[permission])),
            )

        self.register_outputs({})
