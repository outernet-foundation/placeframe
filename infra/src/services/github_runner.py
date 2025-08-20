from pulumi import ComponentResource, Config, ResourceOptions, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_awsx.ecs import FargateService

from components.log import log_configuration
from components.repository import Repository
from components.role import Role, ecs_assume_role_policy
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


class GithubRunner(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        vpc: Vpc,
        cluster: Cluster,
        postgres_security_group: SecurityGroup,
        prepare_deploy_role: Role,
        deploy_role: Role,
        *,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__("custom:GithubRunner", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Log groups
        github_runner_log_group = LogGroup(
            "github-runner-log-group", name="/ecs/github-runner", retention_in_days=7, opts=self._child_opts
        )

        # Secrets
        github_app_private_key_secret = Secret(
            "github-app-secret", secret_string=config.require_secret("github-app-private-key"), opts=self._child_opts
        )

        # Image repos
        github_runner_image_repo = Repository(
            "github-runner-cache-repo",
            name="dockerhub/myoung34/github-runner",
            force_delete=config.require_bool("devMode"),
            opts=ResourceOptions.merge(
                self._child_opts, ResourceOptions(retain_on_delete=True, import_="dockerhub/myoung34/github-runner")
            ),
        )
        prepare_deploy_role.allow_image_repo_actions([github_runner_image_repo])
        export("github-runner-image-repo-url", github_runner_image_repo.url)

        # Security groups
        github_runner_security_group = SecurityGroup(
            "github-runner-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            rules=[
                {"cidr_name": "anywhere", "to_cidr": "0.0.0.0/0", "ports": [443]},  # Allow egress to the GitHub API
                {"to_security_group": postgres_security_group, "ports": [5432]},
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = Role(
            "github-runner-execution-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts
        )
        execution_role.attach_ecs_task_execution_role_policy()
        execution_role.allow_secret_get([github_app_private_key_secret])
        execution_role.allow_repo_pullthrough([github_runner_image_repo])

        # Task role
        task_role = Role("github-runner-task-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts)

        # Service
        service = FargateService(
            "github-runner-service",
            name="github-runner-service",
            cluster=cluster.arn,
            desired_count=1,
            network_configuration={
                "subnets": vpc.private_subnet_ids,
                "security_groups": [github_runner_security_group.id],
            },
            task_definition_args={
                "execution_role": {"role_arn": execution_role.arn},
                "task_role": {"role_arn": task_role.arn},
                "containers": {
                    "runner": {
                        "name": "runner",
                        "image": github_runner_image_repo.locked_digest(),
                        "log_configuration": log_configuration(github_runner_log_group),
                        "secrets": [{"name": "APP_PRIVATE_KEY", "value_from": github_app_private_key_secret.arn}],
                        "environment": [
                            {"name": "APP_ID", "value": config.require("github-app-id")},
                            {"name": "APP_LOGIN", "value": config.require("github-org")},
                            {"name": "RUNNER_SCOPE", "value": "org"},
                            {"name": "ORG_NAME", "value": config.require("github-org")},
                            {"name": "APP_PRIVATE_KEY_VERSION", "value": github_app_private_key_secret.version_id},
                        ],
                    }
                },
            },
            opts=self._child_opts,
        )

        deploy_role.allow_service_deployment(
            "github-runner", [service.service.arn], [execution_role.arn, task_role.arn]
        )
