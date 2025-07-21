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
    db_host: str,
) -> None:
    load_balancer = awsx.lb.ApplicationLoadBalancer("cloudbeaver-load-balancer")

    config_json = json.dumps(
        {
            "connections": {
                "postgres": {
                    "provider": "postgresql",
                    "configuration": {
                        "host": "${DB_HOST}",
                        "database": "postgres",
                        "user": "${DB_USER}",
                        "password": "${DB_PASSWORD}",
                    },
                }
            }
        }
    )

    FargateService(
        "cloudbeaver-service",
        cluster=cluster.arn,
        network_configuration={
            "subnets": vpc.private_subnet_ids,
            "security_groups": [security_group.id],
        },
        desired_count=1,
        task_definition_args={
            "containers": {
                "cloudbeaver-init": {
                    "name": "cloudbeaver-init",
                    "image": "alpine:latest",
                    "essential": False,
                    "command": [
                        "sh",
                        "-c",
                        f"cat > /config/data-sources.json << 'EOF'\n{config_json}\nEOF",
                    ],
                    "environment": [
                        {
                            "name": "DB_HOST",
                            "value": db_host,
                        },
                        {
                            "name": "DB_USER",
                            "value": config.require("dbUsername"),
                        },
                        {
                            "name": "DB_PASSWORD",
                            "value": config.require_secret("dbPassword"),
                        },
                    ],
                    "mount_points": [
                        {
                            "source_volume": "config_volume",
                            "container_path": "/config",
                        }
                    ],
                },
                "cloudbeaver": {
                    "name": "cloudbeaver",
                    "image": "dbeaver/cloudbeaver:latest",
                    "port_mappings": [
                        {
                            "container_port": 8978,
                            "target_group": awsx.lb.ApplicationLoadBalancer(
                                "cloudbeaver-load-balancer"
                            ).default_target_group,
                        }
                    ],
                    "environment": [
                        {
                            "name": "CB_ADMIN_NAME",
                            "value": config.require("cloudbeaverUser"),
                        },
                        {
                            "name": "CB_ADMIN_PASSWORD",
                            "value": config.require_secret("cloudbeaverPassword"),
                        },
                    ],
                    "depends_on": [
                        {
                            "container_name": "cloudbeaver-init",
                            "condition": "SUCCESS",
                        }
                    ],
                    "mount_points": [
                        {
                            "source_volume": "config_volume",
                            "container_path": "/opt/cloudbeaver/config",
                        }
                    ],
                },
            },
        },
    )

    pulumi.export("cloudbeaverUrl", load_balancer.load_balancer.dns_name)
