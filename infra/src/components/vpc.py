from typing import Dict, Sequence, TypedDict, overload

import pulumi
import pulumi_awsx
from pulumi import ComponentResource, Input, Output, ResourceOptions
from pulumi_aws import get_region_output
from pulumi_aws.ec2 import VpcEndpoint, get_route_table_output
from pulumi_awsx.ec2 import NatGatewayStrategy, SubnetAllocationStrategy

from components.security_group import SecurityGroup


class VpcInfo(TypedDict):
    id: Input[str]
    cidr_block: Input[str]
    private_subnet_ids: Input[Sequence[str]]
    public_subnet_ids: Input[Sequence[str]]
    interface_security_group_ids: Dict[str, Input[str]]
    s3_endpoint_prefix_list_id: Input[str]


class Vpc(ComponentResource):
    @overload
    def __init__(self, name: str, *, opts: ResourceOptions | None = None) -> None: ...
    @overload
    def __init__(self, name: str, *, vpc_info: Input[VpcInfo], opts: ResourceOptions | None = None) -> None: ...

    def __init__(
        self, name: str, *, vpc_info: Input[VpcInfo] | None = None, opts: pulumi.ResourceOptions | None = None
    ):
        super().__init__("custom:Vpc", name, opts=opts)

        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))
        self._vpc: pulumi_awsx.ec2.Vpc | None = None

        self.name = name
        self.interface_security_groups: Dict[str, SecurityGroup] = {}

        vpc_info_out = Output.from_input(vpc_info) if vpc_info is not None else None

        if vpc_info_out is not None:
            self.id = vpc_info_out.apply(lambda info: info["id"])
            self.cidr_block = vpc_info_out.apply(lambda info: info["cidr_block"])
            self.private_subnet_ids = vpc_info_out.apply(lambda info: info["private_subnet_ids"])
            self.public_subnet_ids = vpc_info_out.apply(lambda info: info["public_subnet_ids"])
            self.s3_endpoint_prefix_list_id = vpc_info_out.apply(lambda info: info["s3_endpoint_prefix_list_id"])
        else:
            self._vpc: pulumi_awsx.ec2.Vpc | None = pulumi_awsx.ec2.Vpc(
                f"{name}-vpc",
                number_of_availability_zones=2,  # Minimum of 2 AZs required for RDS and ECS
                # Let AWS assign DNS hostnames within the VPC (needed so tasks, ENIs, and private‑DNS endpoints resolve correctly)
                enable_dns_hostnames=True,
                # Don't create any NAT Gateways; we don't need them and they cost money.
                nat_gateways={"strategy": NatGatewayStrategy.NONE},
                # This will be the default in the future, but for now we need to explicitly set it
                subnet_strategy=SubnetAllocationStrategy.AUTO,
                opts=self._child_opts,
            )

            self.id = self._vpc.vpc_id
            self.cidr_block = self._vpc.vpc.cidr_block
            self.private_subnet_ids = self._vpc.private_subnet_ids
            self.public_subnet_ids = self._vpc.public_subnet_ids

        for service_name in ["ecr.api", "ecr.dkr", "secretsmanager", "logs", "sts"]:
            sanitized_name = service_name.replace(".", "-")
            security_group_name = f"{sanitized_name}-security-group"
            if vpc_info_out is not None:
                self.interface_security_groups[service_name] = SecurityGroup(
                    security_group_name,
                    security_group_id=vpc_info_out.apply(
                        lambda info, svc=service_name: info["interface_security_group_ids"][svc]
                    ),
                    opts=self._child_opts,
                )
            elif self._vpc is not None:
                security_group = SecurityGroup(security_group_name, vpc_id=self._vpc.vpc_id, opts=self._child_opts)
                VpcEndpoint(
                    f"{sanitized_name}-endpoint",
                    vpc_id=self._vpc.vpc_id,
                    service_name=pulumi.Output.concat("com.amazonaws.", get_region_output().name, ".", service_name),
                    vpc_endpoint_type="Interface",
                    subnet_ids=self._vpc.private_subnet_ids.apply(
                        lambda ids: [ids[0]]
                    ),  # Only create endpoint in one subnet to reduce costs
                    security_group_ids=[security_group.id],
                    private_dns_enabled=True,
                    opts=self._child_opts,
                )

                self.interface_security_groups[service_name] = security_group

        if self._vpc is not None:
            # Maybe switch to this?
            # route_table_ids = pulumi.Output.all(self.vpc.private_subnet_ids, self.vpc.route_table_associations).apply(
            #     lambda subs_and_assocs: [
            #         assoc.route_table_id for assoc in subs_and_assocs[1] if assoc.subnet_id in subs_and_assocs[0]
            #     ]
            # )

            # Create a VPC endpoint for S3 (gateway type rather than interface type, no security group)
            s3_endpoint = VpcEndpoint(
                "s3-gateway-endpoint",
                vpc_id=self._vpc.vpc_id,
                service_name=pulumi.Output.concat("com.amazonaws.", get_region_output().name, ".s3"),
                vpc_endpoint_type="Gateway",
                route_table_ids=self._vpc.private_subnet_ids.apply(
                    lambda ids: [get_route_table_output(subnet_id=subnet_id).id for subnet_id in ids]
                ),
                opts=self._child_opts,
            )

            self.s3_endpoint_prefix_list_id = s3_endpoint.prefix_list_id

        self.register_outputs({
            "vpc_id": self.id,
            "cidr_block": self.cidr_block,
            "private_subnet_ids": self.private_subnet_ids,
            "public_subnet_ids": self.public_subnet_ids,
            "s3_endpoint_prefix_list_id": self.s3_endpoint_prefix_list_id,
            "interface_security_group_ids": {service: sg.id for service, sg in self.interface_security_groups.items()},
        })
