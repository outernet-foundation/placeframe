from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from placeframe_bash import bash, bash_check, bash_pipe

SCORE_DIR = Path("score")
PROJECT = "score-poc"
CLUSTER = "score-poc"
NODE = f"k3d-{CLUSTER}-server-0"
WORKLOADS = "api.yaml lease-server.yaml gateway.yaml"
SYSTEM_IMAGES = [
    "rancher/local-path-provisioner:v0.0.36",
    "rancher/mirrored-library-busybox:1.37.0",
]


class Target(str, Enum):
    docker = "docker"
    k3s = "k3s"


app = typer.Typer(add_completion=False)


@app.command()
def score_up(
    target: Annotated[Target, typer.Option("--target", help="Where to bring the stack up.")] = Target.docker,
) -> None:
    if not (SCORE_DIR / ".score-compose").exists():
        bash(
            "score-compose init --project placeframe --no-sample "
            "--provisioners ./placeframe-postgres.provisioners.yaml "
            "--patch-templates ./restart-policy.tpl",
            cwd=SCORE_DIR,
        )

    if not (SCORE_DIR / ".score-k8s").exists():
        bash(
            "score-k8s init --no-sample --provisioners ./placeframe-postgres.k8s.provisioners.yaml",
            cwd=SCORE_DIR,
        )

    if target == Target.docker:
        bash(
            f"score-compose generate {WORKLOADS} --publish 8000:api:8000 --publish 8443:gateway:8443",
            cwd=SCORE_DIR,
        )
        bash(f"docker compose -p {PROJECT} up -d", cwd=SCORE_DIR)
        print("Docker stack up -> http://localhost:8443/schema/swagger")
        return

    bash(f"score-k8s generate {WORKLOADS}", cwd=SCORE_DIR)

    if not bash_check(f"docker inspect {NODE}"):
        bash(f'k3d cluster create {CLUSTER} --no-lb --k3s-arg "--disable=traefik@server:0"')

    manifests = (SCORE_DIR / "manifests.yaml").read_text(encoding="utf-8")
    images = SYSTEM_IMAGES + sorted({
        line.split("image:", 1)[1].strip() for line in manifests.splitlines() if line.strip().startswith("image:")
    })
    for image in images:
        _preload_image(image)

    bash("kubectl -n kube-system rollout restart deploy/local-path-provisioner")
    bash("kubectl apply -f manifests.yaml", cwd=SCORE_DIR)
    bash("kubectl wait --for=condition=complete job/pf-postgres-migrate --timeout=200s")
    bash("kubectl rollout status deployment/api --timeout=200s")
    print("k3s stack up -> run: kubectl port-forward deploy/gateway 8443:8443")


def _preload_image(image: str) -> None:
    if not bash_check(f"docker image inspect {image}"):
        bash(f"docker pull {image}")

    bash_pipe(f"docker save {image}", f"docker exec -i {NODE} ctr -n k8s.io images import -")
