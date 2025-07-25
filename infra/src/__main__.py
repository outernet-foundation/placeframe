import json

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from pulumi import Config

# from components import vpc
from components.cloudbeaver import create_cloudbeaver
from components.database import create_database
from components.gateway import create_gateway
from components.lambdas import create_lambda
from components.storage import create_storage
from util import create_zero_trust_security_group

# Stack config (region comes from pulumi config aws:region)
config = Config()

# oidc_provider = aws.iam.OpenIdConnectProvider(
#     "github-oidc-provider", url="https://token.actions.githubusercontent.com", client_id_lists=["sts.amazonaws.com"]
# )

# trust_policy = pulumi.Output.all(oidc_provider.arn).apply(
#     lambda arn: json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [
#             {
#                 "Effect": "Allow",
#                 "Principal": {"Federated": arn[0]},
#                 "Action": "sts:AssumeRoleWithWebIdentity",
#                 "Condition": {
#                     "StringEquals": {f"{oidc_provider.url}:aud": "sts.amazonaws.com"},
#                     "StringLike": {
#                         f"{oidc_provider.url}:sub": [
#                             "repo:outernet-foundation/plerion:refs/heads/main",
#                             "repo:outernet-foundation/plerion:refs/heads/env/*",
#                         ]
#                     },
#                 },
#             }
#         ],
#     })
# )

# ci_role = aws.iam.Role("ci-role", assume_role_policy=trust_policy)

# aws.iam.RolePolicyAttachment(
#     "ci-role-ecr", role=ci_role.name, policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
# )

# aws.iam.RolePolicyAttachment(
#     "ci-role-ecs", role=ci_role.name, policy_arn="arn:aws:iam::aws:policy/AmazonECS_FullAccess"
# )

# aws.iam.RolePolicyAttachment(
#     "ci-role-pulumi", role=ci_role.name, policy_arn="arn:aws:iam::aws:policy/AdministratorAccess"
# )

dockerhub_secret = aws.secretsmanager.Secret(
    "dockerhub-secret",
    name="ecr-pullthroughcache/dockerhub-2",
    description="Credentials for pulling private or rate‐limited Docker Hub images",
)

# 1b. Store your username + token
dockerhub_secret_version = aws.secretsmanager.SecretVersion(
    "dockerhub-secret-version",
    secret_id=dockerhub_secret.id,
    secret_string=pulumi.Output.all(
        config.require("dockerhub-username"), config.require_secret("dockerhub-password")
    ).apply(lambda args: json.dumps({"username": args[0], "accessToken": args[1]})),
)

aws.ecr.PullThroughCacheRule(
    "dockerhub-pull-through-cache-rule",
    ecr_repository_prefix="dockerhub",
    upstream_registry_url="registry-1.docker.io",
    credential_arn=dockerhub_secret.arn,
)


def create_vpc_interface_endpoint(vpc: awsx.ec2.Vpc, name: str) -> aws.ec2.SecurityGroup:
    sanitized_name = name.replace(".", "-")
    security_group = create_zero_trust_security_group(f"{sanitized_name}-endpoint", vpc.vpc_id)
    aws.ec2.VpcEndpoint(
        f"{sanitized_name}-endpoint",
        vpc_id=vpc.vpc_id,
        service_name=f"com.amazonaws.{aws.config.region}.{name}",
        vpc_endpoint_type="Interface",
        subnet_ids=vpc.private_subnet_ids,
        security_group_ids=[security_group.id],
        private_dns_enabled=True,
    )
    return security_group


vpc = awsx.ec2.Vpc("main-vpc", nat_gateways={"strategy": awsx.ec2.NatGatewayStrategy.NONE}, enable_dns_hostnames=True)
ecr_api_security_group = create_vpc_interface_endpoint(vpc, "ecr.api")
ecr_dkr_security_group = create_vpc_interface_endpoint(vpc, "ecr.dkr")
secrets_manager_security_group = create_vpc_interface_endpoint(vpc, "secretsmanager")
logs_security_group = create_vpc_interface_endpoint(vpc, "logs")

# Create a VPC endpoint for S3 (gateway type rather than interface type, no security group)
s3_endpoint = aws.ec2.VpcEndpoint(
    "s3-gateway-endpoint",
    vpc_id=vpc.vpc_id,
    service_name=f"com.amazonaws.{aws.config.region}.s3",
    vpc_endpoint_type="Gateway",
    route_table_ids=vpc.private_subnet_ids.apply(
        lambda ids: [aws.ec2.get_route_table_output(subnet_id=subnet_id).id for subnet_id in ids]
    ),
)

lambda_security_group = create_zero_trust_security_group("lambda", vpc.vpc_id)
cloudbeaver_security_group = create_zero_trust_security_group("cloudbeaver", vpc.vpc_id)
postgres_security_group = create_zero_trust_security_group("postgres", vpc.vpc_id)

# 1. S3 bucket (captures)
captures_bucket = create_storage(config)

# 2. Postgres database
postgres_instance, connection_string = create_database(config, postgres_security_group, vpc.private_subnet_ids)

cluster = aws.ecs.Cluster("cluster")

create_cloudbeaver(
    config,
    vpc=vpc,
    cluster=cluster,
    cloudbeaver_security_group=cloudbeaver_security_group,
    ecr_api_security_group=ecr_api_security_group,
    ecr_dkr_security_group=ecr_dkr_security_group,
    secrets_manager_security_group=secrets_manager_security_group,
    logs_security_group=logs_security_group,
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
    logs_security_group=logs_security_group,
    s3_endpoint=s3_endpoint,
)

# 4. API Gateway → Lambda proxy
api_endpoint_output = create_gateway(api_lambda)

# 5. Stack outputs
pulumi.export("apiUrl", api_endpoint_output)
pulumi.export("capturesBucketId", captures_bucket.id)
pulumi.export("dbEndpointAddress", postgres_instance.address)
