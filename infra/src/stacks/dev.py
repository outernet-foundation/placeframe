from typing import cast

from pulumi import Config, Output, StackReference, export
from pulumi_aws.ecs import Cluster

from components.cloudbeaver import create_cloudbeaver
from components.database import create_database
from components.gateway import create_gateway
from components.lambdas import create_lambda
from components.security_group import SecurityGroup
from components.storage import create_storage
from components.vpc import Vpc, VpcInfo


def create_dev_stack(config: Config):
    vpc = Vpc(
        name="main-vpc",
        vpc_info=cast(Output[VpcInfo], StackReference("tyler-s-hatch/plerion_infra/core").require_output("vpc-info")),
    )

    lambda_security_group = SecurityGroup("lambda-security-group", vpc_id=vpc.id)
    cloudbeaver_security_group = SecurityGroup("cloudbeaver-security-group", vpc_id=vpc.id)
    postgres_security_group = SecurityGroup("postgres-security-group", vpc_id=vpc.id)

    # 1. S3 bucket (captures)
    captures_bucket = create_storage(config)

    # 2. Postgres database
    postgres_instance, connection_string = create_database(config, postgres_security_group, vpc.private_subnet_ids)

    cluster = Cluster("cluster")

    create_cloudbeaver(
        config,
        vpc=vpc,
        cluster=cluster,
        cloudbeaver_security_group=cloudbeaver_security_group,
        postgres_security_group=postgres_security_group,
        db=postgres_instance,
    )

    # 3. Lambda (container image)
    api_lambda = create_lambda(
        config,
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

    # 4. API Gateway → Lambda proxy
    api_endpoint_output = create_gateway(api_lambda)

    # 5. Stack outputs
    export("apiUrl", api_endpoint_output)
    export("capturesBucketId", captures_bucket.id)
    export("dbEndpointAddress", postgres_instance.address)
