from pulumi import Config, Input, Output, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.lb import Listener, LoadBalancer, TargetGroup
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.log import log_configuration
from components.repository import Repository
from components.role import Role, ecs_assume_role_policy
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc

service_map: dict[str, int] = {"api": 8000, "cloudbeaver": 8978, "minio": 9000, "minioconsole": 9001}


def create_tailscale_beacon(
    config: Config,
    vpc: Vpc,
    zone_id: Input[str],
    domain: Input[str],
    certificate_arn: Input[str],
    cluster: Cluster,
    prepare_deploy_role: Role,
    deploy_role: Role,
):
    # Log groups
    tailscale_beacon_log_group = LogGroup(
        "tailscale-beacon-log-group", name="/ecs/tailscale-beacon", retention_in_days=7
    )

    # Secrets
    tailscale_auth_key_secret = Secret(
        "tailscale-auth-key-secret", secret_string=config.require_secret("tailscale-auth-key")
    )

    # Image repos
    tailscale_beacon_image_repo = Repository("tailscale-beacon-image-repo", "tailscale-beacon", force_delete=config.require_bool("devMode"))
    export("tailscale-beacon-image-repo-url", tailscale_beacon_image_repo.url)
    
    # Allow image repo action role to push to this image repo
    prepare_deploy_role.allow_image_repo_actions([tailscale_beacon_image_repo])

    # Security groups
    tailscale_beacon_security_group = SecurityGroup(
        "tailscale-beacon-security-group",
        vpc=vpc,
        vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
        rules=[
            {
                "cidr_name": "anywhere",
                "to_cidr": "0.0.0.0/0",
                "ports": [53],
                "protocols": ["udp", "tcp"],
            },  # temp hack, Allow egress for DNS resolution (required for curl and tailscale to resolve hostnames), need a real nat instance instead
            {
                "cidr_name": "anywhere",
                "to_cidr": "0.0.0.0/0",
                "ports": [443],
            },  # Allow https egress to the tailscale control plane
            {
                "cidr_name": "anywhere",
                "to_cidr": "0.0.0.0/0",
                "ports": [41641],
                "protocols": ["udp"],
            },  # Allow egress to the tailscale DERP servers (WireGuard over UDP)
            {
                "cidr_name": "anywhere",
                "to_cidr": "0.0.0.0/0",
                "ports": [3478],
                "protocols": ["udp"],
            },  # Allow egress for STUN (NAT traversal)
        ],
    )

    # Load balancer
    load_balancer_security_group = SecurityGroup(
        "tailscale-beacon-load-balancer-security-group",
        vpc=vpc,
        rules=[
            {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
            {"to_security_group": tailscale_beacon_security_group, "ports": [80]},
        ],
    )

    load_balancer = LoadBalancer(
        "tailscale-beacon-lb", security_groups=[load_balancer_security_group.id], subnets=vpc.public_subnet_ids
    )

    target_group = TargetGroup(
        "tailscale-beacon-tg",
        vpc_id=vpc.id,
        port=80,
        protocol="HTTP",
        target_type="ip",
        deregistration_delay=30,
        health_check={"path": "/health", "matcher": "200-399"},
    )

    Listener(
        "tailscale-beacon-https-listener",
        load_balancer_arn=load_balancer.arn,
        port=443,
        protocol="HTTPS",
        certificate_arn=certificate_arn,
        default_actions=[{"type": "forward", "target_group_arn": target_group.arn}],
    )

    Listener(
        "tailscale-beacon-http-listener",
        load_balancer_arn=load_balancer.arn,
        port=80,
        protocol="HTTP",
        default_actions=[
            {"type": "redirect", "redirect": {"protocol": "HTTPS", "port": "443", "status_code": "HTTP_301"}}
        ],
    )

    # DNS records
    for device_name in config.require_object("tailnet-devices"):
        for service_name in service_map.keys():
            Record(
                f"{device_name}-{service_name}",
                zone_id=zone_id,
                name=Output.concat(device_name, "-", service_name, ".", domain),
                type="A",
                aliases=[
                    {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": False}
                ],
            )

    # Execution role
    execution_role = Role("tailscale-beacon-exec-role", assume_role_policy=ecs_assume_role_policy())
    execution_role.allow_secret_get([tailscale_auth_key_secret])

    digest = tailscale_beacon_image_repo.locked_digest()

    if not digest:
        return

    # Service
    tailscale_service = FargateService(
        "tailscale-beacon-service",
        name="tailscale-beacon-service",
        cluster=cluster.arn,
        desired_count=1,
        network_configuration={
            "subnets": vpc.public_subnet_ids,
            "security_groups": [tailscale_beacon_security_group.id],
            "assign_public_ip": True,
        },
        task_definition_args={
            "execution_role": {"role_arn": execution_role.arn},
            "containers": {
                "tailscale-beacon": {
                    "name": "tailscale-beacon",
                    "image": digest,
                    "log_configuration": log_configuration(tailscale_beacon_log_group),
                    "port_mappings": [{"container_port": 80, "host_port": 80, "target_group": target_group}],
                    "secrets": [{"name": "TS_AUTHKEY", "value_from": tailscale_auth_key_secret.arn}],
                    "environment": [
                        {"name": "TAILNET", "value": config.require("tailnet-name")},
                        {"name": "DOMAIN", "value": domain},
                        {"name": "SERVICES", "value": " ".join(f"{k}:{v}" for k, v in service_map.items())},
                        {"name": "_TS_AUTHKEY_VERSION", "value": tailscale_auth_key_secret.version_id},
                    ],
                }
            },
        },
    )

    # Allow service deployment role to deploy this service
    deploy_role.allow_service_deployment("tailscale-beacon",[tailscale_service.service.arn], [execution_role.arn])
