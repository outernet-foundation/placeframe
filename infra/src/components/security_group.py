from __future__ import annotations

from typing import List, overload

import pulumi_aws as aws
from pulumi import ComponentResource, Input, Output, ResourceOptions


class SecurityGroup(ComponentResource):
    @overload
    def __init__(self, name: str, *, vpc_id: Input[str], opts: ResourceOptions | None = None) -> None: ...
    @overload
    def __init__(self, name: str, *, security_group_id: Input[str], opts: ResourceOptions | None = None) -> None: ...

    def __init__(
        self,
        name: str,
        *,
        vpc_id: Input[str] | None = None,
        security_group_id: Input[str] | None = None,
        opts: ResourceOptions | None = None,
    ):
        super().__init__("custom:SecurityGroup", name, opts=opts)

        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))
        self._name = name
        self._rule_ids: List[Output[str]] = []

        if vpc_id is not None:
            self._security_group = aws.ec2.SecurityGroup(name, vpc_id=vpc_id, opts=self._child_opts)
        elif security_group_id is not None:
            self._security_group = aws.ec2.get_security_group_output(id=security_group_id)
        else:
            raise ValueError("Either vpc_id or security_group_id must be provided")

        self.register_outputs({"id": self.id, "arn": self.arn})

    @property
    def id(self) -> Output[str]:
        return Output.all(self._security_group.id, *self._rule_ids).apply(lambda args: args[0])

    @property
    def arn(self) -> Output[str]:
        return Output.all(self._security_group.arn, *self._rule_ids).apply(lambda args: args[0])

    def allow_traffic(self, from_security_group: SecurityGroup, to_security_group: SecurityGroup, ports: List[int], protocol: str = "tcp") -> None:
        for port in ports:
            ingress_rule = aws.vpc.SecurityGroupIngressRule(
                f"{to_security_group._name}-ingress-from-{from_security_group._name}-{port}-{protocol}",
                security_group_id=to_security_group._security_group.id,
                ip_protocol=protocol,
                from_port=port,
                to_port=port,
                referenced_security_group_id=from_security_group._security_group.id,
                opts=self._child_opts,
            )
            egress_rule = aws.vpc.SecurityGroupEgressRule(
                f"{from_security_group._name}-egress-to-{to_security_group._name}-{port}-{protocol}",
                security_group_id=from_security_group._security_group.id,
                ip_protocol=protocol,
                from_port=port,
                to_port=port,
                referenced_security_group_id=to_security_group._security_group.id,
                opts=self._child_opts,
            )
            self._rule_ids.append(ingress_rule.id)
            self._rule_ids.append(egress_rule.id)

    def allow_ingress_reciprocal(self, from_security_group: SecurityGroup, ports: List[int], protocol: str = "tcp") -> None:
        self.allow_traffic(from_security_group=from_security_group, to_security_group=self, ports=ports, protocol=protocol)

    def allow_egress_reciprocal(self, to_security_group: SecurityGroup, ports: List[int], protocol: str = "tcp") -> None:
        self.allow_traffic(from_security_group=self, to_security_group=to_security_group, ports=ports, protocol=protocol)

    def allow_ingress_cidr(self, cidr: Input[str], cidr_name: str, ports: List[int], protocol: str = "tcp") -> None:
        for port in ports:
            self._rule_ids.append(
                aws.vpc.SecurityGroupIngressRule(
                    f"{self._name}-ingress-from-{cidr_name}-{port}-{protocol}",
                    security_group_id=self._security_group.id,
                    ip_protocol=protocol,
                    from_port=port,
                    to_port=port,
                    cidr_ipv4=cidr,
                    opts=self._child_opts,
                ).id
            )

    def allow_egress_cidr(self, cidr: Input[str], cidr_name: str, ports: List[int], protocol: str = "tcp") -> None:
        for port in ports:
            self._rule_ids.append(
                aws.vpc.SecurityGroupEgressRule(
                    f"{self._name}-egress-to-{cidr_name}-{port}-{protocol}",
                    security_group_id=self._security_group.id,
                    ip_protocol=protocol,
                    from_port=port,
                    to_port=port,
                    cidr_ipv4=cidr,
                    opts=self._child_opts,
                ).id
            )

    def allow_egress_prefix_list(
        self, prefix_list_id: Input[str], prefix_list_name: str, ports: List[int], protocol: str = "tcp"
    ) -> None:
        for port in ports:
            self._rule_ids.append(
                aws.vpc.SecurityGroupEgressRule(
                    f"{self._name}-egress-to-prefix-list-{prefix_list_name}-{port}-{protocol}",
                    security_group_id=self._security_group.id,
                    ip_protocol=protocol,
                    from_port=port,
                    to_port=port,
                    prefix_list_id=prefix_list_id,
                    opts=self._child_opts,
                ).id
            )
