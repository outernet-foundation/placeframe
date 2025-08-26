from pulumi import ComponentResource, Config, Input, Output, ResourceOptions, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.assume_role_policies import ecs_assume_role_policy
from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.repository import Repository
from components.role import Role
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc

service_map: dict[str, int] = {"api": 8000, "cloudbeaver": 8978, "minio": 9000, "minioconsole": 9001}


class TailscaleBeacon(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        vpc: Vpc,
        zone_id: Input[str],
        domain: Input[str],
        certificate_arn: Input[str],
        cluster: Cluster,
        prepare_deploy_role: Role,
        deploy_role: Role,
        *,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:TailscaleBeacon", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Log groups
        tailscale_beacon_log_group = LogGroup(
            "tailscale-beacon-log-group", name="/ecs/tailscale-beacon", retention_in_days=7, opts=self._child_opts
        )

        # Secrets
        tailscale_auth_key_secret = Secret(
            "tailscale-auth-key-secret",
            secret_string=config.require_secret("tailscale-auth-key"),
            opts=self._child_opts,
        )

        # Image repos
        tailscale_beacon_image_repo = Repository(
            "tailscale-beacon-image-repo",
            "tailscale-beacon",
            opts=ResourceOptions.merge(
                self._child_opts,
                # ResourceOptions(retain_on_delete=True),
                ResourceOptions(import_="tailscale-beacon"),
            ),
        )
        prepare_deploy_role.allow_image_repo_actions([tailscale_beacon_image_repo])
        export("tailscale-beacon-image-repo-url", tailscale_beacon_image_repo.url)

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
            opts=self._child_opts,
        )

        load_balancer_security_group = SecurityGroup(
            "tailscale-beacon-load-balancer-security-group",
            vpc=vpc,
            rules=[
                {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
                {"to_security_group": tailscale_beacon_security_group, "ports": [80]},
            ],
            opts=self._child_opts,
        )

        # Load balancer
        load_balancer = LoadBalancer(
            "api-loadbalancer",
            "api",
            vpc=vpc,
            securityGroup=load_balancer_security_group,
            certificate_arn=certificate_arn,
            port=80,
            deregistration_delay=30,
            health_check={"path": "/health", "matcher": "200-399"},
            opts=self._child_opts,
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
                        {
                            "name": load_balancer.dns_name,
                            "zone_id": load_balancer.zone_id,
                            "evaluate_target_health": False,
                        }
                    ],
                    opts=self._child_opts,
                )

        # Execution role
        execution_role = Role(
            "tailscale-beacon-exec-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts
        )
        execution_role.attach_ecs_task_execution_role_policy()
        execution_role.allow_secret_get([tailscale_auth_key_secret])

        # Task role
        task_role = Role(
            "tailscale-beacon-task-role", assume_role_policy=ecs_assume_role_policy(), opts=self._child_opts
        )

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
                "task_role": {"role_arn": task_role.arn},
                "containers": {
                    "tailscale-beacon": {
                        "name": "tailscale-beacon",
                        "image": tailscale_beacon_image_repo.locked_digest(),
                        "log_configuration": log_configuration(tailscale_beacon_log_group),
                        "port_mappings": [
                            {"container_port": 80, "host_port": 80, "target_group": load_balancer.target_group}
                        ],
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
            opts=self._child_opts,
        )

        # Allow service deployment role to deploy this service
        deploy_role.allow_service_deployment(
            "tailscale-beacon", [tailscale_service.service.arn], [execution_role.arn, task_role.arn]
        )
