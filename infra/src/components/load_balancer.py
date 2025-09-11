from pulumi import ComponentResource, Input, ResourceOptions
from pulumi_aws import lb
from pulumi_aws.lb import Listener, TargetGroup, TargetGroupHealthCheckArgsDict

from components.security_group import SecurityGroup
from components.vpc import Vpc


class LoadBalancer(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        service_name: str,
        vpc: Vpc,
        certificate_arn: Input[str],
        ingress_cidr: Input[str],
        *,
        internal: bool = False,
        target_type: Input[str] = "ip",
        target_port: Input[int] | None = None,
        protocol: Input[str] | None = "HTTP",
        deregistration_delay: Input[int] = 60,
        health_check: TargetGroupHealthCheckArgsDict | None = None,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:LoadBalancer", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        self.security_group = SecurityGroup(
            f"{service_name}-security-group",
            vpc=vpc,
            rules=[{"cidr_name": "anywhere", "from_cidr": ingress_cidr, "ports": [80, 443]}],
            opts=self._child_opts,
        )

        self.load_balancer = lb.LoadBalancer(
            f"{service_name}-lb",
            security_groups=[self.security_group.id],
            subnets=vpc.private_subnet_ids if internal else vpc.public_subnet_ids,
            internal=internal,
            opts=self._child_opts,
        )

        if target_type != "lambda" and health_check is None:
            health_check = TargetGroupHealthCheckArgsDict(
                path="/", protocol="HTTP", interval=15, healthy_threshold=2, unhealthy_threshold=10
            )

        self.target_group = TargetGroup(
            f"{service_name}-lb-tg",
            port=target_port,
            protocol=protocol,
            target_type=target_type,
            vpc_id=self.load_balancer.vpc_id,
            deregistration_delay=deregistration_delay,
            health_check=health_check,
            opts=self._child_opts,
        )

        Listener(
            f"{service_name}-https-listener",
            load_balancer_arn=self.load_balancer.arn,
            port=443,
            protocol="HTTPS",
            certificate_arn=certificate_arn,
            default_actions=[{"type": "forward", "target_group_arn": self.target_group.arn}],
            opts=self._child_opts,
        )

        Listener(
            f"{service_name}-http-listener",
            load_balancer_arn=self.load_balancer.arn,
            port=80,
            protocol="HTTP",
            default_actions=[
                {"type": "redirect", "redirect": {"protocol": "HTTPS", "port": "443", "status_code": "HTTP_301"}}
            ],
            opts=self._child_opts,
        )

        self.arn = self.load_balancer.arn
        self.dns_name = self.load_balancer.dns_name
        self.zone_id = self.load_balancer.zone_id

        self.register_outputs({"arn": self.arn, "dns_name": self.dns_name, "zone_id": self.zone_id})
