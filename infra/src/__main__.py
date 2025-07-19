import pulumi
from pulumi import Config

from components import vpc
from components.database import create_database
from components.gateway import create_gateway
from components.lambdas import create_lambda
from components.minio import create_minio
from components.storage import create_storage

# Stack config (region comes from pulumi config aws:region)
config = Config()

# 0. VPC with security groups
my_vpc, lambda_sg, db_sg = vpc.create_vpc()

# 1. S3 bucket (captures)
captures_bucket = create_storage(config)

create_minio(config, vpc=my_vpc, s3_bucket=captures_bucket)

# 2. Postgres database
postgres_instance, connection_string = create_database(
    config, db_sg, my_vpc.private_subnet_ids
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
    vpc_subnet_ids=my_vpc.private_subnet_ids,
    vpc_security_group_ids=[lambda_sg.id],
)

# 4. API Gateway → Lambda proxy
api_endpoint_output = create_gateway(api_lambda)

# 5. Stack outputs
pulumi.export("apiUrl", api_endpoint_output)
pulumi.export("capturesBucketId", captures_bucket.id)
pulumi.export("dbEndpointAddress", postgres_instance.address)
