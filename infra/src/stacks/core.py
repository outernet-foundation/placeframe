import json

from pulumi import Config, Output, export
from pulumi_aws.ecr import PullThroughCacheRule

from components.secret import Secret
from components.vpc import Vpc, VpcInfo


def create_core_stack(config: Config):
    # oidc_provider = aws.iam.OpenIdConnectProvider(
    #     "github-oidc-provider", url="https://token.actions.githubusercontent.com", client_id_lists=["sts.amazonaws.com"]
    # )

    # trust_policy = pulumi.Output.all(oidc_provider.arn).apply(
    #     lambda arn: json.dumps({
    #         "Version": "2012-10-17",
    #         "Statement": [
    #             {
    #                 "Effect": "Allow",
    #                 "Principal": {"Federated": arn[0]},
    #                 "Action": "sts:AssumeRoleWithWebIdentity",
    #                 "Condition": {
    #                     "StringEquals": {f"{oidc_provider.url}:aud": "sts.amazonaws.com"},
    #                     "StringLike": {
    #                         f"{oidc_provider.url}:sub": [
    #                             "repo:outernet-foundation/plerion:refs/heads/main",
    #                             "repo:outernet-foundation/plerion:refs/heads/env/*",
    #                         ]
    #                     },
    #                 },
    #             }
    #         ],
    #     })
    # )

    # ci_role = aws.iam.Role("ci-role", assume_role_policy=trust_policy)

    # aws.iam.RolePolicyAttachment(
    #     "ci-role-ecr", role=ci_role.name, policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
    # )

    # aws.iam.RolePolicyAttachment(
    #     "ci-role-ecs", role=ci_role.name, policy_arn="arn:aws:iam::aws:policy/AmazonECS_FullAccess"
    # )

    # aws.iam.RolePolicyAttachment(
    #     "ci-role-pulumi", role=ci_role.name, policy_arn="arn:aws:iam::aws:policy/AdministratorAccess"
    # )

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

    vpc = Vpc(name="main-vpc")
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
