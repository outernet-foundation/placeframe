from typing import Sequence, overload

from pulumi import ComponentResource, Config, Input, Output, ResourceOptions, export
from pulumi_awsx.ecs._inputs import TaskDefinitionKeyValuePairArgsDict

from components.repository import Repository
from components.role import Role
from components.secret import Secret


class Oauth(ComponentResource):
    @overload
    def __init__(
        self,
        resource_name: str,
        config: Config,
        zone_name: Input[str],
        *,
        prepare_deploy_role: Role,
        opts: ResourceOptions | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        resource_name: str,
        config: Config,
        zone_name: Input[str],
        *,
        image_repo_name: Input[str],
        client_id_secret_arn: Input[str],
        client_secret_secret_arn: Input[str],
        cookie_secret_secret_arn: Input[str],
        opts: ResourceOptions | None = None,
    ) -> None: ...

    def __init__(
        self,
        resource_name: str,
        config: Config,
        zone_name: Input[str],
        *,
        prepare_deploy_role: Role | None = None,
        image_repo_name: Input[str] | None = None,
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
                "oauth-client-id", secret_string=config.require_secret("oauth-client-id"), opts=self._child_opts
            )
            self.client_secret_secret = Secret(
                "oauth-client-secret", secret_string=config.require_secret("oauth-client-secret"), opts=self._child_opts
            )
            # python -c 'import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())'
            self.cookie_secret_secret = Secret(
                "oauth-cookie-secret", secret_string=config.require_secret("oauth-cookie-secret"), opts=self._child_opts
            )

            # Image repo
            self.image_repo = Repository(
                "oauth2-proxy-repo",
                "quay/oauth2-proxy/oauth2-proxy",
                opts=ResourceOptions.merge(
                    self._child_opts,
                    ResourceOptions(
                        retain_on_delete=True
                        # import_="quay.io/oauth2-proxy/oauth2-proxy",
                    ),
                ),
            )
            prepare_deploy_role.allow_image_repo_actions([self.image_repo])
            export("oauth2-proxy-image-repo-url", self.image_repo.url)

        # adopt branch
        else:
            assert image_repo_name is not None
            assert client_id_secret_arn is not None
            assert client_secret_secret_arn is not None
            assert cookie_secret_secret_arn is not None

            self.client_id_secret = Secret("oauth-client-id", arn=client_id_secret_arn, opts=self._child_opts)
            self.client_secret_secret = Secret(
                "oauth-client-secret", arn=client_secret_secret_arn, opts=self._child_opts
            )
            self.cookie_secret_secret = Secret(
                "oauth-cookie-secret", arn=cookie_secret_secret_arn, opts=self._child_opts
            )
            self.image_repo = Repository("oauth2-proxy-repo", name=image_repo_name, adopt=True, opts=self._child_opts)

        # Environment
        self.environment: Sequence[Input[TaskDefinitionKeyValuePairArgsDict]] = [
            {"name": "OAUTH2_PROXY_HTTP_ADDRESS", "value": "0.0.0.0:4180"},
            {"name": "OAUTH2_PROXY_PROVIDER", "value": "github"},
            {
                "name": "OAUTH2_PROXY_REDIRECT_URL",
                "value": Output.concat("https://auth.", zone_name, "/oauth2/callback"),
            },
            {"name": "OAUTH2_PROXY_EMAIL_DOMAINS", "value": "*"},
            {"name": "OAUTH2_PROXY_UPSTREAMS", "value": "static://200"},
            {"name": "OAUTH2_PROXY_COOKIE_SECURE", "value": "true"},
            {"name": "OAUTH2_PROXY_COOKIE_SAMESITE", "value": "lax"},
            {"name": "OAUTH2_PROXY_REVERSE_PROXY", "value": "true"},
            {"name": "OAUTH2_PROXY_SET_XAUTHREQUEST", "value": "true"},
            {"name": "OAUTH2_PROXY_PASS_AUTHORIZATION_HEADER", "value": "true"},
            {"name": "OAUTH2_PROXY_COOKIE_DOMAINS", "value": Output.concat(".", zone_name)},
            {"name": "OAUTH2_PROXY_WHITELIST_DOMAIN", "value": Output.concat(".", zone_name)},
        ]

        # Allow-lists
        allowed_users = config.get("oauth-allowed-users")
        if allowed_users:
            self.environment.append({"name": "OAUTH2_PROXY_GITHUB_USER", "value": allowed_users})

        github_org = config.get("oauth-org")
        if github_org:
            self.environment.append({"name": "OAUTH2_PROXY_GITHUB_ORG", "value": github_org})

        github_team = config.get("oauth-team")
        if github_team:
            self.environment.append({"name": "OAUTH2_PROXY_GITHUB_TEAM", "value": github_team})
