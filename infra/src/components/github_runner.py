import json
from pathlib import Path

from pulumi import Config, Output
from pulumi_aws import get_caller_identity, get_region_output
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.ecs import Cluster
from pulumi_awsx.ecs import FargateService
from pulumi_command.local import Command
from pulumi_docker import Image

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
        security_group=github_runner_security_group, interfaces=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts"]
    )

    # Allow egress for DNS resolution (required for curl and tailscale to resolve hostnames)
    github_runner_security_group.allow_egress_cidr(cidr_name="dns", cidr="0.0.0.0/0", ports=[53], protocol="udp")
    github_runner_security_group.allow_egress_cidr(cidr_name="dns", cidr="0.0.0.0/0", ports=[53], protocol="tcp")

    # Allow egress to the GitHub API
    github_runner_security_group.allow_egress_cidr(cidr_name="github-api", cidr="0.0.0.0/0", ports=[443])

    policy = github_app_private_key_secret.arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": [arn]}, {}],
        })
    )

    Command(
        "docker-login-ghcr",
        create=Output.concat(
            "echo ",
            config.require("github-pat"),
            " | docker login ghcr.io --username ",
            config.require("github-username"),
            " --password-stdin",
        ),
    )

    # Create a Docker image for GitHub Runner
    init_image_repo = Repository("github-runner-repo", force_delete=config.require_bool("devMode"))
    dockerfile = Path(config.require("github-runner-dockerfile")).resolve()
    creds = get_authorization_token()
    image = Image(
        "github-runner-image",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=Output.concat(init_image_repo.repository_url, ":", "latest"),
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    # Create log groups
    LogGroup("github-runner-log-group", name="/ecs/github-runner", retention_in_days=7)

    FargateService(
        "github-runner-service",
        cluster=cluster.arn,
        desired_count=1,  # one runner; bump up for parallelism
        network_configuration={
            "subnets": vpc.public_subnet_ids,  # so it can hit your DB
            "security_groups": [github_runner_security_group],  # allow outbound 5432
            # TODO: create a nat instance instead of using public subnets
            "assign_public_ip": True,
        },
        task_definition_args={
            "family": "gh-runner-task",
            "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
            "containers": {
                "token-proxy": {
                    "name": "token-proxy",
                    "image": get_region_output().name.apply(
                        lambda r: f"{get_caller_identity().account_id}.dkr.ecr.{r}.amazonaws.com/ghcr/google-github-actions/github-runner-token-proxy:latest"
                    ),
                    "environment": [
                        {"name": "GH_APP_ID", "value": config.require("github-app-id")},
                        {"name": "GH_INSTALLATION_ID", "value": config.require("github-installation-id")},
                        {"name": "GH_REPO", "value": config.require("github-repo")},
                    ],
                    "secrets": [{"name": "GH_APP_PRIVATE_KEY", "value_from": github_app_private_key_secret.arn}],
                },
                "runner": {
                    "name": "runner",
                    "image": image.repo_digest,
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/github-runner",
                            "awslogs-region": get_region_output().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "environment": [
                        {"name": "GH_OWNER", "value": config.require("github-owner")},
                        {"name": "GH_REPO", "value": config.require("github-repo")},
                        {"name": "RUNNER_LABELS", "value": "self-hosted,fargate"},
                    ],
                },
            },
        },
    )
