from typing import cast

from pulumi import Config, Output, StackReference
from pulumi_aws.ecs import Cluster

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

    lambda_security_group = SecurityGroup("lambda-security-group", vpc_id=vpc.id)
    cloudbeaver_security_group = SecurityGroup("cloudbeaver-security-group", vpc_id=vpc.id)
    postgres_security_group = SecurityGroup("postgres-security-group", vpc_id=vpc.id)

    # 1. S3 bucket (captures)
    captures_bucket = create_storage(config)

    # 2. Postgres database
    postgres_instance, connection_string = create_database(config, postgres_security_group, vpc.private_subnet_ids)

    cluster = Cluster("dev-tooling-cluster")

    create_github_runner(vpc=vpc, config=config, cluster=cluster, postgres_security_group=postgres_security_group)

    create_cloudbeaver(
        config,
        core_stack,
        vpc=vpc,
        cloudbeaver_security_group=cloudbeaver_security_group,
        postgres_security_group=postgres_security_group,
        db=postgres_instance,
        cluster=cluster,
    )

    # 3. Lambda (container image)
    create_api(
        config,
        core_stack,
        environment_vars={
            # Pulumi Inputs are OK here; secrets stay secret
            "POSTGRES_DSN": connection_string,
            "CAPTURES_BUCKET": captures_bucket.bucket,
        },
        s3_bucket_arn=captures_bucket.arn,
        vpc=vpc,
        lambda_security_group=lambda_security_group,
        postgres_security_group=postgres_security_group,
    )
