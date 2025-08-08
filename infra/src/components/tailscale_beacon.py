from pulumi import Config, Input, Output, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_images_output
from pulumi_aws.ecs import Cluster
from pulumi_aws.lb import Listener, LoadBalancer, TargetGroup
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.ecr import repo_digest
from components.log import log_configuration
from components.role_policies import allow_repo_push, allow_secret_get, create_github_actions_role
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
    github_oidc_provider_arn: Output[str],
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
    tailscale_beacon_image_repo = Repository("tailscale-beacon-image-repo", force_delete=config.require_bool("devMode"))

    # Github actions role
    github_actions_role = create_github_actions_role(
        "tailscale-beacon-image-repo-role",
        config=config,
        github_oidc_provider_arn=github_oidc_provider_arn,
        policies={"ecr-policy": allow_repo_push([tailscale_beacon_image_repo])},
    )

    # Exports
    export("tailscale-beacon-repo", tailscale_beacon_image_repo.repository_url)
    export("tailscale-beacon-repo-role-arn", github_actions_role.arn)

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

    # Service
    get_images_output(repository_name=tailscale_beacon_image_repo.name).apply(
        lambda images_data: None
        if not images_data.image_ids  # If there are no images, don't create the service
        else FargateService(
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
                "execution_role": {
                    "args": {"inline_policies": [{"policy": allow_secret_get([tailscale_auth_key_secret])}]}
                },
                "containers": {
                    "tailscale-beacon": {
                        "name": "tailscale-beacon",
                        "image": repo_digest(tailscale_beacon_image_repo),
                        "log_configuration": log_configuration(tailscale_beacon_log_group),
                        "port_mappings": [{"container_port": 80, "host_port": 80, "target_group": target_group}],
                        "secrets": [{"name": "TS_AUTHKEY", "value_from": tailscale_auth_key_secret.arn}],
                        "environment": [
                            {"name": "TAILNET", "value": config.require("tailnet-name")},
                            {"name": "DOMAIN", "value": domain},
                            {"name": "SERVICES", "value": " ".join(f"{k}:{v}" for k, v in service_map.items())},
                            {"name": "TS_AUTHKEY_VERSION", "value": tailscale_auth_key_secret.version_id},
                        ],
                    }
                },
            },
        )
    )
