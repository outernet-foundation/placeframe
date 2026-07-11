from __future__ import annotations

import shutil
from pathlib import Path

import typer
from bashrun import bash, bash_output
from pydantic_settings import BaseSettings

from placeframe_unity.ci_step import ci_step

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

ARTIFACT_DIR = Path("/tmp/release-artifacts")
SKIP_PREFIXES = ("env-lock-", "versions")
SKIP_SUFFIXES = ("-build-report",)


class Settings(BaseSettings):
    github_sha: str
    github_repository: str
    github_output: str | None = None


@app.command()
def main(
    ci_run_id: str | None = typer.Option(None, "--ci-run-id", help="Override CI run lookup with a known run ID."),
) -> None:
    settings = Settings.model_validate({})
    repo = settings.github_repository

    if ci_run_id:
        run_id = ci_run_id
        print(f"  Using override CI run: {run_id}")
    else:
        sha = bash_output(f'gh api "/repos/{repo}/git/commits/{settings.github_sha}" --jq ".parents[1].sha"').strip()

        with ci_step("Find successful CI run"):
            run_id = bash_output(
                f'gh api "/repos/{repo}/actions/workflows/placeframe-ci.yml/runs?head_sha={sha}&status=success"'
                " --jq '.workflow_runs[0].id // empty'"
            ).strip()

            if not run_id:
                print(f"::error::No successful CI run found for SHA {sha}. Cannot release untested code.")
                raise typer.Exit(code=1)

            print(f"  CI run: {run_id}")

    if settings.github_output:
        with open(settings.github_output, "a") as f:
            f.write(f"run_id={run_id}\n")

    with ci_step("Download artifacts"):
        bash(f"gh run download {run_id} --repo {repo} --dir {ARTIFACT_DIR}")

        if not ARTIFACT_DIR.is_dir():
            print("  No artifacts downloaded")
            return

        downloaded = 0
        for entry in sorted(ARTIFACT_DIR.iterdir()):
            if not entry.is_dir():
                continue
            if any(entry.name.startswith(p) for p in SKIP_PREFIXES) or any(
                entry.name.endswith(s) for s in SKIP_SUFFIXES
            ):
                print(f"  Removed: {entry.name}")
                shutil.rmtree(entry)
                continue
            downloaded += 1
            print(f"  Kept: {entry.name}")

        print(f"  {downloaded} artifact(s) ready in {ARTIFACT_DIR}")
