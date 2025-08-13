import json
from pathlib import Path

from pulumi import Output
from pulumi_aws import get_caller_identity, get_region_output
from pulumi_aws.ecr import Repository


def repo_digest(repo: Repository, lock_path: str = "infra/image-lock.json") -> Output[str]:
    data = json.loads(Path(lock_path).read_text())

    def pick(url: str, name: str) -> str:
        # Expect lock to map repo name -> digest string "sha256:…"
        digest = data.get(name) or (data.get("repositories", {}).get(name, {}).get("digest"))
        if not digest:
            raise RuntimeError(f"No digest for {name} in {lock_path}")
        return f"{url}@{digest}"

    return Output.all(repo.repository_url, repo.name).apply(lambda t: pick(*t))


def pullthrough_repo_digest(repo: Repository):
    return Output.concat(
        get_caller_identity().account_id,
        ".dkr.ecr.",
        get_region_output().region,
        ".amazonaws.com/",
        repo.name,
        ":latest",
    )
