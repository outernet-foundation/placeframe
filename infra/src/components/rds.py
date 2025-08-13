import pulumi_aws as aws
from pulumi import Config, Input, Output, export

from components.iam import allow_secret_get
from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


def create_database(config: Config, vpc: Vpc, deploy_role_name: Input[str]):
    db_user: str = config.require("postgres-user")
    db_password_output = config.require_secret("postgres-password")

    subnet_group = aws.rds.SubnetGroup(resource_name="db-subnet-group", subnet_ids=vpc.private_subnet_ids)

    postgres_security_group = SecurityGroup("postgres-security-group", vpc=vpc)

    postgres = aws.rds.Instance(
        "postgres",
        db_name="postgres",
        engine="postgres",
        engine_version="15",
        instance_class="db.t3.micro",
        allocated_storage=20,
        db_subnet_group_name=subnet_group.id,
        vpc_security_group_ids=[postgres_security_group.id],
        username=db_user,
        password=db_password_output,
        skip_final_snapshot=True,
    )

    postgres_dsn_secret = Secret(
        "postgres-dsn-secret",
        secret_string=Output.concat(
            "postgresql://", db_user, ":", db_password_output, "@", postgres.address, ":5432/postgres"
        ),
    )

    allow_secret_get(deploy_role_name, [postgres_dsn_secret])
    export("postgres-dsn-secret-arn", postgres_dsn_secret.arn)

    return postgres, postgres_security_group, postgres_dsn_secret
