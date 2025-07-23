import json

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from pulumi import Config
from pulumi_awsx.ecs import FargateService

from util import ALLOW_ALL_EGRESS


def create_cloudbeaver(
    config: Config,
    vpc: awsx.ec2.Vpc,
    cluster: aws.ecs.Cluster,
    security_group: aws.ec2.SecurityGroup,
    db: aws.rds.Instance
) -> None:
    aws.ecr.Repository(
        "alpine-cache-repo",
        name="dockerhub/library/alpine",
        force_delete=config.require_bool("devMode"),
    )

    aws.ecr.Repository(
        "cloudbeaver-cache-repo", 
        name="dockerhub/dbeaver/cloudbeaver",
        force_delete=config.require_bool("devMode"),
    )

    # Get current AWS account ID and region for constructing ECR URLs
    current = aws.get_caller_identity()
    region = aws.get_region()

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
        egress=ALLOW_ALL_EGRESS,
    )

    # Create mount targets for the EFS in each private subnet of our VPC, so CloudBeaver can access it
    mount_targets = vpc.private_subnet_ids.apply(
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

    alb_sg = aws.ec2.SecurityGroup(
        "alb-sg",
        vpc_id=vpc.vpc_id,
        ingress=[
            {
                "protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "cidr_blocks": ["0.0.0.0/0"],
            }
        ],
        egress=ALLOW_ALL_EGRESS,
    )

    # Create a load balancer for CloudBeaver
    load_balancer = awsx.lb.ApplicationLoadBalancer(
        "cloudbeaver-lb-2",
        security_groups=[alb_sg.id],
        subnet_ids=vpc.public_subnet_ids,
        default_target_group_port=8978,
    )

    service_sg = aws.ec2.SecurityGroup(
        "service-sg",
        vpc_id=vpc.vpc_id,
        description="Allow ALB to talk to CloudBeaver containers",
        ingress=[
            {
                "protocol": "tcp",
                "from_port": 8978,
                "to_port": 8978,
                "security_groups": [alb_sg.id],  # only ALB can connect
            }
        ],
        egress=ALLOW_ALL_EGRESS,
    )
    
    # Create the CloudBeaver ECS service
    FargateService(
        "cloudbeaver-service",
        cluster=cluster.arn,
        network_configuration={
            "subnets": vpc.private_subnet_ids,
            "security_groups": [
                security_group.id,
                service_sg.id,
            ],
        },
        desired_count=1,
        opts=pulumi.ResourceOptions(depends_on=mount_targets),
        task_definition_args={
            "execution_role": {
                "args": {
                    "inline_policies": [
                        {
                            "policy": pulumi.Output.all(
                                postgres_secret.arn, cloudbeaver_secret.arn
                            ).apply(
                                lambda arns: json.dumps(
                                    {
                                        "Version": "2012-10-17",
                                        "Statement": [
                                            {
                                                "Effect": "Allow",
                                                "Action": "secretsmanager:GetSecretValue",
                                                "Resource": arns,
                                            },
                                            # Add permission required for ECR pull-through cache
                                            {
                                                "Effect": "Allow",
                                                "Action": "ecr:BatchImportUpstreamImage",
                                                "Resource": "*"
                                            }
                                        ],
                                    }
                                )
                            )
                        }
                    ]
                }
            },
            "volumes": [
                {
                    "name": "efs",
                    "efs_volume_configuration": {
                        "file_system_id": efs.id,
                        "transit_encryption": "ENABLED",
                    },
                },
            ],
            "containers": {
                "cloudbeaver-init": {
                    "name": "cloudbeaver-init",
                    "image": pulumi.Output.all(current.account_id, region.name).apply(
                        lambda args: f"{args[0]}.dkr.ecr.{args[1]}.amazonaws.com/dockerhub/library/alpine:latest"
                    ),
                    "essential": False,
                    "command": [
                        "sh",
                        "-c",
                        "\n".join(
                            [
                                "mkdir -p /opt/cloudbeaver/workspace/GlobalConfiguration/.dbeaver",
                                "cat <<EOF > /opt/cloudbeaver/workspace/GlobalConfiguration/.dbeaver/data-sources.json",
                                json.dumps(
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
                                ),
                                "EOF",
                            ]
                        ),
                    ],
                    "mount_points": [
                        {
                            "source_volume": "efs",
                            "container_path": "/opt/cloudbeaver/workspace",
                        }
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
                   "image": pulumi.Output.all(current.account_id, region.name).apply(
                        lambda args: f"{args[0]}.dkr.ecr.{args[1]}.amazonaws.com/dockerhub/dbeaver/cloudbeaver:latest"
                    ),
                    "port_mappings": [
                        {
                            "container_port": 8978,
                            "host_port": 8978,
                            "target_group": load_balancer.default_target_group,
                        }
                    ],
                    "mount_points": [
                        {
                            "source_volume": "efs",
                            "container_path": "/opt/cloudbeaver/workspace",
                        }
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

    pulumi.export(
        "cloudbeaverUrl",
        load_balancer.load_balancer.dns_name.apply(
            lambda dns_name: f"http://{dns_name}"
        ),
    )
