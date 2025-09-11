from pulumi import ComponentResource, Config, ResourceOptions, export
from pulumi_aws.rds import Instance, SubnetGroup

from components.secret import Secret
from components.security_group import SecurityGroup
from components.vpc import Vpc


class RDSInstance(ComponentResource):
    def __init__(self, resource_name: str, config: Config, vpc: Vpc, *, opts: ResourceOptions | None = None):
        super().__init__("custom:RDSInstance", resource_name, opts=opts)

        self._resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        username: str = config.require("postgres-user")
        password = config.require_secret("postgres-password")

        subnet_group = SubnetGroup(resource_name="db-subnet-group", subnet_ids=vpc.private_subnet_ids)

        self.security_group = SecurityGroup("postgres-security-group", vpc=vpc)

        self.instance = Instance(
            "postgres",
            db_name="postgres",
            engine="postgres",
            engine_version="15",
            instance_class="db.t3.micro",
            allocated_storage=20,
            db_subnet_group_name=subnet_group.id,
            vpc_security_group_ids=[self.security_group.id],
            username=username,
            password=password,
            skip_final_snapshot=True,
            opts=self._child_opts,
        )

        self.password_secret = Secret("postgres-secret", secret_string=password, opts=self._child_opts)

        self.address = self.instance.address

        export("rds-address", self.address)
        export("rds-security-group-id", self.security_group.id)

        self.register_outputs({"address": self.address})
