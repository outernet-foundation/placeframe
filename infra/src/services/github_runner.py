from pulumi import Config, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_awsx.ecs import FargateService

from components.log import log_configuration
from components.repository import Repository
from components.role import Role, ecs_assume_role_policy
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_github_runner(config: Config, vpc: Vpc, cluster: Cluster, postgres_security_group: SecurityGroup) -> None:
    # Log groups
    github_runner_log_group = LogGroup("github-runner-log-group", name="/ecs/github-runner", retention_in_days=7)

    # Secrets
    github_app_private_key_secret = Secret(
        "github-app-secret", secret_string=config.require_secret("github-app-private-key")
    )

    # Image repos
    github_runner_image_repo = Repository(
        "github-runner-cache-repo", name="dockerhub/myoung34/github-runner", force_delete=config.require_bool("devMode")
    )
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
    )

    # Execution role
    execution_role = Role("github-runner-execution-role", assume_role_policy=ecs_assume_role_policy())
    execution_role.allow_secret_get([github_app_private_key_secret])
    execution_role.allow_repo_pullthrough([github_runner_image_repo])

    digest = github_runner_image_repo.locked_digest()

    if not digest:
        return

    # Service
    FargateService(
        "github-runner-service",
        name="github-runner-service",
        cluster=cluster.arn,
        desired_count=1,
        network_configuration={
            # TODO: create a nat instance instead of using public subnets
            "subnets": vpc.public_subnet_ids,
            "security_groups": [github_runner_security_group.id],
            "assign_public_ip": True,
        },
        task_definition_args={
            "execution_role": {"role_arn": execution_role.arn},
            "containers": {
                "runner": {
                    "name": "runner",
                    "image": digest,
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
    )
