# components/ecr.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, TypedDict, cast

from pulumi import ComponentResource, Input, Output, ResourceOptions, export
from pulumi_aws import ecr
from pulumi_aws.ecr import get_repository_output


class Repository(ComponentResource):
    def __init__(self, resource_name: str, name: str | Input[str], *, opts: ResourceOptions | None = None):
        super().__init__("custom:Repository", resource_name, opts=opts)

        self.resource_name = resource_name
        self._child_opts = ResourceOptions.merge(opts, ResourceOptions(parent=self))

        if isinstance(name, str):
            self._repo = ecr.Repository(
                resource_name,
                name=name,
                opts=ResourceOptions.merge(self._child_opts, ResourceOptions(retain_on_delete=True, import_=name)),
            )
        else:
            self._repo = get_repository_output(name=name)

        self.name = name
        self.arn = self._repo.arn
        self.url = self._repo.repository_url

        export(f"{self.resource_name}-url", self.url)

        self.register_outputs({"name": self.name, "arn": self.arn, "url": self.url})

    class RepoEntry(TypedDict, total=False):
        digest: str
        tags: List[str]  # optional metadata; not used for resolution

    def locked_digest(self, lock_path: str = "image-lock.json") -> Output[str]:
        # Find the project root (folder containing Pulumi.yaml)
        project_root = Path(os.getcwd())
        while project_root != project_root.parent:
            if (project_root / "Pulumi.yaml").exists():
                break
            project_root = project_root.parent

        lock_file = project_root / lock_path
        if not lock_file.exists():
            raise FileNotFoundError(f"Lock file not found: {lock_file}")

        # Load and prepare the container map once (outside of apply)
        data_raw: object = json.loads(lock_file.read_text())
        data_map: Dict[str, object] = cast(Dict[str, object], data_raw)
        container_raw: object = data_map.get("repositories", data_map)
        container: Dict[str, object] = cast(Dict[str, object], container_raw)

        def build_locked_ref(name: str, repo_url: str) -> str:
            entry_raw: object = container.get(name)
            if not isinstance(entry_raw, dict):
                # use the resolved name in the message; avoid referencing non-existent self._name
                raise ValueError(f"Invalid or missing entry in lock file for repository '{name}': {entry_raw}")

            entry_map: Dict[str, object] = cast(Dict[str, object], entry_raw)
            digest_obj: object = entry_map.get("digest")
            if not isinstance(digest_obj, str) or not digest_obj:
                raise ValueError(f"Missing 'digest' for repository '{name}' in lock file.")

            return f"{repo_url}@{digest_obj}"

        # Lift both the repo name and URL to build the final locked reference
        return Output.all(self.name, self._repo.repository_url).apply(lambda args: build_locked_ref(args[0], args[1]))
