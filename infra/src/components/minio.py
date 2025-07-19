import json

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from pulumi import Config, Output
from pulumi_awsx.ecs import FargateService


def create_minio(
    config: Config,
    vpc: awsx.ec2.Vpc,
    s3_bucket: aws.s3.Bucket,
) -> Output[str]:
    """
    Create MinIO S3 gateway service with automatic load balancer.

    Returns the URL to access MinIO.
    """

    # Create task role with S3 access for MinIO
    task_role = aws.iam.Role(
        "minio-task-role",
        assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }""",
    )

    # Grant S3 access to MinIO task
    aws.iam.RolePolicy(
        "minio-s3-access",
        role=task_role.id,
        policy=s3_bucket.arn.apply(
            lambda arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket",
                            ],
                            "Resource": [arn, f"{arn}/*"],
                        }
                    ],
                }
            )
        ),
    )

    # Create an Application Load Balancer
    load_balancer = awsx.lb.ApplicationLoadBalancer(
        "minio-lb", subnet_ids=vpc.public_subnet_ids
    )

    # Create target group for MinIO S3 API (port 9000)
    api_target_group = aws.lb.TargetGroup(
        "minio-api-tg",
        port=9000,
        protocol="HTTP",
        vpc_id=vpc.vpc_id,
        target_type="ip",  # Use "ip" for Fargate
        health_check={"path": "/minio/health/live"},
    )

    # Create target group for MinIO Console (port 9001)
    console_target_group = aws.lb.TargetGroup(
        "minio-console-tg",
        port=9001,
        protocol="HTTP",
        vpc_id=vpc.vpc_id,
        target_type="ip",
    )

    # Create listener for MinIO API
    aws.lb.Listener(
        "minio-api-listener",
        load_balancer_arn=load_balancer.load_balancer.arn,
        port=80,
        protocol="HTTP",
        default_actions=[
            {
                "type": "forward",
                "target_group_arn": api_target_group.arn,
            }
        ],
    )

    # Create listener for MinIO Console
    aws.lb.Listener(
        "minio-console-listener",
        load_balancer_arn=load_balancer.load_balancer.arn,
        port=9001,
        protocol="HTTP",
        default_actions=[
            {
                "type": "forward",
                "target_group_arn": console_target_group.arn,
            }
        ],
    )

    # Create an ECS cluster for MinIO
    cluster = aws.ecs.Cluster("minio-cluster")

    # MinIO Service with automatic load balancer integration
    minio = FargateService(
        "minioTool",
        cluster=cluster.arn,
        task_definition_args={
            "task_role": {"role_arn": task_role.arn},
            "container": {
                "name": "minio",
                "image": "minio/minio:latest",
                "cpu": 256,
                "memory": 512,
                "essential": True,
                "command": [
                    "server",
                    "/data",
                    "--address",
                    ":9000",
                    "--console-address",
                    ":9001",
                ],
                "environment": [
                    {
                        "name": "MINIO_ROOT_USER",
                        "value": config.require("minioAccessKey"),
                    },
                    {
                        "name": "MINIO_ROOT_PASSWORD",
                        "value": config.require_secret("minioSecretKey"),
                    },
                    {"name": "MINIO_DOMAIN", "value": "s3.amazonaws.com"},
                ],
                "port_mappings": [
                    {
                        "container_port": 9000,  # MinIO API
                        "host_port": 9000,
                        "protocol": "tcp",
                    },
                    {
                        "container_port": 9001,  # MinIO Console
                        "host_port": 9001,
                        "protocol": "tcp",
                    },
                ],
            },
        },
        network_configuration={
            "subnets": vpc.private_subnet_ids,
            "assign_public_ip": False,  # MinIO should not be publicly accessible
        },
        load_balancers=[
            {
                "target_group_arn": api_target_group.arn,
                "container_name": "minio",
                "container_port": 9000,
            },
            {
                "target_group_arn": console_target_group.arn,
                "container_name": "minio",
                "container_port": 9001,
            },
        ],
        desired_count=1,
    )

    # Get the load balancer URL
    minio_url = load_balancer.load_balancer.dns_name.apply(lambda dns: f"http://{dns}")

    # Export URLs and service info
    pulumi.export("minioServiceName", minio.service.name)
    pulumi.export("minioApiUrl", minio_url.apply(lambda url: f"{url}:9000"))
    pulumi.export("minioConsoleUrl", minio_url.apply(lambda url: f"{url}:9001"))

    return minio_url
