from typing import Sequence

from pulumi import ComponentResource, Config, Input, Output, ResourceOptions
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService
from pulumi_awsx.ecs._inputs import TaskDefinitionKeyValuePairArgsDict

from components.load_balancer import LoadBalancer
from components.log import log_configuration
from components.oauth import Oauth
from components.role import Role
from components.roles import ecs_execution_role, ecs_role
from components.security_group import SecurityGroup
from components.vpc import Vpc


class AuthGateway(ComponentResource):
    def __init__(
        self,
        resource_name: str,
        config: Config,
        zone_id: Input[str],
        zone_name: Input[str],
        certificate_arn: Input[str],
        vpc: Vpc,
        cluster: Cluster,
        prepare_deploy_role: Role,
        deploy_role: Role,
        *,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:AuthGateway", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        # Logs groups
        auth_gateway_log_group = LogGroup(
            "auth-gateway-log-group", name="/ecs/auth-gateway", retention_in_days=7, opts=self._child_opts
        )

        self.oauth = Oauth(
            resource_name="auth-gateway-oauth",
            config=config,
            zone_name=zone_name,
            prepare_deploy_role=prepare_deploy_role,
            opts=self._child_opts,
        )

        # Security Groups
        oauth_security_group = SecurityGroup(
            "oauth-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            opts=self._child_opts,
        )

        load_balancer_security_group = SecurityGroup(
            "oauth-load-balancer-security-group",
            vpc=vpc,
            rules=[
                {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
                {"to_security_group": oauth_security_group, "ports": [4180]},
            ],
            opts=self._child_opts,
        )

        # Load Balancer
        load_balancer = LoadBalancer(
            "oauth-loadbalancer",
            "oauth",
            vpc=vpc,
            securityGroup=load_balancer_security_group,
            certificate_arn=certificate_arn,
            port=4180,
            health_check={
                "path": "/ping",
                "protocol": "HTTP",
                "interval": 15,
                "healthy_threshold": 2,
                "unhealthy_threshold": 10,
            },
            opts=self._child_opts,
        )

        # DNS Record
        domain = Output.concat("auth.", zone_name)
        Record(
            "oauth-domain-record",
            zone_id=zone_id,
            name=domain,
            type="A",
            aliases=[
                {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = ecs_execution_role("oauth-execution-role", opts=self._child_opts)
        execution_role.allow_secret_get([
            self.oauth.client_id_secret,
            self.oauth.client_secret_secret,
            self.oauth.cookie_secret_secret,
        ])

        # Task Role
        task_role = ecs_role("oauth-task-role", opts=self._child_opts)

        # Environment
        environment: Sequence[Input[TaskDefinitionKeyValuePairArgsDict]] = [
            {"name": "OAUTH2_PROXY_HTTP_ADDRESS", "value": "0.0.0.0:4180"},
            {"name": "OAUTH2_PROXY_PROVIDER", "value": "github"},
            {
                "name": "OAUTH2_PROXY_REDIRECT_URL",
                "value": domain.apply(lambda domain: f"https://{domain}/oauth2/callback"),
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
            environment.append({"name": "OAUTH2_PROXY_GITHUB_USER", "value": allowed_users})

        github_org = config.get("oauth-org")
        if github_org:
            environment.append({"name": "OAUTH2_PROXY_GITHUB_ORG", "value": github_org})

        github_team = config.get("oauth-team")
        if github_team:
            environment.append({"name": "OAUTH2_PROXY_GITHUB_TEAM", "value": github_team})

        # Service
        service = FargateService(
            "oauth-service",
            name="oauth-service",
            cluster=cluster.arn,
            desired_count=1,
            network_configuration={"subnets": vpc.private_subnet_ids, "security_groups": [oauth_security_group.id]},
            task_definition_args={
                "execution_role": {"role_arn": execution_role.arn},
                "task_role": {"role_arn": task_role.arn},
                "containers": {
                    "oauth2-proxy": {
                        "name": "oauth2-proxy",
                        "image": self.oauth.image_repo.locked_digest(),
                        "log_configuration": log_configuration(auth_gateway_log_group),
                        "port_mappings": [
                            {"container_port": 4180, "host_port": 4180, "target_group": load_balancer.target_group}
                        ],
                        "environment": environment,
                        "secrets": [
                            {"name": "OAUTH2_PROXY_CLIENT_ID", "value_from": self.oauth.client_id_secret.arn},
                            {"name": "OAUTH2_PROXY_CLIENT_SECRET", "value_from": self.oauth.client_secret_secret.arn},
                            {"name": "OAUTH2_PROXY_COOKIE_SECRET", "value_from": self.oauth.cookie_secret_secret.arn},
                        ],
                    }
                },
            },
            opts=self._child_opts,
        )

        # Allow service deployment
        deploy_role.allow_service_deployment(
            "auth-gateway", passroles=[execution_role, task_role], services=[service.service]
        )
