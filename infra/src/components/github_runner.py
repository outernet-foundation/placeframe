from pulumi import Config
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository
from pulumi_aws.ecs import Cluster
from pulumi_awsx.ecs import FargateService

from components.ecr import pullthrough_repo_digest
from components.log import log_configuration
from components.role_policies import allow_repo_pullthrough, allow_secret_get
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
            "execution_role": {
                "args": {
                    "inline_policies": [
                        {"policy": allow_secret_get([github_app_private_key_secret])},
                        {"policy": allow_repo_pullthrough([github_runner_image_repo])},
                    ]
                }
            },
            "containers": {
                "runner": {
                    "name": "runner",
                    "image": pullthrough_repo_digest(github_runner_image_repo),
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
