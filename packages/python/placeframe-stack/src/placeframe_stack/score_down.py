from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from placeframe_bash import bash

SCORE_DIR = Path("score")
PROJECT = "score-poc"
CLUSTER = "score-poc"


class Target(str, Enum):
    docker = "docker"
    k3s = "k3s"


app = typer.Typer(add_completion=False)


@app.command()
def score_down(
    target: Annotated[Target, typer.Option("--target", help="Which stack to tear down.")] = Target.docker,
) -> None:
    if target == Target.docker:
        bash(f"docker compose -p {PROJECT} down -v", cwd=SCORE_DIR)
        print("Docker stack down.")
        return

    bash(f"k3d cluster delete {CLUSTER}")
    bash("rm -rf .score-k8s manifests.yaml", cwd=SCORE_DIR)
    print("k3s cluster deleted.")
