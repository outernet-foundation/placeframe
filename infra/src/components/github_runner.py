import json

from pulumi import Config
from pulumi_aws import get_caller_identity, get_region_output
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository
from pulumi_aws.ecs import Cluster
from pulumi_awsx.ecs import FargateService

from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_github_runner(config: Config, vpc: Vpc, cluster: Cluster, postgres_security_group: SecurityGroup) -> None:
    github_app_private_key_secret = Secret(
        "github-app-secret", secret_string=config.require_secret("github-app-private-key")
    )

    github_runner_security_group = SecurityGroup("github-runner-security-group", vpc_id=vpc.id)

    # Allow the runner to access Postgres
    github_runner_security_group.allow_egress_reciprocal(to_security_group=postgres_security_group, ports=[5432])

    # Private interface endpoints the task may hit (image pulls/logs/secrets)
    vpc.allow_endpoint_access(
        security_group=github_runner_security_group,
        endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
    )

    # Allow egress for DNS resolution (required for curl and tailscale to resolve hostnames)
    github_runner_security_group.allow_egress_cidr(cidr_name="dns", cidr="0.0.0.0/0", ports=[53], protocol="udp")
    github_runner_security_group.allow_egress_cidr(cidr_name="dns", cidr="0.0.0.0/0", ports=[53], protocol="tcp")

    # Allow egress to the GitHub API
    github_runner_security_group.allow_egress_cidr(cidr_name="github-api", cidr="0.0.0.0/0", ports=[443])

    policy = github_app_private_key_secret.base_arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": [arn]},
                {"Effect": "Allow", "Action": ["ecr:BatchImportUpstreamImage"], "Resource": "*"},
            ],
        })
    )

    Repository(
        "github-runner-cache-repo", name="dockerhub/myoung34/github-runner", force_delete=config.require_bool("devMode")
    )

    # Create log groups
    LogGroup("github-runner-log-group", name="/ecs/github-runner", retention_in_days=7)

    FargateService(
        "github-runner-service",
        name="github-runner-service",
        cluster=cluster.arn,
        desired_count=1,  # one runner; bump up for parallelism
        network_configuration={
            "subnets": vpc.public_subnet_ids,  # so it can hit your DB
            "security_groups": [github_runner_security_group.id],  # allow outbound 5432
            # TODO: create a nat instance instead of using public subnets
            "assign_public_ip": True,
        },
        task_definition_args={
            "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
            "containers": {
                "runner": {
                    "name": "runner",
                    "image": get_region_output().name.apply(
                        lambda r: f"{get_caller_identity().account_id}.dkr.ecr.{r}.amazonaws.com/dockerhub/myoung34/github-runner:latest"
                    ),
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/github-runner",
                            "awslogs-region": get_region_output().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "environment": [
                        {"name": "APP_ID", "value": config.require("github-app-id")},
                        {"name": "APP_LOGIN", "value": config.require("github-org")},
                        {"name": "RUNNER_SCOPE", "value": "org"},
                        {"name": "ORG_NAME", "value": config.require("github-org")},
                    ],
                    "secrets": [{"name": "APP_PRIVATE_KEY", "value_from": github_app_private_key_secret.versioned_arn}],
                }
            },
        },
    )
