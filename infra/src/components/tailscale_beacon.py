from pathlib import Path

import pulumi_awsx
from pulumi import Config, Input, Output
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecr import Repository, get_authorization_token
from pulumi_aws.lb import Listener, LoadBalancer
from pulumi_awsx.ecs import EC2Service
from pulumi_docker import Image

from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_tailscale_beacon(
    config: Config, vpc: Vpc, zone_id: Input[str], domain: Input[str], certificate_arn: Input[str]
):
    load_balancer_security_group = SecurityGroup("tailscale-bridge-load-balancer-security-group", vpc_id=vpc.id)
    tailscale_bridge_security_group = SecurityGroup("tailscale-bridge-security-group", vpc_id=vpc.id)

    # Allow http/https ingress to the load balancer from anywhere
    load_balancer_security_group.allow_ingress_cidr(cidr_name="anywhere", cidr="0.0.0.0/0", ports=[80], protocol="tcp")
    load_balancer_security_group.allow_ingress_cidr(cidr_name="anywhere", cidr="0.0.0.0/0", ports=[443], protocol="tcp")

    # Allow the load balancer to access the Tailscale bridge
    tailscale_bridge_security_group.allow_ingress_reciprocal(
        from_security_group=load_balancer_security_group, ports=[80]
    )

    vpc.allow_endpoint_access(
        security_group=tailscale_bridge_security_group,
        interfaces=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts"],
    )

    # Allow egress to the tailscale control plane
    tailscale_bridge_security_group.allow_egress_cidr(
        cidr_name="tailscale-control-plane", cidr="0.0.0.0/0", ports=[443]
    )

    # Allow egress to the tailscale DERP servers
    tailscale_bridge_security_group.allow_egress_cidr(
        cidr_name="tailscale-derp", cidr="0.0.0.0/0", ports=[41641], protocol="udp"
    )

    # Create a load balancer for the Tailscale bridge
    load_balancer = LoadBalancer(
        "tailscale-bridge-lb", security_groups=[load_balancer_security_group.id], subnets=vpc.public_subnet_ids
    )

    # Minimal HTTPS listener with a 404 fixed‑response default; real routing is
    # added via one ListenerRule per engineer later.
    https_listener = Listener(
        "tailscale-bridge-https-listener",
        load_balancer_arn=load_balancer.arn,
        port=443,
        protocol="HTTPS",
        certificate_arn=certificate_arn,
        default_actions=[
            {"type": "fixed-response", "fixed_response": {"content_type": "text/plain", "status_code": "404"}}
        ],
    )

    # Optional HTTP → HTTPS redirect (kept very simple).
    Listener(
        "tailscale-bridge-http-listener",
        load_balancer_arn=load_balancer.arn,
        port=80,
        protocol="HTTP",
        default_actions=[
            {"type": "redirect", "redirect": {"protocol": "HTTPS", "port": "443", "status_code": "HTTP_301"}}
        ],
    )

    # Create repos for image pull-through cache
    tailscale_beacon_repo = Repository("tailscale-beacon-repo", force_delete=config.require_bool("devMode"))
    dockerfile = Path(config.require("tailscale-beacon-dockerfile")).resolve()
    creds = get_authorization_token()
    tailscale_beacon_image = Image(
        "tailscale-beacon-image",
        build={"dockerfile": str(dockerfile), "context": str(dockerfile.parent), "platform": "linux/amd64"},
        image_name=Output.concat(tailscale_beacon_repo.repository_url, ":", "latest"),
        registry={"server": creds.proxy_endpoint, "username": creds.user_name, "password": creds.password},
    )

    local_services = {"cloudbeaver": 8978, "minio": 9000, "minioconsole": 9001, "api": 8000}

    tailscale_auth_key_secret = Secret(
        "tailscale-auth-key-secret", secret_string=config.require_secret("tailscale-auth-key")
    )

    LogGroup("tailscale-beacon-log-group", name="/ecs/tailscale-beacon", retention_in_days=7)

    cluster = pulumi_awsx.ecs.Cluster(
        "tailscale-beacon-cluster", instance_type="t3.micro", desired_capacity=1, min_size=1, max_size=2
    )

    tailnet_name = config.require("tailscale-tailnet-name")

    service = EC2Service(
        "tailscale-beacon-service",
        cluster=cluster,
        network_mode="host",  # keep ALB→instance:80
        desired_count=1,
        task_definition_args={
            "containers": {
                "tailscale-beacon": {
                    "image": tailscale_beacon_image.repo_digest,
                    "linux_parameters": {"capabilities": {"add": ["NET_ADMIN"]}},
                    "environment": [{"name": "TAILNET_NAME", "value": tailnet_name}],
                    "secrets": {"TS_AUTHKEY": tailscale_auth_key_secret.arn},
                    "port_mappings": [{"container_port": 80, "host_port": 80, "protocol": "tcp"}],
                }
            }
        },
    )

    # target_group = TargetGroup(
    #     f"tsb-{name}-tg",
    #     port=80,
    #     protocol="HTTP",
    #     target_type="ip",
    #     vpc_id=load_balancer.vpc_id,
    #     health_check={"path": "/health"},  # simple quick check
    # )

    # ListenerRule(
    #     f"tailscale-listener-rule-{name}",
    #     listener_arn=https_listener.arn,
    #     actions=[{"type": "forward", "target_group_arn": target_group.arn}],
    #     conditions=[{"host_header": {"values": [f"{name}-*.{domain}"]}}],
    # )

    # for local_service in local_services:
    #     Record(
    #         f"{local_service}-{name}",
    #         zone_id=zone_id,
    #         name=f"{name}-{local_service}.{domain}",
    #         type="A",
    #         aliases=[
    #             {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": False}
    #         ],
    #     )

    # # Create a policy allowing the tailscale bridge to access secrets and use the pull-through cache
    # policy = auth_key_secret.arn.apply(
    #     lambda arn: json.dumps({
    #         "Version": "2012-10-17",
    #         "Statement": [
    #             {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": [arn]},
    #             {"Effect": "Allow", "Action": "ecr:BatchImportUpstreamImage", "Resource": "*"},
    #         ],
    #     })
    # )

    # # Build Caddyfile
    # caddyfile = "{\n    auto_https off\n}\n" + ":80 {\n    respond /health 200\n}\n\n"
    # for svc, port in local_services.items():
    #     caddyfile += f"{name}-{svc}.{domain} {{\n    tls off\n reverse_proxy {ip}:{port}\n}}\n\n"

    # print(caddyfile)

    # FargateService(
    #     f"tailscale-bridge-{name}-service",
    #     cluster=cluster.arn,
    #     desired_count=1,
    #     network_configuration={
    #         "subnets": vpc.private_subnet_ids,
    #         "security_groups": [tailscale_bridge_security_group.id],
    #     },
    #     task_definition_args={
    #         "execution_role": {"args": {"inline_policies": [{"policy": policy}]}},
    #         "containers": {
    #             "tailscale": {
    #                 "name": "tailscale",
    #                 "image": get_region_output().name.apply(
    #                     lambda r: f"{get_caller_identity().account_id}.dkr.ecr.{r}.amazonaws.com/dockerhub/tailscale/tailscale:latest"
    #                 ),
    #                 "command": [
    #                     "/bin/sh",
    #                     "-c",
    #                     "tailscaled --tun=userspace-networking "
    #                     "--socks5-server=localhost:1055 "
    #                     # "--outbound-http-proxy-listen=localhost:1055 & "
    #                     f"tailscale up --hostname=bridge-{name} --authkey=$TS_AUTH_KEY --reset && "
    #                     "sleep infinity",
    #                 ],
    #                 "secrets": [{"name": "TS_AUTH_KEY", "value_from": auth_key_secret.arn}],
    #                 "log_configuration": {
    #                     "log_driver": "awslogs",
    #                     "options": {
    #                         "awslogs-group": f"/ecs/tailscale/{name}",
    #                         "awslogs-region": get_region_output().name,
    #                         "awslogs-stream-prefix": "ecs",
    #                     },
    #                 },
    #             }
    #         },
    #     },
    # )
