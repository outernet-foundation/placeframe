import pulumi
import pulumi_aws as aws
import pulumi_aws.ec2 as ec2
import pulumi_awsx as awsx
from pulumi import Config

# from components import vpc
from components.cloudbeaver import create_cloudbeaver
from components.database import create_database
from components.gateway import create_gateway
from components.lambdas import create_lambda
from components.storage import create_storage
from util import ALLOW_ALL_EGRESS

# Stack config (region comes from pulumi config aws:region)
config = Config()

# 0. VPC with security groups
# Create a VPC with default subnet layout (public + private in each AZ)
vpc = awsx.ec2.Vpc(
    "main-vpc",
    nat_gateways={
        "strategy": awsx.ec2.NatGatewayStrategy.SINGLE,
    },
    enable_dns_hostnames=True,  # Add these
    enable_dns_support=True,  # explicitly
)

# Security group for Lambda functions: no inbound, all outbound
lambda_security_group = ec2.SecurityGroup(
    "lambda-security-group",
    vpc_id=vpc.vpc_id,
    egress=ALLOW_ALL_EGRESS,
)

cloudbeaver_security_group = aws.ec2.SecurityGroup(
    "cloudbeaver-security-group",
    vpc_id=vpc.vpc_id,
    egress=ALLOW_ALL_EGRESS,
)

# Security group for RDS: allow Lambda SG on port 5432, all outbound
postgres_security_group = ec2.SecurityGroup(
    "postgres-security-group",
    vpc_id=vpc.vpc_id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "security_groups": [
                lambda_security_group.id,
                cloudbeaver_security_group.id,
            ],
        }
    ],
)

# 1. S3 bucket (captures)
captures_bucket = create_storage(config)

# create_minio(config, vpc=my_vpc, s3_bucket=captures_bucket)

# 2. Postgres database
postgres_instance, connection_string = create_database(
    config, postgres_security_group, vpc.private_subnet_ids
)


cluster = aws.ecs.Cluster("cluster")

create_cloudbeaver(
    config,
    vpc=vpc,
    cluster=cluster,
    security_group=cloudbeaver_security_group,
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
    vpc_subnet_ids=vpc.private_subnet_ids,
    vpc_security_group_ids=[lambda_security_group.id],
)

# 4. API Gateway → Lambda proxy
api_endpoint_output = create_gateway(api_lambda)

# 5. Stack outputs
pulumi.export("apiUrl", api_endpoint_output)
pulumi.export("capturesBucketId", captures_bucket.id)
pulumi.export("dbEndpointAddress", postgres_instance.address)
