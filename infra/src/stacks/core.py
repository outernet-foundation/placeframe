import json

from pulumi import Config, Output, export
from pulumi_aws.acm import Certificate, CertificateValidation
from pulumi_aws.ecr import PullThroughCacheRule
from pulumi_aws.ecs import Cluster
from pulumi_aws.iam import OpenIdConnectProvider, Role, RolePolicyAttachment
from pulumi_aws.route53 import Record, Zone

from components.secret import Secret
from components.tailscale_beacon import create_tailscale_beacon
from components.vpc import Vpc, VpcInfo


def create_core_stack(config: Config):
    # 1) Create the GitHub OIDC provider (if you haven’t already)
    github_oidc = OpenIdConnectProvider(
        "githubOidcProvider",
        url="https://token.actions.githubusercontent.com",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],
    )

    # 2) Create an IAM role that trusts that provider on your main branch
    oidc_role = Role(
        "githubActionsRole",
        assume_role_policy=Output.all(github_oidc.arn).apply(
            lambda arn: json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Federated": arn},
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringLike": {
                                # adjust repo & branch as needed
                                "token.actions.githubusercontent.com:sub": "repo:myOrg/myRepo:ref:refs/heads/main"
                            }
                        },
                    }
                ],
            })
        ),
    )

    # 3) Attach whatever policies you need, e.g. full Pulumi permissions
    RolePolicyAttachment("pulumiAccess", role=oidc_role.name, policy_arn="arn:aws:iam::aws:policy/PowerUserAccess")

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
        secret_string=Output.all(config.require("dockerhub-user"), config.require_secret("dockerhub-password")).apply(
            lambda args: json.dumps({"username": args[0], "accessToken": args[1]})
        ),
    )

    PullThroughCacheRule(
        "dockerhub-pull-through-cache-rule",
        ecr_repository_prefix="dockerhub",
        upstream_registry_url="registry-1.docker.io",
        credential_arn=dockerhub_secret.arn,
    )

    ghcr_secret = Secret(
        "ghcr-secret",
        name_prefix="ecr-pullthroughcache/",
        secret_string=Output.all(config.require("github-username"), config.require_secret("github-pat")).apply(
            lambda args: json.dumps({"username": args[0], "accessToken": args[1]})
        ),
    )

    PullThroughCacheRule(
        "ghcr-pull-through-cache-rule",
        ecr_repository_prefix="ghcr",
        upstream_registry_url="ghcr.io",
        credential_arn=ghcr_secret.arn,
    )

    vpc = Vpc(name="main-vpc")

    cluster = Cluster("core-tooling-cluster")

    create_tailscale_beacon(
        vpc=vpc, config=config, zone_id=zone.id, domain=domain, certificate_arn=certificate.arn, cluster=cluster
    )

    export("github_actions_role_arn", oidc_role.arn)
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
