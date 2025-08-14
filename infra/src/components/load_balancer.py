from pulumi import ComponentResource, Input, ResourceOptions
from pulumi_aws import lb
from pulumi_aws.lb import Listener, TargetGroup

from components.security_group import SecurityGroup
from components.vpc import Vpc


class LoadBalancer(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        service_name: str,
        vpc: Vpc,
        securityGroup: SecurityGroup,
        certificate_arn: Input[str],
        port: Input[int],
        *,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:LoadBalancer", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        self.load_balancer = lb.LoadBalancer(
            f"{service_name}-lb",
            security_groups=[securityGroup.id],
            subnets=vpc.public_subnet_ids,
            opts=self._child_opts,
        )

        self.target_group = TargetGroup(
            f"{service_name}-lb-tg",
            port=port,
            protocol="HTTP",
            target_type="ip",
            vpc_id=self.load_balancer.vpc_id,
            deregistration_delay=60,
            health_check={
                "path": "/",
                "protocol": "HTTP",
                "interval": 15,
                "healthy_threshold": 2,
                "unhealthy_threshold": 10,
            },
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

        self.dns_name = self.load_balancer.dns_name
        self.zone_id = self.load_balancer.zone_id

        self.register_outputs({"dns_name": self.dns_name, "zone_id": self.zone_id})
