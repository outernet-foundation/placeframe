from pulumi import Config, Output, export
from pulumi_aws.acm import Certificate, CertificateValidation
from pulumi_aws.ecr import PullThroughCacheRule
from pulumi_aws.ecs import Cluster
from pulumi_aws.iam import OpenIdConnectProvider
from pulumi_aws.route53 import Record, Zone

from components.nat_instance import NatInstance
from components.oauth import Oauth
from components.rds import RDSInstance
from components.role import Role
from components.roles import github_actions_assume_role_policy
from components.secret import Secret
from components.vpc import Vpc
from services.auth_gateway import AuthGateway
from services.cloudbeaver import Cloudbeaver
from services.database_manager import DatabaseManager
from services.tailscale_beacon import TailscaleBeacon


def create_core_stack(config: Config):
    github_oidc_provider = OpenIdConnectProvider(
        "github-oidc-provider",
        url="https://token.actions.githubusercontent.com",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],  # GitHub OIDC thumbprint
    )

    # Roles for GitHub Actions

    main_prepare_deploy_role = Role(
        resource_name="main-prepare-deploy-role",
        assume_role_policy=github_actions_assume_role_policy(config, github_oidc_provider.arn, "main-prepare-deploy"),
    )

    main_deploy_role = Role(
        resource_name="main-deploy-role",
        assume_role_policy=github_actions_assume_role_policy(config, github_oidc_provider.arn, "main-deploy"),
    )
    main_deploy_role.attach_read_only_access_role_policy()  # needed by pulumi to construct plans

    export("main-prepare-deploy-role-arn", main_prepare_deploy_role.arn)
    export("main-prepare-deploy-role-name", main_prepare_deploy_role.name)
    export("main-deploy-role-arn", main_deploy_role.arn)
    export("main-deploy-role-name", main_deploy_role.name)

    # DNS

    domain = config.require("domain")

    zone = Zone("main-zone", name=domain)

    certificate = Certificate(
        "main-certificate", domain_name=f"*.{domain}", subject_alternative_names=[domain], validation_method="DNS"
    )

    validation = certificate.domain_validation_options[0]

    validation_record = Record(
        "validation-record",
        zone_id=zone.id,
        name=validation.resource_record_name,
        type=validation.resource_record_type,
        records=[validation.resource_record_value],
        ttl=300,
    )

    CertificateValidation(
        "certValidation", certificate_arn=certificate.arn, validation_record_fqdns=[validation_record.fqdn]
    )

    export("zone-id", zone.id)
    export("zone-name", zone.name)
    export("zone-name-servers", zone.name_servers)
    export("certificate-arn", certificate.arn)

    # ECR Pull Through Cache Rules

    dockerhub_secret = Secret(
        "dockerhub-secret",
        name_prefix="ecr-pullthroughcache/",
        secret_string=Output.json_dumps({
            "username": config.require("dockerhub-user"),
            "accessToken": config.require_secret("dockerhub-password"),
        }),
    )

    ghcr_secret = Secret(
        "ghcr-secret",
        name_prefix="ecr-pullthroughcache/",
        secret_string=Output.json_dumps({
            "username": config.require("ghcr-user"),
            "accessToken": config.require_secret("ghcr-personal-access-token"),
        }),
    )

    PullThroughCacheRule(
        "dockerhub-pull-through-cache-rule",
        ecr_repository_prefix="dockerhub",
        upstream_registry_url="registry-1.docker.io",
        credential_arn=dockerhub_secret.arn,
    )

    PullThroughCacheRule(
        "ghcr-pull-through-cache-rule",
        ecr_repository_prefix="ghcr",
        upstream_registry_url="ghcr.io",
        credential_arn=ghcr_secret.arn,
    )

    PullThroughCacheRule("quay-pull-through-cache-rule", ecr_repository_prefix="quay", upstream_registry_url="quay.io")

    # Core Infrastructure

    vpc = Vpc(name="main-vpc")

    NatInstance("main-nat", vpc=vpc)

    rds = RDSInstance("rds", config=config, vpc=vpc)

    cluster = Cluster("core-cluster")

    auth_gateway = AuthGateway(
        resource_name="auth-gateway",
        config=config,
        vpc=vpc,
        zone_id=zone.id,
        zone_name=zone.name,
        certificate_arn=certificate.arn,
        cluster=cluster,
        deploy_role=main_deploy_role,
        prepare_deploy_role=main_prepare_deploy_role,
    )

    oauth = Oauth(
        "cloudbeaver-oauth",
        config=config,
        proxy_image_repo_name=auth_gateway.proxy_image_repo_name,
        reverse_proxy_image_repo_name=auth_gateway.reverse_proxy_image_repo_name,
        client_id_secret_arn=auth_gateway.client_id_secret_arn,
        client_secret_secret_arn=auth_gateway.client_secret_secret_arn,
        cookie_secret_secret_arn=auth_gateway.cookie_secret_secret_arn,
    )

    cloudbeaver = Cloudbeaver(
        resource_name="cloudbeaver",
        config=config,
        zone_name=zone.name,
        zone_id=zone.id,
        certificate_arn=certificate.arn,
        vpc=vpc,
        rds=rds,
        cluster=cluster,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
        oauth=oauth,
    )

    DatabaseManager(
        resource_name="database-manager",
        config=config,
        vpc=vpc,
        efs=cloudbeaver.efs,
        rds=rds,
        ecs_cluster_arn=cluster.arn,
        cloudbeaver_service_arn=cloudbeaver.service_arn,
        prepare_deploy_role=main_prepare_deploy_role,
        deploy_role=main_deploy_role,
    )

    TailscaleBeacon(
        resource_name="tailscale-beacon",
        config=config,
        vpc=vpc,
        zone_id=zone.id,
        domain=domain,
        certificate_arn=certificate.arn,
        cluster=cluster,
        deploy_role=main_deploy_role,
        prepare_deploy_role=main_prepare_deploy_role,
        rds_security_group=rds.security_group,
    )
