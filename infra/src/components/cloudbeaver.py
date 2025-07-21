import json

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from pulumi import Config
from pulumi_awsx.ecs import FargateService


def create_cloudbeaver(
    config: Config,
    vpc: awsx.ec2.Vpc,
    cluster: aws.ecs.Cluster,
    security_group: aws.ec2.SecurityGroup,
    db: aws.rds.Instance,
) -> None:
    # Create Secrets Manager secret for Postgres password
    postgres_secret = aws.secretsmanager.Secret("postgres-secret")
    aws.secretsmanager.SecretVersion(
        "postgres-secret-version",
        secret_id=postgres_secret.id,
        secret_string=config.require_secret("postgres-password"),
    )

    # Create Secrets Manager secret for CloudBeaver admin password
    cloudbeaver_secret = aws.secretsmanager.Secret("cloudbeaver-secret")
    aws.secretsmanager.SecretVersion(
        "cloudbeaver-secret-version",
        secret_id=cloudbeaver_secret.id,
        secret_string=config.require_secret("cloudbeaver-password"),
    )

    # Create an EFS file system for CloudBeaver
    efs = aws.efs.FileSystem("cloudbeaver-efs")

    # Configure EFS security group to allow ingress from CloudBeaver
    efs_security_group = aws.ec2.SecurityGroup(
        "cloudbeaver-efs-sg",
        vpc_id=vpc.vpc_id,
        ingress=[
            {
                "protocol": "tcp",
                "from_port": 2049,
                "to_port": 2049,
                "security_groups": [security_group.id],
            }
        ],
    )

    # Create mount targets for the EFS in each private subnet of our VPC, so CloudBeaver can access it
    vpc.private_subnet_ids.apply(
        lambda subnet_ids: [
            aws.efs.MountTarget(
                f"efs-mount-{i}",
                file_system_id=efs.id,
                subnet_id=sid,
                security_groups=[efs_security_group.id],
            )
            for i, sid in enumerate(subnet_ids)
        ]
    )

    # Create a load balancer for CloudBeaver
    load_balancer = awsx.lb.ApplicationLoadBalancer("cloudbeaver-lb")

    config_json = json.dumps(
        {
            "connections": {
                "postgres": {
                    "provider": "postgresql",
                    "configuration": {
                        "host": "${POSTGRES_HOST}",
                        "database": "postgres",
                        "user": "${POSTGRES_USER}",
                        "password": "${POSTGRES_PASSWORD}",
                    },
                }
            }
        }
    )

    # Create the CloudBeaver ECS service
    FargateService(
        "cloudbeaver-service",
        cluster=cluster.arn,
        network_configuration={
            "subnets": vpc.private_subnet_ids,
            "security_groups": [security_group.id],
        },
        desired_count=1,
        task_definition_args={
            "volumes": [
                {"name": "efs", "efs_volume_configuration": {"file_system_id": efs.id}},
            ],
            "containers": {
                "cloudbeaver-init": {
                    "name": "cloudbeaver-init",
                    "image": "alpine:latest",
                    "essential": False,
                    "command": [
                        "sh",
                        "-c",
                        f"mkdir -p /opt/cloudbeaver/conf && cat > /opt/cloudbeaver/conf/initial-data-sources.conf << 'EOF'\n{config_json}\nEOF",
                    ],
                    "mount_points": [
                        {"source_volume": "efs", "container_path": "/opt/cloudbeaver"}
                    ],
                    "environment": [
                        {
                            "name": "POSTGRES_HOST",
                            "value": db.address,
                        },
                        {
                            "name": "POSTGRES_USER",
                            "value": config.require("postgres-user"),
                        },
                    ],
                    "secrets": [
                        {
                            "name": "POSTGRES_PASSWORD",
                            "value_from": postgres_secret.arn,
                        }
                    ],
                },
                "cloudbeaver": {
                    "name": "cloudbeaver",
                    "image": "dbeaver/cloudbeaver:latest",
                    "port_mappings": [
                        {
                            "container_port": 8978,
                            "target_group": load_balancer.default_target_group,
                        }
                    ],
                    "mount_points": [
                        {"source_volume": "efs", "container_path": "/opt/cloudbeaver"}
                    ],
                    "environment": [
                        {
                            "name": "CB_ADMIN_NAME",
                            "value": config.require("cloudbeaver-user"),
                        }
                    ],
                    "secrets": [
                        {
                            "name": "CB_ADMIN_PASSWORD",
                            "value_from": cloudbeaver_secret.arn,
                        }
                    ],
                    "depends_on": [
                        {
                            "container_name": "cloudbeaver-init",
                            "condition": "SUCCESS",
                        }
                    ],
                },
            },
        },
    )

    pulumi.export("cloudbeaverUrl", load_balancer.load_balancer.dns_name)
