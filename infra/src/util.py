from typing import List

import pulumi_aws as aws
from pulumi_aws.ec2 import SecurityGroupEgressArgs

ALLOW_ALL_EGRESS: List[SecurityGroupEgressArgs] = [
    SecurityGroupEgressArgs(
        protocol="-1",
        from_port=0,
        to_port=0,
        cidr_blocks=["0.0.0.0/0"],
    )
]


def add_security_group_cross_reference(
    source_sg: aws.ec2.SecurityGroup,
    target_sg: aws.ec2.SecurityGroup,
    ports: List[int],
    source_name: str,
    target_name: str,
    protocol: str = "tcp",
) -> None:
    for port in ports:
        aws.vpc.SecurityGroupEgressRule(
            f"{source_name}-to-{target_name}-{port}",
            security_group_id=source_sg.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=target_sg.id,
        )
        aws.vpc.SecurityGroupIngressRule(
            f"{target_name}-from-{source_name}-{port}",
            security_group_id=target_sg.id,
            ip_protocol=protocol,
            from_port=port,
            to_port=port,
            referenced_security_group_id=source_sg.id,
        )
