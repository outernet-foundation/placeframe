from typing import Sequence

import pulumi
import pulumi_aws as aws
from pulumi import Config, Input, Output

from components.security_group import SecurityGroup


def create_database(
    config: Config, security_group: SecurityGroup, subnet_ids: Input[Sequence[Input[str]]]
) -> tuple[aws.rds.Instance, Output[str]]:
    instance_class: str = config.require("rdsInstanceClass")
    db_user: str = config.require("postgres-user")
    db_password_output = config.require_secret("postgres-password")

    # Subnet group over default VPC subnets (sync lookups OK in small stacks).
    subnet_group = aws.rds.SubnetGroup(resource_name="db-subnet-group", subnet_ids=subnet_ids)

    db_instance = aws.rds.Instance(
        resource_name="postgres-instance",
        engine="postgres",
        engine_version="15.7",
        instance_class=instance_class,
        allocated_storage=20,
        db_subnet_group_name=subnet_group.id,
        vpc_security_group_ids=[security_group.id],
        username=db_user,
        password=db_password_output,  # accepts Input[str]; we pass secret Output[str]
        skip_final_snapshot=True,
    )

    # postgres_provider = postgresql.Provider(
    #     "postgres-provider",
    #     host=db_instance.address,
    #     port=5432,
    #     username=config.require("postgres-user"),
    #     password=config.require_secret("postgres-password"),
    #     database="postgres",  # Connect to default database first
    #     sslmode="require"
    # )

    # Export a connection string as an Output[str]. Note we DO NOT stringify the secret
    # at plan time; Pulumi will handle secret propagation.
    connection_string = Output.concat(
        "postgresql://", db_user, ":", db_password_output, "@", db_instance.address, ":5432/postgres"
    ).apply(lambda s: s)  # ensures Output[str], not Output[Any]

    pulumi.export("postgresConnectionString", connection_string)

    return db_instance, connection_string
