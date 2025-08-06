import json

from pulumi import Config, export
from pulumi_aws.acm import Certificate, CertificateValidation
from pulumi_aws.ecr import PullThroughCacheRule
from pulumi_aws.ecs import Cluster
from pulumi_aws.route53 import Record, Zone

from components.secret import Secret
from components.tailscale_beacon import create_tailscale_beacon
from components.vpc import Vpc, VpcInfo


def create_core_stack(config: Config):
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
        secret_string=config.require_secret("dockerhub-password").apply(
            lambda access_token: json.dumps({"username": config.require("dockerhub-user"), "accessToken": access_token})
        ),
    )

    PullThroughCacheRule(
        "dockerhub-pull-through-cache-rule",
        ecr_repository_prefix="dockerhub",
        upstream_registry_url="registry-1.docker.io",
        credential_arn=dockerhub_secret.arn,
    )

    vpc = Vpc(name="main-vpc")

    cluster = Cluster("core-tooling-cluster")

    create_tailscale_beacon(
        vpc=vpc, config=config, zone_id=zone.id, domain=domain, certificate_arn=certificate.arn, cluster=cluster
    )

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
