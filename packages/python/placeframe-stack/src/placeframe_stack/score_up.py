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
CNPG_OPERATOR_MANIFEST = "https://github.com/cloudnative-pg/cloudnative-pg/releases/download/v1.30.0/cnpg-1.30.0.yaml"
CNPG_OPERATOR_IMAGE = "ghcr.io/cloudnative-pg/cloudnative-pg:1.30.0"
CNPG_OPERAND_IMAGE = "placeframe-postgres-cnpg:14-trusted"
CNPG_OPERAND_DOCKERFILE = "docker/postgres-cnpg/Dockerfile"
CNPG_OPERAND_CONTEXT = "docker/postgres-cnpg"


class Target(str, Enum):
    docker = "docker"
    k3s = "k3s"


class Postgres(str, Enum):
    statefulset = "statefulset"
    cnpg = "cnpg"


K8S_PROVISIONERS = {
    Postgres.statefulset: "placeframe-postgres.k8s.provisioners.yaml",
    Postgres.cnpg: "placeframe-postgres-cnpg.k8s.provisioners.yaml",
}

app = typer.Typer(add_completion=False)


@app.command()
def score_up(
    target: Annotated[Target, typer.Option("--target", help="Where to bring the stack up.")] = Target.docker,
    postgres: Annotated[
        Postgres, typer.Option("--postgres", help="k3s postgres backend: raw StatefulSet or CloudNativePG.")
    ] = Postgres.statefulset,
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
        if postgres == Postgres.cnpg:
            raise typer.BadParameter("CloudNativePG postgres is Kubernetes-only; use --target k3s.")

        if not (SCORE_DIR / ".score-compose").exists():
            bash(
                "score-compose init --project placeframe --no-sample "
                "--provisioners ./placeframe-postgres.provisioners.yaml "
                "--patch-templates ./restart-policy.tpl",
                cwd=SCORE_DIR,
            )

        bash(
            f"score-compose generate {WORKLOADS} --publish 8000:api:8000 --publish 8443:gateway:8443",
            cwd=SCORE_DIR,
        )
        bash(f"docker compose -p {PROJECT} up -d", cwd=SCORE_DIR)
        print("Docker stack up -> http://localhost:8443/schema/swagger")
        return

    fresh = not bash_check(f"docker inspect {NODE}")
    if fresh:
        # A fresh cluster gets fresh generated passwords, so wipe any stale k8s score state
        # and register the provisioner for the chosen postgres backend before generating.
        bash("rm -rf .score-k8s manifests.yaml", cwd=SCORE_DIR)
        bash(f"score-k8s init --no-sample --provisioners ./{K8S_PROVISIONERS[postgres]}", cwd=SCORE_DIR)
        bash(f'k3d cluster create {CLUSTER} --no-lb --k3s-arg "--disable=traefik@server:0"')

        if postgres == Postgres.cnpg:
            bash(f"docker build -f {CNPG_OPERAND_DOCKERFILE} -t {CNPG_OPERAND_IMAGE} {CNPG_OPERAND_CONTEXT}")
            bash_pipe(f"docker save {CNPG_OPERAND_IMAGE}", f"docker exec -i {NODE} ctr -n k8s.io images import -")
            _preload_image(CNPG_OPERATOR_IMAGE)
            bash(f"kubectl apply --server-side -f {CNPG_OPERATOR_MANIFEST}")
            bash("kubectl -n cnpg-system rollout status deploy/cnpg-controller-manager --timeout=180s")

    bash(f"score-k8s generate {WORKLOADS}", cwd=SCORE_DIR)

    manifests = (SCORE_DIR / "manifests.yaml").read_text(encoding="utf-8")
    images = SYSTEM_IMAGES + sorted({
        line.split("image:", 1)[1].strip() for line in manifests.splitlines() if line.strip().startswith("image:")
    })
    for image in images:
        _preload_image(image)

    bash("kubectl -n kube-system rollout restart deploy/local-path-provisioner")
    bash("kubectl apply -f manifests.yaml", cwd=SCORE_DIR)

    if postgres == Postgres.cnpg:
        bash("kubectl wait --for=condition=Ready cluster/pf-postgres --timeout=300s")

    bash("kubectl wait --for=condition=complete job/pf-postgres-migrate --timeout=300s")
    bash("kubectl rollout status deployment/api --timeout=200s")
    print("k3s stack up -> run: kubectl port-forward deploy/gateway 8443:8443")


def _preload_image(image: str) -> None:
    if not bash_check(f"docker image inspect {image}"):
        bash(f"docker pull {image}")

    bash_pipe(f"docker save {image}", f"docker exec -i {NODE} ctr -n k8s.io images import -")
