from typing import cast

from pulumi import Config, Output, StackReference
from pulumi_aws.ecs import Cluster

from components.role import Role
from components.s3 import create_storage
from components.security_group import SecurityGroup
from components.vpc import Vpc, VpcInfo
from services.api import Api
from services.github_runner import GithubRunner


def create_dev_stack(config: Config):
    core_stack = StackReference("tyler-s-hatch/plerion_infra/core")
    zone_name = core_stack.require_output("zone-name")
    zone_id = core_stack.require_output("zone-id")
    certificate_arn = core_stack.require_output("certificate-arn")
    rds_security_group_id = core_stack.require_output("rds-security-group-id")
    rds_address = core_stack.require_output("rds-address")

    main_prepare_deploy_role = Role(
        "main-prepare-deploy-role",
        name=core_stack.require_output("main-prepare-deploy-role-name"),
        arn=core_stack.require_output("main-prepare-deploy-role-arn"),
    )
    main_deploy_role = Role(
        "main-deploy-role",
        name=core_stack.require_output("main-deploy-role-name"),
        arn=core_stack.require_output("main-deploy-role-arn"),
    )

    vpc = Vpc(name="main-vpc", vpc_info=cast(Output[VpcInfo], core_stack.require_output("vpc-info")))

    rds_security_group = SecurityGroup("rds-security-group", vpc=vpc, security_group_id=rds_security_group_id)

    captures_bucket = create_storage(core_stack)

    cluster = Cluster("main-cluster")

    GithubRunner(
        resource_name="github-runner",
        vpc=vpc,
        config=config,
        cluster=cluster,
        postgres_security_group=rds_security_group,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
    )

    Api(
        resource_name="api",
        config=config,
        zone_id=zone_id,
        zone_name=zone_name,
        certificate_arn=certificate_arn,
        vpc=vpc,
        cluster=cluster,
        s3_bucket=captures_bucket,
        rds_security_group=rds_security_group,
        rds_address=rds_address,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
    )
