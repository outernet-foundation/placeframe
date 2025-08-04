import json
import re
from pathlib import Path
from string import Template

from pulumi import Config, Input, Output
from pulumi_aws import get_region_output
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.ecs import Cluster
from pulumi_aws.lb import Listener, LoadBalancer, TargetGroup
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService
from pulumi_docker import Image

from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def render_caddyfile(domain: str, tailnet: str, svc_to_port: dict[str, int]) -> str:
    service_names = "|".join(sorted(svc_to_port))
    # Need 8 spaces for proper indentation in the map block
    port_mappings = "\n        ".join(f"{svc} {port}" for svc, port in sorted(svc_to_port.items()))
    escaped_domain = re.escape(domain)  # safe for regex

    tpl = Template(r"""{
    admin off
    auto_https off
    debug
}

:80 {
    log {
        output stdout
        format console
        level DEBUG
    }
    
    respond /health 200
    
    @pair header_regexp pair Host ^([^.]+?)-(${SERVICE_NAMES})\.${ESCAPED_DOMAIN}$$
    
    handle @pair {
        header {
            X-Map-Source "{http.regexp.pair.2}"
            X-Up-Port-BEFORE "{http.vars.up_port}"
        }
                   


        map {http.regexp.pair.2} {up_port} {
            api "8000"
            cloudbeaver "8978"
            minio "9000"
            minioconsole "9001"
            default "0
        }
                    
        header {
            X-Up-Port-COPY "{http.vars.up_port_copy}"
        } 

        # Show the result of the map
        header {
            X-Up-Port-AFTER "{up_port}"
        }
                   
        vars {
            up_port_literal 8000
        }
                   
        header {
            X-Up-Port-LITERAL "{http.vars.up_port_literal}"
        }

        # Short-circuit so you can read the values without proxying
        respond 200
    }
    
    respond 404
}
""")

    return tpl.substitute(
        SERVICE_NAMES=service_names, ESCAPED_DOMAIN=escaped_domain, PORT_MAPPINGS=port_mappings, TAILNET=tailnet
    )

    return tpl.substitute(
        SERVICE_NAMES=service_names, ESCAPED_DOMAIN=escaped_domain, PORT_MAPPINGS=port_mappings, TAILNET=tailnet
    )


