from pulumi import Config, StackReference
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_images_output
from pulumi_aws.ecs import Cluster
from pulumi_aws.lb import Listener, LoadBalancer, TargetGroup
from pulumi_aws.route53 import Record
from pulumi_aws.s3 import Bucket
from pulumi_awsx.ecs import FargateService

from components.ecr import locked_image_ref
from components.log import log_configuration
from components.role import Role, ecs_assume_role_policy
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_api(
    config: Config,
    core_stack: StackReference,
    vpc: Vpc,
    cluster: Cluster,
    s3_bucket: Bucket,
    postgres_security_group: SecurityGroup,
    postgres_dsn_secret: Secret,
    prepare_deploy_role: Role,
    deploy_role: Role,
) -> None:
    # Log groups
    api_log_group = LogGroup("api-log-group", name="/ecs/api", retention_in_days=7)

    # Image repos
    api_image_repo = Repository("api-repo", force_delete=config.require_bool("devMode"))

    # Allow image repo actions role to push to this image repo
    prepare_deploy_role.allow_image_repo_actions([api_image_repo])

    # Security groups
    api_security_group = SecurityGroup(
        "api-security-group",
        vpc=vpc,
        vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
        rules=[{"to_security_group": postgres_security_group, "ports": [5432]}],
    )

    load_balancer_security_group = SecurityGroup(
        "api-load-balancer-security-group",
        vpc=vpc,
        rules=[
            {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
            {"to_security_group": api_security_group, "ports": [8000]},
        ],
    )

    # Load balancer
    load_balancer = LoadBalancer(
        "api-lb", security_groups=[load_balancer_security_group.id], subnets=vpc.public_subnet_ids
    )

    target_group = TargetGroup(
        "api-lb-tg",
        port=8000,
        protocol="HTTP",
        target_type="ip",
        vpc_id=load_balancer.vpc_id,
        deregistration_delay=60,
        health_check={
            "path": "/",
            "protocol": "HTTP",
            "interval": 15,
            "healthy_threshold": 2,
            "unhealthy_threshold": 10,
        },
    )

    Listener(
        "api-https-listener",
        load_balancer_arn=load_balancer.arn,
        port=443,
        protocol="HTTPS",
        certificate_arn=core_stack.require_output("certificate-arn"),
        default_actions=[{"type": "forward", "target_group_arn": target_group.arn}],
    )

    Listener(
        "api-http-listener",
        load_balancer_arn=load_balancer.arn,
        port=80,
        protocol="HTTP",
        default_actions=[
            {"type": "redirect", "redirect": {"protocol": "HTTPS", "port": "443", "status_code": "HTTP_301"}}
        ],
    )

    # DNS Records
    domain = core_stack.require_output("zone-name").apply(lambda zone_name: f"api.{zone_name}")
    Record(
        "api-domain-record",
        zone_id=core_stack.require_output("zone-id"),
        name=domain,
        type="A",
        aliases=[{"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}],
    )

    # Execution role
    execution_role = Role("api-execution-role", assume_role_policy=ecs_assume_role_policy())
    execution_role.allow_secret_get([postgres_dsn_secret])

    # Task role
    task_role = Role("api-task-role", assume_role_policy=ecs_assume_role_policy())
    task_role.allow_s3(s3_bucket)

    service = FargateService(
        "api-service",
        name="api-service",
        cluster=cluster.arn,
        desired_count=get_images_output(repository_name=api_image_repo.name).apply(
            lambda output: 1 if output.image_ids else 0
        ),  # Set desired count to 0 if the image repository is empty
        network_configuration={"subnets": vpc.private_subnet_ids, "security_groups": [api_security_group.id]},
        task_definition_args={
            "execution_role": {"role_arn": execution_role.arn},
            "task_role": {"role_arn": task_role.arn},
            "containers": {
                "api": {
                    "name": "api",
                    "image": locked_image_ref(api_image_repo),
                    "log_configuration": log_configuration(api_log_group),
                    "port_mappings": [{"container_port": 8000, "host_port": 8000, "target_group": target_group}],
                    "secrets": [{"name": "POSTGRES_DSN", "value_from": postgres_dsn_secret.arn}],
                    "environment": [{"name": "_POSTGRES_DSN_VERSION", "value": postgres_dsn_secret.version_id}],
                }
            },
        },
    )

    # Allow the deployment role to deploy this service
    deploy_role.allow_service_deployment([service.service.arn], [execution_role.arn])
