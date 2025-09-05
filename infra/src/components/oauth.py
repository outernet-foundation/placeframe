from typing import Sequence, overload

from pulumi import ComponentResource, Config, Input, Output, ResourceOptions, export
from pulumi_aws.cloudwatch import LogGroup
from pulumi_awsx.ecs._inputs import (
    TaskDefinitionContainerDefinitionArgsDict,
    TaskDefinitionKeyValuePairArgsDict,
    TaskDefinitionPortMappingArgsDict,
)

from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.repository import Repository
from components.role import Role
from components.secret import Secret


class Oauth(ComponentResource):
    @overload
    def __init__(
        self, resource_name: str, config: Config, *, prepare_deploy_role: Role, opts: ResourceOptions | None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        resource_name: str,
        config: Config,
        *,
        proxy_image_repo_name: Input[str],
        reverse_proxy_image_repo_name: Input[str],
        client_id_secret_arn: Input[str],
        client_secret_secret_arn: Input[str],
        cookie_secret_secret_arn: Input[str],
        opts: ResourceOptions | None = None,
    ) -> None: ...

    def __init__(
        self,
        resource_name: str,
        config: Config,
        *,
        prepare_deploy_role: Role | None = None,
        proxy_image_repo_name: Input[str] | None = None,
        reverse_proxy_image_repo_name: Input[str] | None = None,
        client_id_secret_arn: Input[str] | None = None,
        client_secret_secret_arn: Input[str] | None = None,
        cookie_secret_secret_arn: Input[str] | None = None,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:Oauth", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # non-adopt branch
        if prepare_deploy_role is not None:
            # Secrets
            self.client_id_secret = Secret(
                "oauth2-client-id", secret_string=config.require_secret("oauth2-client-id"), opts=self._child_opts
            )
            self.client_secret_secret = Secret(
                "oauth2-client-secret",
                secret_string=config.require_secret("oauth2-client-secret"),
                opts=self._child_opts,
            )
            # python -c 'import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())'
            self.cookie_secret_secret = Secret(
                "oauth2-cookie-secret",
                secret_string=config.require_secret("oauth2-cookie-secret"),
                opts=self._child_opts,
            )

            # Image repos
            self.proxy_image_repo = Repository(
                "oauth2-proxy-repo",
                name="quay/oauth2-proxy/oauth2-proxy",
                opts=ResourceOptions.merge(
                    self._child_opts,
                    ResourceOptions(
                        retain_on_delete=True
                        # import_="quay.io/oauth2-proxy/oauth2-proxy",
                    ),
                ),
            )
            self.reverse_proxy_image_repo = Repository(
                "oauth2-reverse-proxy-repo",
                name="oauth2-reverse-proxy",
                opts=ResourceOptions.merge(
                    self._child_opts,
                    ResourceOptions(
                        retain_on_delete=True
                        # import_="oauth2-reverse-proxy",
                    ),
                ),
            )

            prepare_deploy_role.allow_image_repo_actions([self.proxy_image_repo, self.reverse_proxy_image_repo])
            export("oauth2-proxy-image-repo-url", self.proxy_image_repo.url)
            export("oauth2-reverse-proxy-image-repo-url", self.reverse_proxy_image_repo.url)

        # adopt branch
        else:
            assert proxy_image_repo_name is not None
            assert reverse_proxy_image_repo_name is not None
            assert client_id_secret_arn is not None
            assert client_secret_secret_arn is not None
            assert cookie_secret_secret_arn is not None

            self.client_id_secret = Secret("oauth2-client-id", arn=client_id_secret_arn, opts=self._child_opts)
            self.client_secret_secret = Secret(
                "oauth2-client-secret", arn=client_secret_secret_arn, opts=self._child_opts
            )
            self.cookie_secret_secret = Secret(
                "oauth2-cookie-secret", arn=cookie_secret_secret_arn, opts=self._child_opts
            )
            self.proxy_image_repo = Repository(
                "oauth2-proxy-repo", name=proxy_image_repo_name, adopt=True, opts=self._child_opts
            )
            self.reverse_proxy_image_repo = Repository(
                "oauth2-reverse-proxy-repo", name=reverse_proxy_image_repo_name, adopt=True, opts=self._child_opts
            )

    def proxy_task_definition(
        self,
        config: Config,
        zone_name: Input[str],
        log_group: LogGroup,
        proxy_upstreams: Input[str],
        load_balancer: LoadBalancer | None = None,  # load balancer provided only for the auth gateway
    ):
        # Environment
        environment: Sequence[Input[TaskDefinitionKeyValuePairArgsDict]] = [
            {"name": "OAUTH2_PROXY_HTTP_ADDRESS", "value": "0.0.0.0:4180"},
            {"name": "OAUTH2_PROXY_PROVIDER", "value": "github"},
            {
                "name": "OAUTH2_PROXY_REDIRECT_URL",
                "value": Output.concat("https://auth.", zone_name, "/oauth2/callback"),
            },
            # {"name": "OAUTH2_PROXY_SKIP_PROVIDER_BUTTON", "value": "true"},
            # {"name": "OAUTH2_PROXY_PASS_HOST_HEADER", "value": "true"},
            {"name": "OAUTH2_PROXY_UPSTREAMS", "value": proxy_upstreams},
            {"name": "OAUTH2_PROXY_EMAIL_DOMAINS", "value": "*"},
            # {"name": "OAUTH2_PROXY_COOKIE_SECURE", "value": "true"},
            # {"name": "OAUTH2_PROXY_COOKIE_SAMESITE", "value": "lax"},
            {"name": "OAUTH2_PROXY_REVERSE_PROXY", "value": "true"},
            # {"name": "OAUTH2_PROXY_SET_XAUTHREQUEST", "value": "true"},
            # {"name": "OAUTH2_PROXY_PASS_AUTHORIZATION_HEADER", "value": "true"},
            {"name": "OAUTH2_PROXY_COOKIE_DOMAINS", "value": Output.concat(".", zone_name)},
            {"name": "OAUTH2_PROXY_WHITELIST_DOMAINS", "value": Output.concat(".", zone_name)},
            {"name": "OAUTH2_PROXY_SCOPE", "value": "read:user,user:email,read:org"},
            {"name": "OAUTH2_PROXY_GITHUB_ORG", "value": config.require("oauth2-allowed-org")},
        ]

        port_mapping: TaskDefinitionPortMappingArgsDict = {"container_port": 4180, "host_port": 4180}

        if not load_balancer:
            # If this is not the auth gateway, we need to set some additional environment variables
            environment.extend([
                {"name": "OAUTH2_PROXY_PASS_ACCESS_TOKEN", "value": "true"},
                {"name": "OAUTH2_PROXY_COOKIE_REFRESH", "value": "1h"},
                {"name": "OAUTH2_PROXY_COOKIE_EXPIRE", "value": "168h"},
            ])
        else:
            port_mapping["target_group"] = load_balancer.target_group

        task_definition: TaskDefinitionContainerDefinitionArgsDict = {
            "name": "oauth2-proxy",
            "image": self.proxy_image_repo.locked_digest(),
            "log_configuration": log_configuration(log_group),
            "port_mappings": [port_mapping],
            "environment": environment,
            "secrets": [
                {"name": "OAUTH2_PROXY_CLIENT_ID", "value_from": self.client_id_secret.arn},
                {"name": "OAUTH2_PROXY_CLIENT_SECRET", "value_from": self.client_secret_secret.arn},
                {"name": "OAUTH2_PROXY_COOKIE_SECRET", "value_from": self.cookie_secret_secret.arn},
            ],
        }

        return task_definition

    def reverse_proxy_task_definition(self, log_group: LogGroup, load_balancer: LoadBalancer):
        task_definition: TaskDefinitionContainerDefinitionArgsDict = {
            "name": "oauth2-reverse-proxy",
            "image": self.reverse_proxy_image_repo.locked_digest(),
            "log_configuration": log_configuration(log_group),
            "port_mappings": [{"container_port": 4181, "host_port": 4181, "target_group": load_balancer.target_group}],
            "environment": [{"name": "UPSTREAM", "value": "127.0.0.1:4180"}],
        }

        return task_definition
