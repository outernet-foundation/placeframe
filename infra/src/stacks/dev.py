from typing import cast

from pulumi import Config, Output, StackReference
from pulumi_aws.ecs import Cluster

from components.api import create_api
from components.cloudbeaver import create_cloudbeaver
from components.database import create_database
from components.github_runner import create_github_runner
from components.oidc import create_oidc
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

    github_runner_image_repo = create_github_runner(
        vpc=vpc, config=config, cluster=cluster, postgres_security_group=postgres_security_group
    )

    cloudbeaver_init_image_repo = create_cloudbeaver(
        config,
        core_stack,
        vpc=vpc,
        postgres_security_group=postgres_security_group,
        db=postgres_instance,
        cluster=cluster,
    )

    # 3. Lambda (container image)
    api_image_repo = create_api(
        config,
        core_stack,
        s3_bucket_arn=captures_bucket.arn,
        vpc=vpc,
        postgres_security_group=postgres_security_group,
        postgres_connection_secret=postgres_connection_secret,
    )

    create_oidc(
        config, postgres_connection_secret, [github_runner_image_repo, cloudbeaver_init_image_repo, api_image_repo]
    )
