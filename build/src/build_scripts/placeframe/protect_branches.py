from __future__ import annotations

import json
from pathlib import Path

import typer
from bashrun import bash, bash_output
from pydantic import BaseModel

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

REPO_ROOT = Path.cwd()
CONFIG_FILE = REPO_ROOT / ".github" / "branch-protection.json"


# --- Models ---


class BypassActor(BaseModel):
    app_name: str | None = None
    actor_id: int | None = None
    actor_type: str
    bypass_mode: str = "always"


class RefNameCondition(BaseModel):
    include: list[str] = []
    exclude: list[str] = []


class Conditions(BaseModel):
    ref_name: RefNameCondition = RefNameCondition()


class Ruleset(BaseModel, extra="allow"):
    """GitHub ruleset config. Extra fields (rules, target, enforcement) are passed through to the API."""

    name: str
    bypass_actors: list[BypassActor] = []
    conditions: Conditions = Conditions()


class MergeStrategies(BaseModel):
    allow_merge_commit: bool = True
    allow_squash_merge: bool = False
    allow_rebase_merge: bool = False


class Config(BaseModel):
    rulesets: list[Ruleset] = []
    merge_strategies: MergeStrategies | None = None


# --- Helpers ---


def _get_repo_slug() -> str:
    return bash_output("gh repo view --json nameWithOwner -q .nameWithOwner").strip()


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-")


def _resolve_app_id(app_name: str) -> int:
    slug = _slugify(app_name)
    result = bash_output(f"gh api apps/{slug} --jq '.id'").strip()
    if not result:
        raise SystemExit(f"GitHub App '{app_name}' not found.\nExpected slug: {slug}")
    return int(result)


def _delete_existing_ruleset(repo: str, name: str) -> None:
    existing = bash_output(f"gh api repos/{repo}/rulesets --jq '.[].id'").strip()
    for ruleset_id in existing.splitlines():
        ruleset_id = ruleset_id.strip()
        if not ruleset_id:
            continue
        ruleset_name = bash_output(f"gh api repos/{repo}/rulesets/{ruleset_id} --jq '.name'").strip()
        if ruleset_name == name:
            bash(f"gh api repos/{repo}/rulesets/{ruleset_id} -X DELETE")
            print(f"  Deleted existing ruleset '{name}' (id: {ruleset_id})")


def _resolve_bypass_actors(actors: list[BypassActor]) -> list[dict[str, str | int]]:
    resolved: list[dict[str, str | int]] = []
    for actor in actors:
        if actor.app_name is not None:
            actor_id = _resolve_app_id(actor.app_name)
            print(f"  Resolved app '{actor.app_name}' -> actor_id {actor_id}")
            resolved.append({"actor_id": actor_id, "actor_type": actor.actor_type, "bypass_mode": actor.bypass_mode})
        elif actor.actor_id is not None:
            resolved.append({
                "actor_id": actor.actor_id,
                "actor_type": actor.actor_type,
                "bypass_mode": actor.bypass_mode,
            })
    return resolved


# --- Main ---


@app.command()
def main(dry_run: bool = typer.Option(False, help="Show what would be applied without making changes")) -> None:
    """Apply branch protection rulesets from .github/branch-protection.json via the GitHub API."""
    config = Config.model_validate_json(CONFIG_FILE.read_text())

    repo = _get_repo_slug()
    print(f"Repository: {repo}")

    for ruleset in config.rulesets:
        print(f"\nRuleset: {ruleset.name}")

        # Build the API payload: start with the full JSON (including extra fields like rules),
        # then replace bypass_actors with resolved IDs
        payload = json.loads(ruleset.model_dump_json(by_alias=True))
        if ruleset.bypass_actors:
            payload["bypass_actors"] = _resolve_bypass_actors(ruleset.bypass_actors)

        if dry_run:
            print(f"  Would apply: {json.dumps(payload, indent=2)}")
            continue

        _delete_existing_ruleset(repo, ruleset.name)

        bash(f"gh api repos/{repo}/rulesets -X POST --input -", stdin_text=json.dumps(payload))
        print(f"  Ruleset '{ruleset.name}' created.")

    if config.merge_strategies is not None:
        print("\nMerge strategies:")
        payload = json.loads(config.merge_strategies.model_dump_json(by_alias=True))

        if dry_run:
            print(f"  Would apply: {json.dumps(payload, indent=2)}")
            return

        bash(f"gh api repos/{repo} -X PATCH --input -", stdin_text=json.dumps(payload))
        print("  Applied.")
