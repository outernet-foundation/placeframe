# components/ecr.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, TypedDict, cast

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_aws import ecr


class Repository(ComponentResource):
    def __init__(self, resource_name: str, name: str, force_delete: bool | None = None, opts: ResourceOptions | None = None):
        super().__init__("custom:Repository", resource_name, opts=opts)
        
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))
        self._name = name
        self._repo = ecr.Repository(resource_name, name=name, force_delete=force_delete, opts=self._child_opts)

        self.resource_name = resource_name
        
        self.arn = self._repo.arn

        self.register_outputs({"arn": self.arn})

    class RepoEntry(TypedDict, total=False):
        digest: str
        tags: List[str]  # optional metadata; not used for resolution

    def locked_digest(self, lock_path: str = "infra/image-lock.json") -> Output[str] | None:
        if not Path(lock_path).exists():
            return None

        data_raw: object = json.loads(Path(lock_path).read_text())
        data_map: Dict[str, object] = cast(Dict[str, object], data_raw)
        container_raw: object = data_map.get("repositories", data_map)
        container: Dict[str, object] = cast(Dict[str, object], container_raw)
        entry_raw: object = container.get(self._name)
        
        if not isinstance(entry_raw, dict):
            return None
        
        entry_map: Dict[str, object] = cast(Dict[str, object], entry_raw)
        digest: object = entry_map.get("digest")

        return self._repo.repository_url.apply(lambda url: f"{url}@{digest}")