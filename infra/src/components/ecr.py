from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, TypedDict, cast

from pulumi import Output
from pulumi_aws.ecr import Repository


class RepoEntry(TypedDict, total=False):
    tag: str
    digest: str
    contextHash: str


def locked_image_ref(repo: Repository, lock_path: str = "infra/image-lock.json") -> Output[str]:
    def build_ref(url: str, name: str) -> str:
        # Load and parse lock file
        try:
            data = json.loads(Path(lock_path).read_text())
        except FileNotFoundError:
            raise RuntimeError(f"{lock_path} not found")

        if not isinstance(data, dict):
            raise RuntimeError(f"{lock_path} must be a JSON object")

        data_dict = cast(Dict[str, object], data)

        # Find entry for this repository
        entry_data = data_dict.get(name)
        if not isinstance(entry_data, dict):
            raise RuntimeError(f"Lock entry for '{name}' missing 'tag' or 'digest' in {lock_path}")

        entry_dict = cast(Dict[str, object], entry_data)
        entry: RepoEntry = {}

        for field in ["tag", "digest", "context-hash"]:
            value = entry_dict.get(field)
            if isinstance(value, str):
                entry[field] = value  # type: ignore[literal-required]

        if not entry or "tag" not in entry or "digest" not in entry:
            raise RuntimeError(f"Lock entry for '{name}' missing 'tag' or 'digest' in {lock_path}")

        return f"{url}:{entry['tag']}@{entry['digest']}"

    return repo.repository_url.apply(lambda url: repo.name.apply(lambda name: build_ref(url, name)))
