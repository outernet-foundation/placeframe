from __future__ import annotations

import pulumi_aws as aws


def create_postgres_security_group() -> aws.ec2.SecurityGroup:
    """
    Security group that allows TCP/5432 traffic *within* the VPC (10.0.0.0/8).
    Adjust CIDR to your environment as needed.
    """
    return aws.ec2.SecurityGroup(
        resource_name="postgresSecurityGroup",
        description="Allow Postgres inside VPC",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=5432,
                to_port=5432,
                cidr_blocks=["10.0.0.0/8"],
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            )
        ],
    )
