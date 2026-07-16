import json
import os
import re
import shlex
from pathlib import Path
from subprocess import CalledProcessError

import typer
from placeframe_bash import bash_handoff, bash_output

REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_INFRA_PROJECT = REPO_ROOT.parent / "infra" / "placeframe"
STACK = "dev"

app = typer.Typer(add_completion=False)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def secrets_exec(ctx: typer.Context) -> None:
    if not ctx.args:
        raise typer.BadParameter("Provide a command to run, e.g. `uv run pf-secrets -- uv run up`.")

    infra_override = os.environ.get("PLACEFRAME_INFRA_DIR")
    infra_project = Path(infra_override) if infra_override else DEFAULT_INFRA_PROJECT

    # Only secret config is injected; non-secret config stays in placeframe's .env.
    secrets = _load_secrets(infra_project)
    if not secrets:
        raise typer.BadParameter(f"No secrets in the Pulumi '{STACK}' stack at {infra_project}.")

    os.environ.update(secrets)
    bash_handoff(shlex.join(ctx.args))


def _load_secrets(infra_project: Path) -> dict[str, str]:
    try:
        config_json = bash_output(f"pulumi config --show-secrets --json -s {STACK}", cwd=infra_project)
    except CalledProcessError as error:
        typer.echo(f"Could not read the Pulumi '{STACK}' stack at {infra_project} — are you logged in?", err=True)
        raise typer.Exit(code=1) from error

    config: dict[str, dict[str, object]] = json.loads(config_json)
    secrets: dict[str, str] = {}
    for key, entry in config.items():
        value = entry.get("value")
        if not entry.get("secret") or not isinstance(value, str):
            continue

        # placeframe:minioSecretKey -> MINIO_SECRET_KEY
        env_name = re.sub(r"(?<!^)(?=[A-Z])", "_", key.split(":", 1)[-1]).upper()
        secrets[env_name] = value

    return secrets
