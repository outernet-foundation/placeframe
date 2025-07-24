import json
from pathlib import Path

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_docker as docker  # top-level module (we'll pass dicts for inputs)
from pulumi import Config, Output
from pulumi_awsx.ecs import FargateService

from util import ALLOW_ALL_EGRESS


def create_cloudbeaver(
    config: Config,
    vpc: awsx.ec2.Vpc,
    cluster: aws.ecs.Cluster,
    security_group: aws.ec2.SecurityGroup,
    db: aws.rds.Instance,
) -> None:
    # Allow internet http ingress to load balancer
    load_balancer_security_group = aws.ec2.SecurityGroup(
        "alb-sg",
        vpc_id=vpc.vpc_id,
        ingress=[{"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]}],
        egress=ALLOW_ALL_EGRESS,
    )
    
    # Allow load balancer ingress to CloudBeaver
    aws.ec2.SecurityGroupRule(
        "cloudbeaver-ingress-rule",
        type="ingress",
        from_port=8978,
        to_port=8978,
        protocol="tcp",
        security_group_id=security_group.id,
        source_security_group_id=load_balancer_security_group.id,
    )

    # Allow CloudBeaver ingress to EFS
    efs_security_group = aws.ec2.SecurityGroup(
        "cloudbeaver-efs-sg",
        vpc_id=vpc.vpc_id,
        ingress=[{"protocol": "tcp", "from_port": 2049, "to_port": 2049, "security_groups": [security_group.id]}],
        egress=ALLOW_ALL_EGRESS,
    )

    # Create secret for postgres password
    postgres_secret = aws.secretsmanager.Secret("postgres-secret")
    aws.secretsmanager.SecretVersion(
        "postgres-secret-version",
        secret_id=postgres_secret.id,
        secret_string=config.require_secret("postgres-password"),
    )

    # Create secret for CloudBeaver admin password
    cloudbeaver_secret = aws.secretsmanager.Secret("cloudbeaver-secret")
    aws.secretsmanager.SecretVersion(
        "cloudbeaver-secret-version",
        secret_id=cloudbeaver_secret.id,
        secret_string=config.require_secret("cloudbeaver-password"),
    )

    # Create repos for image pull-through cache
    aws.ecr.Repository(
        "alpine-cache-repo", name="dockerhub/library/alpine", force_delete=config.require_bool("devMode")
    )
    aws.ecr.Repository(
        "cloudbeaver-cache-repo", name="dockerhub/dbeaver/cloudbeaver", force_delete=config.require_bool("devMode")
    )

    # Create a policy allowing CloudBeaver to access secrets and use the pull-through cache
    policy = pulumi.Output.all(postgres_secret.arn, cloudbeaver_secret.arn).apply(
        lambda arns: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "secretsmanager:GetSecretValue",
                    "Resource": arns,
                },
                {"Effect": "Allow", "Action": "ecr:BatchImportUpstreamImage", "Resource": "*"},
            ],
        })
    )

    # Create a Docker image for CloudBeaver initialization
    repo = aws.ecr.Repository("cloudbeaver-init-repo", force_delete=config.require_bool("devMode"))
    dockerfile = Path(config.require("cloudbeaver-init-dockerfile")).resolve()
    creds = aws.ecr.get_authorization_token()
    image = docker.Image(
        "cloudbeaver-init-image",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=Output.concat(repo.repository_url, ":", "latest"),
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    # Create EFS for CloudBeaver workspace
    efs = aws.efs.FileSystem("cloudbeaver-efs")

    # Create mount targets for the EFS in each private subnet of our VPC
    mount_targets = vpc.private_subnet_ids.apply(
        lambda subnet_ids: [
            aws.efs.MountTarget(
                f"efs-mount-{i}", file_system_id=efs.id, subnet_id=sid, security_groups=[efs_security_group.id]
            )
            for i, sid in enumerate(subnet_ids)
        ]
    )

    # Create load balancer
    load_balancer = awsx.lb.ApplicationLoadBalancer(
        "cloudbeaver-lb",
        security_groups=[load_balancer_security_group.id],
        subnet_ids=vpc.public_subnet_ids,
        default_target_group=awsx.lb.TargetGroupArgs(
            port=8978,
            # Wait up to 60 s for in‑flight requests to drain before deregistering a target
            deregistration_delay=60,
            health_check=aws.lb.TargetGroupHealthCheckArgs(
                path="/health",
                protocol="HTTP",
                matcher="200-299", # Paranoia
                interval=30,
                timeout=5,
                healthy_threshold=3, # Down from default 5
                unhealthy_threshold=2,
            ),
        ),
    )

    # Create log groups
    aws.cloudwatch.LogGroup("cloudbeaver-log-group", name="/ecs/cloudbeaver", retention_in_days=7)
    aws.cloudwatch.LogGroup("cloudbeaver-init-log-group", name="/ecs/cloudbeaver-init", retention_in_days=7)
    
    # Precompute some Input strings
    db_url = pulumi.Output.all(db.address, db.port, db.name).apply(lambda args: f"jdbc:postgresql://{args[0]}:{args[1]}/{args[2]}")
    cloudbeaver_url = pulumi.Output.all(load_balancer.load_balancer.dns_name).apply(lambda dns_name: f"http://{dns_name}")
    cloudbeaver_image = pulumi.Output.all(aws.get_caller_identity().account_id, aws.get_region().name).apply(
        lambda args: f"{args[0]}.dkr.ecr.{args[1]}.amazonaws.com/dockerhub/dbeaver/cloudbeaver:latest"
    )

    # Create Fargate service
    FargateService(
        "cloudbeaver-service",
        cluster=cluster.arn,
        desired_count=1,
        opts=pulumi.ResourceOptions(depends_on=mount_targets),
        network_configuration={
            "subnets": vpc.private_subnet_ids,
            "security_groups": [security_group.id],
        },
        task_definition_args={
            "execution_role": {
                "args": {
                    "inline_policies": [
                        {
                            "policy": policy
                        }
                    ]
                }
            },
            "volumes": [
                {"name": "efs", "efs_volume_configuration": {"file_system_id": efs.id, "transit_encryption": "ENABLED"}}
            ],
            "containers": {
                "cloudbeaver-init": {
                    "name": "cloudbeaver-init",
                    "image": image.repo_digest,
                    "essential": False,
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/cloudbeaver-init",
                            "awslogs-region": aws.get_region().name,
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
                    "image": cloudbeaver_image,
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/cloudbeaver",
                            "awslogs-region": aws.get_region().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "port_mappings": [
                        {"container_port": 8978, "host_port": 8978, "target_group": load_balancer.default_target_group}
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
    pulumi.export("cloudbeaverUrl", load_balancer.load_balancer.dns_name.apply(lambda dns_name: f"http://{dns_name}"))

