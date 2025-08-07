import json
from typing import cast

from pulumi import Config, Output, StackReference, export
from pulumi_aws.ecs import Cluster
from pulumi_aws.iam import Role

from components.api import create_api
from components.cloudbeaver import create_cloudbeaver
from components.database import create_database
from components.github_runner import create_github_runner
from components.security_group import SecurityGroup
from components.storage import create_storage
from components.vpc import Vpc, VpcInfo


def create_dev_stack(config: Config):
    core_stack = StackReference("tyler-s-hatch/plerion_infra/core")

    vpc = Vpc(name="main-vpc", vpc_info=cast(Output[VpcInfo], core_stack.require_output("vpc-info")))

    postgres_security_group = SecurityGroup("postgres-security-group", vpc_id=vpc.id)

    # 1. S3 bucket (captures)
    captures_bucket = create_storage(config)

    # 2. Postgres database
    postgres_instance, postgres_connection_secret = create_database(config, postgres_security_group, vpc)

    cluster = Cluster("dev-tooling-cluster")

    create_github_runner(vpc=vpc, config=config, cluster=cluster, postgres_security_group=postgres_security_group)

    create_cloudbeaver(
        config,
        core_stack,
        vpc=vpc,
        postgres_security_group=postgres_security_group,
        db=postgres_instance,
        cluster=cluster,
    )

    # 3. Lambda (container image)
    create_api(
        config,
        core_stack,
        s3_bucket_arn=captures_bucket.arn,
        vpc=vpc,
        postgres_security_group=postgres_security_group,
        postgres_connection_secret=postgres_connection_secret,
    )

    github_org = config.require("github-org")
    github_repo = config.require("github-repo")
    github_oidc_provider_arn = core_stack.require_output("github_oidc_provider_arn")
    github_assume_role_policy = github_oidc_provider_arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Federated": arn},
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringLike": {
                            "token.actions.githubusercontent.com:sub": (
                                f"repo:{github_org}/{github_repo}:ref:refs/heads/{config.require('github-branch')}"
                            )
                        },
                        "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
                    },
                }
            ],
        })
    )

    github_actions_db_migrations_role = Role(
        "github-actions-db-migrations-role",
        assume_role_policy=github_assume_role_policy,
        inline_policies=[
            {
                "name": "db-secret-policy",
                "policy": postgres_connection_secret.arn.apply(
                    lambda arn: json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [
                            {"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"], "Resource": arn}
                        ],
                    })
                ),
            }
        ],
    )

    export("github_actions_db_migrations_role_arn", github_actions_db_migrations_role.arn)
