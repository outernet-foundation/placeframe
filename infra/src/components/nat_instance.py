from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_aws.ec2 import Instance, Route, RouteArgs, get_ami_output, get_route_table_output

from components.security_group import SecurityGroup
from components.vpc import Vpc


# https://docs.aws.amazon.com/vpc/latest/userguide/work-with-nat-instances.html
def user_data(vpc_cidr: str) -> str:
    return f"""
#!/bin/bash
set -euxo pipefail

# Enable IP forwarding
echo 'net.ipv4.ip_forward=1' >/etc/sysctl.d/99-nat.conf
sysctl --system

# Install iptables
yum -y install iptables-services
systemctl enable --now iptables

# Determine egress network interface name
OUT_IF="$(ip route show default | awk '{{print $5; exit}}')"

# Allow egress to use this instance’s public IP via NAT (MASQUERADE); add rule if absent
iptables -C -t nat POSTROUTING -o "$OUT_IF" -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o "$OUT_IF" -j MASQUERADE

# Default to disallowing all forwarding
iptables -P FORWARD DROP

# Clear existing forwarding rules
iptables -F FORWARD

# Allow ingress from already established connections
iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow egress from the vpc's private subnets to the internet
iptables -A FORWARD -s "{vpc_cidr}" -o "$OUT_IF" -j ACCEPT

# Persist rules
service iptables save
"""


class NatInstance(ComponentResource):
    def __init__(self, resource_name: str, vpc: Vpc, *, opts: ResourceOptions | None = None) -> None:
        super().__init__("custom:NatInstance", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Security groups
        security_group = SecurityGroup(
            f"{resource_name}-security-group",
            vpc=vpc,
            rules=[
                {
                    "cidr_name": "vpc",
                    "from_cidr": vpc.cidr_block,
                    "ports": [0],
                    "protocols": ["-1"],
                },  # Allow ingress from VPC over all protocols
                {
                    "cidr_name": "anywhere",
                    "to_cidr": "0.0.0.0/0",
                    "ports": [0],
                    "protocols": ["-1"],
                },  # Allow egress to anywhere over all protocols
            ],
            opts=self._child_opts,
        )

        # EC2
        instance = Instance(
            f"{resource_name}-instance",
            ami=get_ami_output(
                owners=["amazon"],
                most_recent=True,
                filters=[{"name": "name", "values": ["amzn2-ami-kernel-5.10-hvm-*-arm64-gp2"]}],
            ).id,
            instance_type="t4g.nano",
            subnet_id=vpc.public_subnet_ids.apply(lambda ids: ids[0]),
            vpc_security_group_ids=[security_group.id],
            associate_public_ip_address=True,
            source_dest_check=False,
            user_data=Output.from_input(vpc.cidr_block).apply(lambda cidr: user_data(cidr)),
            metadata_options={"http_tokens": "required"},
            opts=self._child_opts,
        )

        # Routes
        vpc.private_subnet_ids.apply(
            lambda ids: [
                Route(
                    f"{resource_name}-route-{i}",
                    RouteArgs(
                        route_table_id=get_route_table_output(subnet_id=sid).id,
                        destination_cidr_block="0.0.0.0/0",
                        network_interface_id=instance.primary_network_interface_id,
                    ),
                    opts=self._child_opts,
                )
                for i, sid in enumerate(ids)
            ]
        )
