import json
from pathlib import Path

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_docker as docker  # top-level module (we'll pass dicts for inputs)
from pulumi import Config, Output
from pulumi.resource import CustomTimeouts
from pulumi_awsx.ecs import FargateService

from util import add_reciprocal_security_group_rules


def create_cloudbeaver(
    config: Config,
    vpc: awsx.ec2.Vpc,
    cluster: aws.ecs.Cluster,
    cloudbeaver_security_group: aws.ec2.SecurityGroup,
    ecr_api_security_group: aws.ec2.SecurityGroup,
    ecr_dkr_security_group: aws.ec2.SecurityGroup,
    secrets_manager_security_group: aws.ec2.SecurityGroup,
    logs_security_group: aws.ec2.SecurityGroup,
    postgres_security_group: aws.ec2.SecurityGroup,
    db: aws.rds.Instance,
) -> None:
    load_balancer_security_group = aws.ec2.SecurityGroup(
        "load-balancer-security-group",
        vpc_id=vpc.vpc_id,
        # Allow load balancer ingress from the internet
        ingress=[{"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]}],
        egress=[],
    )

    efs_security_group = aws.ec2.SecurityGroup(
        "cloudbeaver-efs-security-group", vpc_id=vpc.vpc_id, ingress=[], egress=[]
    )

    # Allow Cloudbeaver ingress from the load balancer and allow load balancer egress to CloudBeaver
    add_reciprocal_security_group_rules(
        ingress_security_group=cloudbeaver_security_group,
        egress_security_group=load_balancer_security_group,
        ports=[8978],
    )

    # For each vpc endpoint, allow endpoint ingress from Cloudbeaver and allow CloudBeaver egress to endpoint
    for vpc_endpoint_security_group in [
        ecr_api_security_group,
        ecr_dkr_security_group,
        secrets_manager_security_group,
        logs_security_group,
    ]:
        add_reciprocal_security_group_rules(
            ingress_security_group=vpc_endpoint_security_group,
            egress_security_group=cloudbeaver_security_group,
            ports=[443],
        )

    # Allow Postgres ingress from CloudBeaver and allow CloudBeaver egress to Postgres
    add_reciprocal_security_group_rules(
        ingress_security_group=postgres_security_group, egress_security_group=cloudbeaver_security_group, ports=[5432]
    )

    # Allow EFS ingress from CloudBeaver and allow CloudBeaver egress to EFS
    add_reciprocal_security_group_rules(
        ingress_security_group=efs_security_group,
        egress_security_group=cloudbeaver_security_group,
        ports=[2049],
        protocol="tcp",
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
                {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": arns},
                {"Effect": "Allow", "Action": "ecr:BatchImportUpstreamImage", "Resource": "*"},
            ],
        })
    )

    # Create a Docker image for CloudBeaver initialization
    init_image_repo = aws.ecr.Repository("cloudbeaver-init-repo", force_delete=config.require_bool("devMode"))
    dockerfile = Path(config.require("cloudbeaver-init-dockerfile")).resolve()
    creds = aws.ecr.get_authorization_token()
    docker.Image(
        "cloudbeaver-init-image",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=Output.concat(init_image_repo.repository_url, ":", "latest"),
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
            deregistration_delay=60,  # Wait 60s before deregistering unhealthy instances (down from default of 300, for faster rotation since we only have one instance)
            health_check=aws.lb.TargetGroupHealthCheckArgs(
                interval=15,  # Check every 15 seconds (down from default of 30)
                healthy_threshold=2,  # We are healthy after 30 seconds (down from default of 5*30, for faster deployments)
                unhealthy_threshold=10,  # We are unhealthy after 150 seconds (up from default of 3*30, because CloudBeaver can take a while to start up)
            ),
        ),
    )

    # Create log groups
    aws.cloudwatch.LogGroup("cloudbeaver-log-group", name="/ecs/cloudbeaver", retention_in_days=7)
    aws.cloudwatch.LogGroup("cloudbeaver-init-log-group", name="/ecs/cloudbeaver-init", retention_in_days=7)

    # Precompute some Input strings
    db_url = pulumi.Output.all(db.address, db.port).apply(
        lambda args: f"jdbc:postgresql://{args[0]}:{args[1]}/postgres"
    )
    cloudbeaver_url = load_balancer.load_balancer.dns_name.apply(lambda dns_name: f"http://{dns_name}")

    # Create Fargate service
    FargateService(
        "cloudbeaver-service",
        cluster=cluster.arn,
        desired_count=1,
        opts=pulumi.ResourceOptions(depends_on=mount_targets, custom_timeouts=CustomTimeouts(create="5m")),
        network_configuration={"subnets": vpc.private_subnet_ids, "security_groups": [cloudbeaver_security_group.id]},
        task_definition_args={
            "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
            "volumes": [
                {"name": "efs", "efs_volume_configuration": {"file_system_id": efs.id, "transit_encryption": "ENABLED"}}
            ],
            "containers": {
                "cloudbeaver-init": {
                    "name": "cloudbeaver-init",
                    "image": init_image_repo.repository_url.apply(lambda u: f"{u}:latest"),
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
                    "image": f"{aws.get_caller_identity().account_id}.dkr.ecr.{aws.get_region().name}.amazonaws.com/dockerhub/dbeaver/cloudbeaver:latest",
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
    pulumi.export("cloudbeaverUrl", cloudbeaver_url)
