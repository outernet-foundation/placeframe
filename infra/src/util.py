from typing import List

import pulumi_aws as aws
from pulumi import Input
from pulumi_aws.ec2 import SecurityGroupEgressArgs

ALLOW_ALL_EGRESS: List[SecurityGroupEgressArgs] = [
    SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])
]


def create_zero_trust_security_group(name: str, vpc_id: Input[str]) -> aws.ec2.SecurityGroup:
    return aws.ec2.SecurityGroup(resource_name=f"{name}-security-group", vpc_id=vpc_id, ingress=[], egress=[])


def add_reciprocal_security_group_rules(
    ingress_sg: aws.ec2.SecurityGroup, egress_sg: aws.ec2.SecurityGroup, ports: List[int], protocol: str = "tcp"
) -> None:
    ingress_name = ingress_sg.name.apply(lambda id: id.replace("-security-group", ""))
    egress_name = egress_sg.name.apply(lambda id: id.replace("-security-group", ""))

    for port in ports:
        aws.vpc.SecurityGroupIngressRule(
            f"{ingress_name}-ingress-from-{egress_name}-{port}",
            security_group_id=ingress_sg.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=egress_sg.id,
        )
        aws.vpc.SecurityGroupEgressRule(
            f"{egress_name}-egress-to-{ingress_name}-{port}",
            security_group_id=egress_sg.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=ingress_sg.id,
        )