def create_tailscale_beacon(
    config: Config, vpc: Vpc, zone_id: Input[str], domain: Input[str], certificate_arn: Input[str]
):
    load_balancer_security_group = SecurityGroup("tailscale-bridge-load-balancer-security-group", vpc_id=vpc.id)
    tailscale_bridge_security_group = SecurityGroup("tailscale-bridge-security-group", vpc_id=vpc.id)

    # Allow http/https ingress to the load balancer from anywhere
    load_balancer_security_group.allow_ingress_cidr(cidr_name="anywhere", cidr="0.0.0.0/0", ports=[80], protocol="tcp")
    load_balancer_security_group.allow_ingress_cidr(cidr_name="anywhere", cidr="0.0.0.0/0", ports=[443], protocol="tcp")

    # Allow the load balancer to access the service task (port 80)
    tailscale_bridge_security_group.allow_ingress_reciprocal(
        from_security_group=load_balancer_security_group, ports=[80]
    )

    # Private interface endpoints the task may hit (image pulls/logs/secrets)
    vpc.allow_endpoint_access(
        security_group=tailscale_bridge_security_group,
        interfaces=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts"],
    )

    # Allow egress for DNS resolution (required for curl and tailscale to resolve hostnames)
    tailscale_bridge_security_group.allow_egress_cidr(cidr_name="dns", cidr="0.0.0.0/0", ports=[53], protocol="udp")
    tailscale_bridge_security_group.allow_egress_cidr(cidr_name="dns", cidr="0.0.0.0/0", ports=[53], protocol="tcp")

    # Allow egress to the tailscale control plane (HTTPS) and DERP (WireGuard over UDP)
    tailscale_bridge_security_group.allow_egress_cidr(
        cidr_name="tailscale-control-plane", cidr="0.0.0.0/0", ports=[443]
    )
    tailscale_bridge_security_group.allow_egress_cidr(
        cidr_name="tailscale-derp", cidr="0.0.0.0/0", ports=[41641], protocol="udp"
    )

    # Add HTTP for bootstrap DNS fallback
    tailscale_bridge_security_group.allow_egress_cidr(cidr_name="tailscale-bootstrap", cidr="0.0.0.0/0", ports=[80])

    # Add STUN for NAT traversal (used during connection establishment)
    tailscale_bridge_security_group.allow_egress_cidr(
        cidr_name="tailscale-stun", cidr="0.0.0.0/0", ports=[3478], protocol="udp"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # ECS Cluster (Fargate — no capacity config needed)
    # ─────────────────────────────────────────────────────────────────────────
    cluster = Cluster("tailscale-beacon-cluster")

    # ─────────────────────────────────────────────────────────────────────────
    # Public ALB (TLS at ALB; HTTP to task)
    # ─────────────────────────────────────────────────────────────────────────
    load_balancer = LoadBalancer(
        "tailscale-bridge-lb", security_groups=[load_balancer_security_group.id], subnets=vpc.public_subnet_ids
    )

    # Fargate requires target_type="ip"
    target_group = TargetGroup(
        "tailscale-beacon-tg",
        vpc_id=vpc.id,
        port=80,
        protocol="HTTP",
        target_type="ip",
        deregistration_delay=30,
        health_check={"path": "/health", "matcher": "200-399"},
    )

    # HTTPS listener → forward to TG
    Listener(
        "tailscale-bridge-https-listener",
        load_balancer_arn=load_balancer.arn,
        port=443,
        protocol="HTTPS",
        certificate_arn=certificate_arn,
        default_actions=[{"type": "forward", "target_group_arn": target_group.arn}],
    )

    Listener(
        "tailscale-bridge-http-listener",
        load_balancer_arn=load_balancer.arn,
        port=80,
        protocol="HTTP",
        default_actions=[{"type": "forward", "target_group_arn": target_group.arn}],
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Container image (single container runs tailscaled + Caddy via entrypoint)
    # ─────────────────────────────────────────────────────────────────────────
    tailscale_beacon_repo = Repository("tailscale-beacon-repo", force_delete=config.require_bool("devMode"))
    dockerfile = Path(config.require("tailscale-beacon-dockerfile")).resolve()
    creds = get_authorization_token()
    tailscale_beacon_image = Image(
        "tailscale-beacon-image",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=Output.concat(tailscale_beacon_repo.repository_url, ":", "latest"),
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    # Tailscale auth key (ECS task secret)
    tailscale_auth_key_secret = Secret(
        "tailscale-auth-key-secret", secret_string=config.require_secret("tailscale-auth-key")
    )

    tailnet_name = config.require("tailnet-name")

    # Service→port mapping for memorable names (can be overridden via config)
    # e.g., pulumi config set caddy-services '{"api":8000,"cloudbeaver":8978,"minio":9000,"minioconsole":9001}'
    service_map: dict[str, int] = config.get_object("caddy-services") or {
        "api": 8000,
        "cloudbeaver": 8978,
        "minio": 9000,
        "minioconsole": 9001,
    }

    # Render Caddyfile once from (domain, tailnet, service map)
    caddyfile_text = Output.all(domain, tailnet_name).apply(
        lambda args: render_caddyfile(args[0], args[1], service_map)
    )

    caddyfile_text.apply(lambda x: print(f"Caddyfile:\n{x}"))

    # Execution role inline policy to allow ECS to pull the secret value for TS_AUTHKEY
    policy = tailscale_auth_key_secret.arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": [arn]}],
        })
    )

    ssm_inline = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenControlChannel",
                    "ssmmessages:OpenDataChannel",
                ],
                "Resource": "*",
            }
        ],
    })

    LogGroup("tailscale-beacon-log-group", name="/ecs/tailscale-beacon", retention_in_days=7)

    FargateService(
        "tailscale-beacon-service",
        cluster=cluster.arn,
        desired_count=1,
        enable_execute_command=True,
        network_configuration={
            "subnets": vpc.public_subnet_ids,
            "security_groups": [tailscale_bridge_security_group.id],
            "assign_public_ip": True,
        },
        task_definition_args={
            "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
            "task_role": {"args": {"inline_policies": [{"policy": ssm_inline}]}},
            "containers": {
                "tailscale-beacon": {
                    "name": "tailscale-beacon",
                    "image": tailscale_beacon_image.repo_digest,
                    "environment": [{"name": "CADDYFILE", "value": caddyfile_text}],
                    "secrets": [{"name": "TS_AUTHKEY", "value_from": tailscale_auth_key_secret.arn}],
                    "port_mappings": [{"container_port": 80, "host_port": 80, "target_group": target_group}],
                    "log_configuration": {
                        "log_driver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/tailscale-beacon",
                            "awslogs-region": get_region_output().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                }
            },
        },
    )

    tailnet_devices: list[str] = config.require_object("tailnet-devices")
    print(f"Devices: {tailnet_devices}")
    for device_name in tailnet_devices:
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
