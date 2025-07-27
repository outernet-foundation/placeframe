import json
from pathlib import Path
from typing import Sequence

import pulumi_docker as docker
from pulumi import Config, Output, ResourceOptions, export
from pulumi_aws import get_caller_identity, get_region
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ec2 import VpcEndpoint
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.ecs import Cluster
from pulumi_aws.efs import FileSystem, MountTarget
from pulumi_aws.lb import Listener, LoadBalancer, TargetGroup
from pulumi_aws.rds import Instance
from pulumi_awsx.ec2 import Vpc
from pulumi_awsx.ecs import FargateService

from components.secret import Secret
from components.security_group import SecurityGroup


def create_cloudbeaver(
    config: Config,
    vpc: Vpc,
    private_subnet_ids: Output[Sequence[str]],
    public_subnet_ids: Output[Sequence[str]],
    cluster: Cluster,
    cloudbeaver_security_group: SecurityGroup,
    ecr_api_security_group: SecurityGroup,
    ecr_dkr_security_group: SecurityGroup,
    secrets_manager_security_group: SecurityGroup,
    logs_security_group: SecurityGroup,
    sts_security_group: SecurityGroup,
    postgres_security_group: SecurityGroup,
    s3_endpoint: VpcEndpoint,
    db: Instance,
) -> None:
    load_balancer_security_group = SecurityGroup("load-balancer-security-group", vpc_id=vpc.vpc_id)
    efs_security_group = SecurityGroup("cloudbeaver-efs-security-group", vpc_id=vpc.vpc_id)

    # Allow http ingress to the load balancer
    load_balancer_security_group.allow_ingress_cidr(cidr="0.0.0.0/0", cidr_name="vpc-cidr", ports=[80], protocol="tcp")

    # Allow egress to the VPC CIDR for DNS resolution
    cloudbeaver_security_group.allow_egress_cidr(cidr_name="vpc-cidr", cidr=vpc.vpc.cidr_block, ports=[53])
    cloudbeaver_security_group.allow_egress_cidr(
        cidr_name="vpc-cidr", cidr=vpc.vpc.cidr_block, ports=[53], protocol="udp"
    )

    # Allow load balancer to access CloudBeaver
    cloudbeaver_security_group.allow_ingress(from_security_group=load_balancer_security_group, ports=[8978])

    # For each VPC endpoint, allow Cloudbeaver to access it
    for vpc_endpoint_security_group in [
        ecr_api_security_group,
        ecr_dkr_security_group,
        secrets_manager_security_group,
        logs_security_group,
        sts_security_group,
    ]:
        vpc_endpoint_security_group.allow_ingress(from_security_group=cloudbeaver_security_group, ports=[443])

    # Allow Cloudbeaver egress to S3 (required for pulling images because ecr uses s3 for image layer blobs)
    cloudbeaver_security_group.allow_egress_prefix_list(
        prefix_list_name="s3", prefix_list_id=s3_endpoint.prefix_list_id, ports=[443]
    )

    # Allow CloudBeaver to access Postgres
    postgres_security_group.allow_ingress(from_security_group=cloudbeaver_security_group, ports=[5432])

    # Allow CloudBeaver to access EFS
    efs_security_group.allow_ingress(from_security_group=cloudbeaver_security_group, ports=[2049])

    # Create secrets for Postgres and CloudBeaver passwords
    postgres_secret = Secret("postgres-secret", secret_string=config.require_secret("postgres-password"))
    cloudbeaver_secret = Secret("cloudbeaver-secret", secret_string=config.require_secret("cloudbeaver-password"))

    # Create repos for image pull-through cache
    Repository("alpine-cache-repo", name="dockerhub/library/alpine", force_delete=config.require_bool("devMode"))
    Repository(
        "cloudbeaver-cache-repo", name="dockerhub/dbeaver/cloudbeaver", force_delete=config.require_bool("devMode")
    )

    # Create a policy allowing CloudBeaver to access secrets and use the pull-through cache
    policy = Output.all(postgres_secret.arn, cloudbeaver_secret.arn).apply(
        lambda arns: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": arns},
                {"Effect": "Allow", "Action": "ecr:BatchImportUpstreamImage", "Resource": "*"},
            ],
        })
    )

    # Create a Docker image for CloudBeaver initialization
    init_image_repo = Repository("cloudbeaver-init-repo", force_delete=config.require_bool("devMode"))
    dockerfile = Path(config.require("cloudbeaver-init-dockerfile")).resolve()
    creds = get_authorization_token()
    init_image = docker.Image(
        "cloudbeaver-init-image",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=Output.concat(init_image_repo.repository_url, ":", "latest"),
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    # Create EFS for CloudBeaver workspace
    efs = FileSystem("cloudbeaver-efs")

    # Create mount targets for the EFS in each private subnet of our VPC
    mount_targets = private_subnet_ids.apply(
        lambda subnet_ids: [
            MountTarget(f"efs-mount-{i}", file_system_id=efs.id, subnet_id=sid, security_groups=[efs_security_group.id])
            for i, sid in enumerate(subnet_ids)
        ]
    )

    # 1) Create the ALB itself
    load_balancer = LoadBalancer(
        "cloudbeaver-lb", security_groups=[load_balancer_security_group.id], subnets=public_subnet_ids
    )

    # 2) Create the Target Group
    load_balancer_target_group = TargetGroup(
        "cloudbeaver-lb-tg",
        port=8978,
        protocol="HTTP",
        target_type="ip",
        vpc_id=load_balancer.vpc_id,
        deregistration_delay=60,  # Wait 60s before deregistering unhealthy instances (down from default of 300, for faster rotation since we only have one instance)
        health_check={
            "path": "/",
            "protocol": "HTTP",
            "interval": 15,  # Check every 15 seconds (down from default of 30)
            "healthy_threshold": 2,  # We are healthy after 30 seconds (down from default of 5*30, for faster deployments)
            "unhealthy_threshold": 10,  # We are unhealthy after 150 seconds (up from default of 3*30, because CloudBeaver can take a while to start up)
        },
    )

    # 3) Create the Listener, forwarding to our TG
    Listener(
        "cloudbeaver-lb-listener",
        load_balancer_arn=load_balancer.arn,
        port=80,
        protocol="HTTP",
        default_actions=[{"type": "forward", "target_group_arn": load_balancer_target_group.arn}],
    )

    # Create log groups
    LogGroup("cloudbeaver-log-group", name="/ecs/cloudbeaver", retention_in_days=7)
    LogGroup("cloudbeaver-init-log-group", name="/ecs/cloudbeaver-init", retention_in_days=7)

    # Precompute some Input strings
    db_url = Output.all(db.address, db.port).apply(lambda args: f"jdbc:postgresql://{args[0]}:{args[1]}/postgres")
    cloudbeaver_url = load_balancer.dns_name.apply(lambda dns_name: f"http://{dns_name}")

    # Create Fargate service
    FargateService(
        "cloudbeaver-service",
        cluster=cluster.arn,
        desired_count=1,
        opts=ResourceOptions(depends_on=mount_targets),
        network_configuration={"subnets": private_subnet_ids, "security_groups": [cloudbeaver_security_group.id]},
        task_definition_args={
            "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
            "volumes": [
                {"name": "efs", "efs_volume_configuration": {"file_system_id": efs.id, "transit_encryption": "ENABLED"}}
            ],
            "containers": {
                "cloudbeaver-init": {
                    "name": "cloudbeaver-init",
                    "image": init_image.repo_digest,
                    "essential": False,
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/cloudbeaver-init",
                            "awslogs-region": get_region().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "mount_points": [{"source_volume": "efs", "container_path": "/opt/cloudbeaver/workspace"}],
                    "environment": [
                        {"name": "POSTGRES_HOST", "value": db.address},
                        {"name": "POSTGRES_PORT", "value": "5432"},
                        {"name": "POSTGRES_DB", "value": "postgres"},
                        {"name": "POSTGRES_USER", "value": config.require("postgres-user")},
                    ],
                    "secrets": [{"name": "POSTGRES_PASSWORD", "value_from": postgres_secret.arn}],
                },
                "cloudbeaver": {
                    "name": "cloudbeaver",
                    "image": f"{get_caller_identity().account_id}.dkr.ecr.{get_region().name}.amazonaws.com/dockerhub/dbeaver/cloudbeaver:latest",
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/cloudbeaver",
                            "awslogs-region": get_region().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "port_mappings": [
                        {"container_port": 8978, "host_port": 8978, "target_group": load_balancer_target_group}
                    ],
                    "mount_points": [{"source_volume": "efs", "container_path": "/opt/cloudbeaver/workspace"}],
                    "environment": [
                        {"name": "CB_SERVER_NAME", "value": "CloudBeaver"},
                        {"name": "CB_SERVER_URL", "value": cloudbeaver_url},
                        {"name": "CB_ADMIN_NAME", "value": config.require("cloudbeaver-user")},
                        {"name": "CLOUDBEAVER_DB_DRIVER", "value": "postgres-jdbc"},
                        {"name": "CLOUDBEAVER_DB_URL", "value": db_url},
                        {"name": "CLOUDBEAVER_DB_USER", "value": config.require("postgres-user")},
                        {"name": "CLOUDBEAVER_DB_SCHEMA", "value": "cloudbeaver"},
                    ],
                    "secrets": [
                        {"name": "CLOUDBEAVER_DB_PASSWORD", "value_from": postgres_secret.arn},
                        {"name": "CB_ADMIN_PASSWORD", "value_from": cloudbeaver_secret.arn},
                    ],
                    "depends_on": [{"container_name": "cloudbeaver-init", "condition": "SUCCESS"}],
                },
            },
        },
    )

    # Export load balancer URL
    export("cloudbeaverUrl", cloudbeaver_url)
