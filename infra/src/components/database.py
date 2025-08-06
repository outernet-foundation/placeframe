import pulumi_aws as aws
from pulumi import Config, Output

from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_database(config: Config, security_group: SecurityGroup, vpc: Vpc) -> tuple[aws.rds.Instance, Secret]:
    db_user: str = config.require("postgres-user")
    db_password_output = config.require_secret("postgres-password")

    subnet_group = aws.rds.SubnetGroup(resource_name="db-subnet-group", subnet_ids=vpc.private_subnet_ids)

    db_instance = aws.rds.Instance(
        "postgres",
        db_name="postgres",
        engine="postgres",
        engine_version="15",
        instance_class="db.t3.micro",
        allocated_storage=20,
        db_subnet_group_name=subnet_group.id,
        vpc_security_group_ids=[security_group.id],
        username=db_user,
        password=db_password_output,
        skip_final_snapshot=True,
    )

    connection_secret = Secret(
        "db-connection-secret",
        name="prod/db/connection",
        secret_string=Output.concat(
            "postgresql://", db_user, ":", db_password_output, "@", db_instance.address, ":5432/postgres"
        ),
    )

    return db_instance, connection_secret
