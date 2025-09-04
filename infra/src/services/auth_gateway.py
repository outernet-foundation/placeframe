from pulumi import ComponentResource, Config, Input, Output, ResourceOptions
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ecs import Cluster
from pulumi_aws.route53 import Record
from pulumi_awsx.ecs import FargateService

from components.load_balancer import LoadBalancer
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
            prepare_deploy_role=prepare_deploy_role,
            opts=self._child_opts,
        )

        # Security Groups
        oauth_security_group = SecurityGroup(
            "auth-gateway-security-group",
            vpc=vpc,
            vpc_endpoints=["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts", "s3"],
            rules=[
                # allow HTTPS egress to the Internet (goes via your NAT if in private subnets)
                {"cidr_name": "anywhere", "to_cidr": "0.0.0.0/0", "ports": [443]}
            ],
            opts=self._child_opts,
        )

        load_balancer_security_group = SecurityGroup(
            "auth-gateway-load-balancer-security-group",
            vpc=vpc,
            rules=[
                {"cidr_name": "anywhere", "from_cidr": "0.0.0.0/0", "ports": [80, 443]},
                {"to_security_group": oauth_security_group, "ports": [4180]},
            ],
            opts=self._child_opts,
        )

        # Load Balancer
        load_balancer = LoadBalancer(
            "auth-gateway-loadbalancer",
            "auth-gateway",
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
            "auth-gateway-domain-record",
            zone_id=zone_id,
            name=domain,
            type="A",
            aliases=[
                {"name": load_balancer.dns_name, "zone_id": load_balancer.zone_id, "evaluate_target_health": True}
            ],
            opts=self._child_opts,
        )

        # Execution role
        execution_role = ecs_execution_role("auth-gateway-execution-role", opts=self._child_opts)
        execution_role.allow_secret_get(
            "auth-gateway-secrets",
            [self.oauth.client_id_secret, self.oauth.client_secret_secret, self.oauth.cookie_secret_secret],
        )

        # Task Role
        task_role = ecs_role("auth-gateway-task-role", opts=self._child_opts)

        # Service
        service = FargateService(
            "auth-gateway-service",
            name="auth-gateway-service",
            cluster=cluster.arn,
            desired_count=1,
            network_configuration={"subnets": vpc.private_subnet_ids, "security_groups": [oauth_security_group.id]},
            task_definition_args={
                "execution_role": {"role_arn": execution_role.arn},
                "task_role": {"role_arn": task_role.arn},
                "containers": {
                    "oauth2-proxy": self.oauth.proxy_task_definition(
                        config=config,
                        zone_name=zone_name,
                        log_group=auth_gateway_log_group,
                        load_balancer=load_balancer,
                        proxy_upstreams="static://200",
                    )
                },
            },
            opts=self._child_opts,
        )

        # Allow service deployment
        deploy_role.allow_service_deployment(
            "auth-gateway", passroles=[execution_role, task_role], services=[service.service]
        )

        self.proxy_image_repo_name = self.oauth.proxy_image_repo.name
        self.reverse_proxy_image_repo_name = self.oauth.reverse_proxy_image_repo.name
        self.client_id_secret_arn = self.oauth.client_id_secret.arn
        self.client_secret_secret_arn = self.oauth.client_secret_secret.arn
        self.cookie_secret_secret_arn = self.oauth.cookie_secret_secret.arn

        self.register_outputs({
            "proxy_image_repo_name": self.proxy_image_repo_name,
            "reverse_proxy_image_repo_name": self.reverse_proxy_image_repo_name,
            "client_id_secret_arn": self.client_id_secret_arn,
            "client_secret_secret_arn": self.client_secret_secret_arn,
            "cookie_secret_secret_arn": self.cookie_secret_secret_arn,
        })
