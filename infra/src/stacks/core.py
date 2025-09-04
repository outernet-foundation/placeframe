from pulumi import Config, Output, export
from pulumi_aws.acm import Certificate, CertificateValidation
from pulumi_aws.ecr import PullThroughCacheRule
from pulumi_aws.ecs import Cluster
from pulumi_aws.iam import OpenIdConnectProvider
from pulumi_aws.route53 import Record, Zone

from components.role import Role
from components.roles import github_actions_assume_role_policy
from components.secret import Secret
from components.vpc import Vpc, VpcInfo
from services.auth_gateway import AuthGateway
from services.tailscale_beacon import TailscaleBeacon


def create_core_stack(config: Config):
    github_oidc_provider = OpenIdConnectProvider(
        "github-oidc-provider",
        url="https://token.actions.githubusercontent.com",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],  # GitHub OIDC thumbprint
    )

    main_prepare_deploy_role = Role(
        resource_name="main-prepare-deploy-role",
        assume_role_policy=github_actions_assume_role_policy(config, github_oidc_provider.arn, "main-prepare-deploy"),
    )

    main_deploy_role = Role(
        resource_name="main-deploy-role",
        assume_role_policy=github_actions_assume_role_policy(config, github_oidc_provider.arn, "main-deploy"),
    )
    main_deploy_role.attach_read_only_access_role_policy()  # needed by pulumi to construct plans

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

    dockerhub_secret = Secret(
        "dockerhub-secret",
        name_prefix="ecr-pullthroughcache/",
        secret_string=Output.json_dumps({
            "username": config.require("dockerhub-user"),
            "accessToken": config.require_secret("dockerhub-password"),
        }),
    )

    PullThroughCacheRule(
        "dockerhub-pull-through-cache-rule",
        ecr_repository_prefix="dockerhub",
        upstream_registry_url="registry-1.docker.io",
        credential_arn=dockerhub_secret.arn,
    )

    PullThroughCacheRule("quay-pull-through-cache-rule", ecr_repository_prefix="quay", upstream_registry_url="quay.io")

    vpc = Vpc(name="main-vpc")

    cluster = Cluster("core-tooling-cluster")

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
    )

    export("main-prepare-deploy-role-arn", main_prepare_deploy_role.arn)
    export("main-prepare-deploy-role-name", main_prepare_deploy_role.name)
    export("main-deploy-role-arn", main_deploy_role.arn)
    export("main-deploy-role-name", main_deploy_role.name)
    export("zone-id", zone.id)
    export("zone-name", zone.name)
    export("zone-name-servers", zone.name_servers)
    export("certificate-arn", certificate.arn)
    export(
        "vpc-info",
        VpcInfo({
            "id": vpc.id,
            "cidr_block": vpc.cidr_block,
            "private_subnet_ids": vpc.private_subnet_ids,
            "public_subnet_ids": vpc.public_subnet_ids,
            "interface_security_group_ids": {service: sg.id for service, sg in vpc.interface_security_groups.items()},
            "s3_endpoint_prefix_list_id": vpc.s3_endpoint_prefix_list_id,
        }),
    )
    export("oauth2-proxy-image-repo-name", auth_gateway.proxy_image_repo_name)
    export("oauth2-reverse-proxy-image-repo-name", auth_gateway.reverse_proxy_image_repo_name)
    export("oauth2-client-id-secret-arn", auth_gateway.client_id_secret_arn)
    export("oauth2-client-secret-secret-arn", auth_gateway.client_secret_secret_arn)
    export("oauth2-cookie-secret-secret-arn", auth_gateway.cookie_secret_secret_arn)
