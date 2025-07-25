from typing import List

import pulumi_aws as aws
from pulumi import Input
from pulumi_awsx.ec2 import Vpc


def create_zero_trust_security_group(name: str, vpc_id: Input[str]) -> aws.ec2.SecurityGroup:
    return aws.ec2.SecurityGroup(resource_name=f"{name}-security-group", vpc_id=vpc_id, ingress=[], egress=[])


def add_reciprocal_security_group_rules(
    ingress_security_group: aws.ec2.SecurityGroup,
    egress_security_group: aws.ec2.SecurityGroup,
    ports: List[int],
    protocol: str = "tcp",
) -> None:
    ingress_name = ingress_security_group.name.apply(lambda id: id.replace("-security-group", ""))
    egress_name = egress_security_group.name.apply(lambda id: id.replace("-security-group", ""))

    for port in ports:
        aws.vpc.SecurityGroupIngressRule(
            f"{ingress_name}-ingress-from-{egress_name}-{port}",
            security_group_id=ingress_security_group.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=egress_security_group.id,
        )
        aws.vpc.SecurityGroupEgressRule(
            f"{egress_name}-egress-to-{ingress_name}-{port}",
            security_group_id=egress_security_group.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=ingress_security_group.id,
        )


def add_egress_to_dns_rule(security_group: aws.ec2.SecurityGroup, vpc: Vpc) -> None:
    aws.vpc.SecurityGroupEgressRule(
        f"{security_group.name}-egress-to-dns-udp",
        security_group_id=security_group.id,
        ip_protocol="udp",
        from_port=53,
        to_port=53,
        cidr_ipv4=vpc.vpc.cidr_block,
    )
    aws.vpc.SecurityGroupEgressRule(
        f"{security_group.name}-egress-to-dns-tcp",
        security_group_id=security_group.id,
        ip_protocol="tcp",
        from_port=53,
        to_port=53,
        cidr_ipv4=vpc.vpc.cidr_block,
    )
