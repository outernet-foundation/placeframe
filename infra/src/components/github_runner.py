import json
from pathlib import Path

from pulumi import Config, Output
from pulumi_aws import get_region_output
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.ecs import Cluster
from pulumi_awsx.ecs import FargateService
from pulumi_docker import Image

from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_github_runner(config: Config, vpc: Vpc, cluster: Cluster):
    github_pat = config.require_secret("github-pat")  # your GitHub registration token

    github_runner_security_group = SecurityGroup("github-runner-security-group", vpc_id=vpc.id)

    policy = github_pat.arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": [arn]}, {}],
        })
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
            "subnets": vpc.private_subnet_ids,  # so it can hit your DB
            "security_groups": [github_runner_security_group],  # allow outbound 5432
        },
        task_definition_args={
            "family": "gh-runner-task",
            "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
            "container": {
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
                "secrets": [{"name": "GH_PAT", "value_from": github_pat.arn}],
            },
        },
    )
