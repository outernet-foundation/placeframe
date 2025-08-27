from __future__ import annotations

from ipaddress import ip_network
from typing import TYPE_CHECKING, List, NotRequired, Required, Sequence, TypedDict, Union, assert_never, overload

from pulumi import ComponentResource, Input, Output, ResourceOptions
from pulumi_aws import ec2
from pulumi_aws.ec2 import get_security_group_output
from pulumi_aws.vpc import SecurityGroupEgressRule, SecurityGroupIngressRule

if TYPE_CHECKING:
    from components.vpc import Vpc


class _BaseRule(TypedDict):
    ports: Required[Sequence[int | None]]
    protocols: NotRequired[Sequence[str]]


class _ToSG(_BaseRule, total=False):
    to_security_group: Required[SecurityGroup]


class _ToPrefix(_BaseRule, total=False):
    prefix_name: Required[str]
    to_prefix_list_id: Required[Input[str]]


class _ToCidr(_BaseRule, total=False):
    cidr_name: Required[str]
    to_cidr: Required[Input[str]]


class _FromCidr(_BaseRule, total=False):
    cidr_name: Required[str]
    from_cidr: Required[Input[str]]


SecurityGroupRule = Union[_ToSG, _ToPrefix, _ToCidr, _FromCidr]


def amazon_provided_dns_cidr(vpc_cidr: Input[str]) -> Output[str]:
    """
    Return the /32 CIDR for the Amazon-provided DNS resolver of a VPC.
    AWS defines this as <primary VPC CIDR base> + 2.
    """
    return Output.from_input(vpc_cidr).apply(lambda cidr: f"{ip_network(cidr, strict=False).network_address + 2}/32")


class SecurityGroup(ComponentResource):
    @overload
    def __init__(
        self,
        resource_name: str,
        vpc: "Vpc",
        *,
        vpc_endpoints: List[str] | None = None,
        rules: List[SecurityGroupRule] = [],
        opts: ResourceOptions | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        resource_name: str,
        vpc: "Vpc",
        *,
        security_group_id: Input[str],
        vpc_endpoints: List[str] | None = None,
        rules: List[SecurityGroupRule] = [],
        opts: ResourceOptions | None = None,
    ) -> None: ...

    def __init__(
        self,
        resource_name: str,
        vpc: "Vpc",
        *,
        security_group_id: Input[str] | None = None,
        vpc_endpoints: List[str] | None = None,
        rules: List[SecurityGroupRule] = [],
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:SecurityGroup", resource_name, opts=opts)

        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))
        self._resource_name = resource_name
        self._rule_ids: List[Output[str]] = []

        if security_group_id is not None:
            self._security_group = get_security_group_output(id=security_group_id)
        else:
            self._security_group = ec2.SecurityGroup(resource_name, vpc_id=vpc.id, opts=self._child_opts)

        self.id = self._security_group.id
        self.arn = self._security_group.arn

        if vpc_endpoints:
            rules.append({
                "cidr_name": "amazon-provided-dns",
                "to_cidr": Output.from_input(vpc.cidr_block).apply(
                    lambda cidr: f"{ip_network(cidr, strict=False).network_address + 2}/32"
                ),  # The /32 CIDR for the Amazon-provided DNS resolver of a VPC, defined by aws as <primary VPC CIDR base> + 2.
                "ports": [53],
                "protocols": ["tcp", "udp"],
            })

            for endpoint in vpc_endpoints:
                if endpoint == "s3":
                    rules.append({
                        "prefix_name": "s3",
                        "to_prefix_list_id": vpc.s3_endpoint_prefix_list_id,
                        "ports": [443],
                    })
                else:
                    rules.append({"to_security_group": vpc.interface_security_groups[endpoint], "ports": [443]})

        for rule in rules:
            ports = rule["ports"]
            protocols = rule["protocols"] if "protocols" in rule else ["tcp"]
            for port in ports:
                port_string = "all" if port is None else port
                for protocol in protocols:
                    protocol_string = "all" if protocol == "-1" else protocol
                    port_protocol_string = f"{port_string}-{protocol_string}"
                    if "to_security_group" in rule:
                        to_security_group = rule["to_security_group"]
                        SecurityGroupEgressRule(
                            f"{self._resource_name}-egress-to-{to_security_group._name}-{port_protocol_string}",
                            security_group_id=self._security_group.id,
                            ip_protocol=protocol,
                            from_port=port,
                            to_port=port,
                            referenced_security_group_id=to_security_group._security_group.id,
                            opts=self._child_opts,
                        )

                        SecurityGroupIngressRule(
                            f"{to_security_group._name}-ingress-from-{self._resource_name}-{port_protocol_string}",
                            security_group_id=to_security_group._security_group.id,
                            ip_protocol=protocol,
                            from_port=port,
                            to_port=port,
                            referenced_security_group_id=self._security_group.id,
                            opts=self._child_opts,
                        )

                    elif "to_prefix_list_id" in rule:
                        to_prefix_list_id = rule["to_prefix_list_id"]
                        SecurityGroupEgressRule(
                            f"{self._resource_name}-egress-to-prefix-list-{rule['prefix_name']}-{port_protocol_string}",
                            security_group_id=self._security_group.id,
                            ip_protocol=protocol,
                            from_port=port,
                            to_port=port,
                            prefix_list_id=to_prefix_list_id,
                            opts=self._child_opts,
                        )

                    elif "to_cidr" in rule:
                        to_cidr = rule["to_cidr"]
                        SecurityGroupEgressRule(
                            f"{self._resource_name}-egress-to-cidr-{rule['cidr_name']}-{port_protocol_string}",
                            security_group_id=self._security_group.id,
                            ip_protocol=protocol,
                            from_port=port,
                            to_port=port,
                            cidr_ipv4=to_cidr,
                            opts=self._child_opts,
                        )

                    elif "from_cidr" in rule:
                        from_cidr = rule["from_cidr"]
                        SecurityGroupIngressRule(
                            f"{self._resource_name}-ingress-from-cidr-{rule['cidr_name']}-{port_protocol_string}",
                            security_group_id=self._security_group.id,
                            ip_protocol=protocol,
                            from_port=port,
                            to_port=port,
                            cidr_ipv4=from_cidr,
                            opts=self._child_opts,
                        )

                    else:
                        assert_never(rule)

        self.register_outputs({"id": self.id, "arn": self.arn})
