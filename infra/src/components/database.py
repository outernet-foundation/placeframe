# database.py
# Pulumi dynamic resource that calls your codegen'd Python client to create/delete databases.

from typing import Any, Dict, Optional

# Codegen'd client (OpenAPI Generator Python):
from plerion_client import ApiClient, Configuration
from plerion_client.api.default_api import DefaultApi
from plerion_client.models.body_create_database import BodyCreateDatabase
from pulumi import Input, Output, ResourceOptions
from pulumi.dynamic import CreateResult, DiffResult, Resource, ResourceProvider, UpdateResult

try:
    # OpenAPI Generator raises ApiException on non-2xx; import if available.
    from plerion_client.exceptions import ApiException  # type: ignore
except Exception:  # pragma: no cover

    class ApiException(Exception):  # fallback, in case exceptions module layout differs
        def __init__(self, status: int = 0, reason: str = ""):
            super().__init__(reason)
            self.status = status


class _DatabaseProvider(ResourceProvider):
    def _api(self, url: str) -> DefaultApi:
        cfg = Configuration(host=url)  # set base URL for the client
        return DefaultApi(ApiClient(cfg))

    def create(self, inputs: Dict[str, Any]) -> CreateResult:
        api = self._api(inputs["url"])
        body = BodyCreateDatabase(
            # Adjust field names here if your BodyCreateDatabase differs.
            name=inputs["name"],
            security_group_id=inputs["security_group_id"],
        )
        api.create_database(body)  # returns `object` per codegen; we don't need details
        return CreateResult(id_=inputs["name"], outs=inputs)

    def diff(self, _id: str, olds: Dict[str, Any], news: Dict[str, Any]) -> DiffResult:
        replaces = [k for k in ("url", "security_group_id", "name") if olds.get(k) != news.get(k)]
        return DiffResult(changes=bool(replaces), replaces=replaces, delete_before_replace=False)

    def update(self, _id: str, _olds: Dict[str, Any], news: Dict[str, Any]) -> UpdateResult:
        # No in-place updates; any meaningful change triggers replacement via diff().
        return UpdateResult(outs=news)

    def delete(self, _id: str, props: Dict[str, Any]) -> None:
        api = self._api(props["url"])
        try:
            api.delete_database(name=props["name"])
        except ApiException as e:
            # Ignore "not found" so destroy stays idempotent; codegen sets status when possible.
            if getattr(e, "status", None) != 404:
                raise


class Database(Resource):
    url: Output[str]
    security_group_id: Output[str]
    name: Output[str]

    def __init__(
        self,
        resource_name: str,
        *,
        url: Input[str],
        security_group_id: Input[str],
        name: Optional[Input[str]] = None,
        opts: Optional[ResourceOptions] = None,
    ):
        props = {"url": url, "security_group_id": security_group_id, "name": name or resource_name}
        super().__init__(_DatabaseProvider(), resource_name, props, opts)
