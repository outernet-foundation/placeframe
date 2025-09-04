from typing import cast

from pulumi import Config, Output, StackReference
from pulumi_aws.ecs import Cluster

from components.nat_instance import NatInstance
from components.oauth import Oauth
from components.rds import create_database
from components.role import Role
from components.s3 import create_storage
from components.vpc import Vpc, VpcInfo
from services.api import Api
from services.cloudbeaver import Cloudbeaver
from services.github_runner import GithubRunner


def create_dev_stack(config: Config):
    core_stack = StackReference("tyler-s-hatch/plerion_infra/core")
    zone_name = core_stack.require_output("zone-name")
    zone_id = core_stack.require_output("zone-id")
    certificate_arn = core_stack.require_output("certificate-arn")

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

    oauth = Oauth(
        "cloudbeaver-oauth",
        config=config,
        proxy_image_repo_name=core_stack.require_output("oauth2-proxy-image-repo-name"),
        reverse_proxy_image_repo_name=core_stack.require_output("oauth2-reverse-proxy-image-repo-name"),
        client_id_secret_arn=core_stack.require_output("oauth2-client-id-secret-arn"),
        client_secret_secret_arn=core_stack.require_output("oauth2-client-secret-secret-arn"),
        cookie_secret_secret_arn=core_stack.require_output("oauth2-cookie-secret-secret-arn"),
    )

    vpc = Vpc(name="main-vpc", vpc_info=cast(Output[VpcInfo], core_stack.require_output("vpc-info")))

    NatInstance("main-nat", vpc=vpc)

    captures_bucket = create_storage(core_stack)

    postgres_instance, postgres_security_group = create_database(config, vpc)

    cluster = Cluster("main-cluster")

    GithubRunner(
        resource_name="github-runner",
        vpc=vpc,
        config=config,
        cluster=cluster,
        postgres_security_group=postgres_security_group,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
    )

    Cloudbeaver(
        resource_name="cloudbeaver",
        config=config,
        zone_name=zone_name,
        zone_id=zone_id,
        certificate_arn=certificate_arn,
        vpc=vpc,
        postgres_security_group=postgres_security_group,
        db=postgres_instance,
        cluster=cluster,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
        oauth=oauth,
    )

    Api(
        resource_name="api",
        config=config,
        zone_id=zone_id,
        zone_name=zone_name,
        certificate_arn=certificate_arn,
        cluster=cluster,
        s3_bucket=captures_bucket,
        vpc=vpc,
        postgres_security_group=postgres_security_group,
        postgres_instance=postgres_instance,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
    )
