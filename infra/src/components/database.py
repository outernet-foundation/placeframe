from __future__ import annotations

import pulumi
import pulumi_aws as aws

from ..utils import get_default_subnet_ids
from .network import create_postgres_security_group


def create_database(*, config: pulumi.Config) -> aws.rds.Instance:
    instance_class: str = config.require("rdsInstanceClass")
    db_user: str = config.require("dbUsername")
    db_password_output = config.require_secret("dbPassword")

    # Security group permitting 5432 from inside VPC.
    postgres_sg = create_postgres_security_group()

    # Subnet group over default VPC subnets (sync lookups OK in small stacks).
    subnet_group = aws.rds.SubnetGroup(
        resource_name="dbSubnetGroup",
        subnet_ids=get_default_subnet_ids(),
    )

    db_instance = aws.rds.Instance(
        resource_name="postgresInstance",
        engine="postgres",
        engine_version="15.5",
        instance_class=instance_class,
        allocated_storage=20,
        db_subnet_group_name=subnet_group.id,
        vpc_security_group_ids=[postgres_sg.id],
        username=db_user,
        password=db_password_output,  # accepts Input[str]; we pass secret Output[str]
        skip_final_snapshot=True,
    )

    # Export a connection string as an Output[str]. Note we DO NOT stringify the secret
    # at plan time; Pulumi will handle secret propagation.
    pulumi.export(
        "postgresConnectionString",
        pulumi.Output.concat(
            "postgresql://",
            db_user,
            ":",
            db_password_output,
            "@",
            db_instance.address,
            ":5432/postgres",
        ),
    )

    return db_instance
