from typing import List

import pulumi_aws as aws
from pulumi_aws.ec2 import SecurityGroup
from pulumi_aws.vpc import SecurityGroupEgressRule, SecurityGroupIngressRule
from pulumi_awsx.ec2 import Vpc


def add_reciprocal_security_group_rules(
    from_resource_name: str,
    to_resource_name: str,
    from_security_group: SecurityGroup,
    to_security_group: SecurityGroup,
    ports: List[int],
    protocol: str = "tcp",
) -> None:
    for port in ports:
        SecurityGroupIngressRule(
            f"{to_resource_name}-ingress-from-{from_resource_name}-{port}",
            security_group_id=to_security_group.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=from_security_group.id,
        )
        SecurityGroupEgressRule(
            f"{from_resource_name}-egress-to-{to_resource_name}-{port}",
            security_group_id=from_security_group.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=to_security_group.id,
        )


def add_egress_to_dns_rule(resource_name: str, security_group: aws.ec2.SecurityGroup, vpc: Vpc) -> None:
    SecurityGroupEgressRule(
        f"{resource_name}-egress-to-dns-udp",
        security_group_id=security_group.id,
        ip_protocol="udp",
        from_port=53,
        to_port=53,
        cidr_ipv4=vpc.vpc.cidr_block,
    )
    SecurityGroupEgressRule(
        f"{resource_name}-egress-to-dns-tcp",
        security_group_id=security_group.id,
        ip_protocol="tcp",
        from_port=53,
        to_port=53,
        cidr_ipv4=vpc.vpc.cidr_block,
    )
