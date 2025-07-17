from typing import Sequence

import pulumi_aws as aws


def get_default_subnet_ids() -> Sequence[str]:
    default_vpc = aws.ec2.get_vpc(default=True)
    subnets = aws.ec2.get_subnets(
        filters=[{"name": "vpc-id", "values": [default_vpc.id]}]
    )
    return subnets.ids
