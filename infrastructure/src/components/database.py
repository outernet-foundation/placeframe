from __future__ import annotations

import json
from typing import Any, Optional

from common.boto_clients import create_lambda_client
from components.secret import Secret
from pulumi import Input, ResourceOptions
from pulumi.dynamic import CreateResult, DiffResult, Resource, ResourceProvider, UpdateResult


class _DatabaseProvider(ResourceProvider):
    def _invoke_lambda(self, function_arn: str, payload: dict[str, Any]) -> None:
        response = create_lambda_client().invoke(
            FunctionName=function_arn, InvocationType="RequestResponse", Payload=json.dumps(payload).encode("utf-8")
        )
        if response.get("FunctionError"):
            error_payload = json.loads(response["Payload"].read().decode("utf-8"))
            raise RuntimeError(f"Lambda invocation failed: {error_payload}")

    def create(self, props: dict[str, Any]):
        self._invoke_lambda(
            function_arn=props["function_arn"],
            payload={
                "op": "create",
                "name": props["name"],
                "owner_password_secret_arn": props["owner_password_secret_arn"],
                "service_password_secret_arn": props["service_password_secret_arn"],
            },
        )

        return CreateResult(
            id_=props["name"],
            outs={
                "function_arn": props["function_arn"],
                "name": props["name"],
                "owner_password_secret_arn": props["owner_password_secret_arn"],
                "service_password_secret_arn": props["service_password_secret_arn"],
            },
        )

    def diff(self, _id: str, olds: dict[str, Any], news: dict[str, Any]) -> DiffResult:
        replaces = [k for k in ("function_arn", "name") if olds.get(k) != news.get(k)]
        changes = bool(
            replaces
            or (olds.get("owner_password_secret_arn") != news.get("owner_password_secret_arn"))
            or (olds.get("service_password_secret_arn") != news.get("service_password_secret_arn"))
            or (olds.get("owner_password_secret_version_id") != news.get("owner_password_secret_version_id"))
            or (olds.get("service_password_secret_version_id") != news.get("service_password_secret_version_id"))
        )
        return DiffResult(changes=changes, replaces=replaces, delete_before_replace=False)

    def update(self, _id: str, olds: dict[str, Any], news: dict[str, Any]) -> UpdateResult:
        if olds.get("owner_password_secret_arn") != news.get("owner_password_secret_arn") or olds.get(
            "service_password_secret_arn"
        ) != news.get("service_password_secret_arn"):
            self._invoke_lambda(
                function_arn=news["function_arn"],
                payload={
                    "op": "update",
                    "name": news["name"],
                    "owner_password_secret_arn": news["owner_password_secret_arn"],
                    "service_password_secret_arn": news["service_password_secret_arn"],
                },
            )
        return UpdateResult(outs=news)

    def delete(self, _id: str, props: dict[str, Any]):
        self._invoke_lambda(function_arn=props["function_arn"], payload={"op": "delete", "name": props["name"]})


class Database(Resource):
    def __init__(
        self,
        resource_name: str,
        database_manager_function_arn: Input[str],
        name: Input[str],
        password_secret: Secret,
        *,
        opts: Optional[ResourceOptions] = None,
    ):
        super().__init__(
            _DatabaseProvider(),
            resource_name,
            {
                "function_arn": database_manager_function_arn,
                "name": name,
                "owner_password_secret_arn": password_secret.arn,
                "service_password_secret_arn": password_secret.arn,
                "owner_password_secret_version_id": password_secret.version_id,
                "service_password_secret_version_id": password_secret.version_id,
            },
            opts,
        )
