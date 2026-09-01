from __future__ import annotations

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import yaml
from bashrun import bash
from stack_lifecycle.context_sha import compute_service_shas
from typer import Option, Typer

REPO_ROOT = Path(__file__).parents[4]
SCORE_DIR = REPO_ROOT / "score"
BAKE_FILE = Path("compose.bake.yml")

WORKLOADS = ["api.yaml", "lease-server.yaml", "gateway.yaml"]

COMPOSE_OUTPUT = Path("compose.yaml")
K8S_OUTPUT = Path("deploy") / "manifests.yaml"
# --local writes here instead. Gitignored, so a local run cannot overwrite the committed
# artifact Argo CD deploys — a local-only storage class reaching the cluster leaves the
# Postgres and MinIO volumes unbindable on the next rebuild.
K8S_LOCAL_OUTPUT = Path("manifests.yaml")
K8S_STATE = Path(".score-k8s")

# Read by the k8s provisioners as {{ env "SCORE_STORAGE_CLASS" }}.
STORAGE_CLASS_VAR = "SCORE_STORAGE_CLASS"
CLOUD_STORAGE_CLASS = "hcloud-volumes"
LOCAL_STORAGE_CLASS = "local-path"

COMPOSE_PROVISIONERS = [
    "placeframe-postgres.provisioners.yaml",
    "placeframe-config.provisioners.yaml",
    "placeframe-keycloak.provisioners.yaml",
    "placeframe-s3.provisioners.yaml",
]
COMPOSE_PATCH_TEMPLATES = ["restart-policy.tpl"]

K8S_PROVISIONERS = [
    "placeframe-postgres.k8s.provisioners.yaml",
    "placeframe-minio.k8s.provisioners.yaml",
    "placeframe-config.k8s.provisioners.yaml",
    "placeframe-keycloak.k8s.provisioners.yaml",
]

# Placeholders in the workload files are ALL-CAPS, so this cannot collide with Score's own
# lowercase dotted ${resources.db.host} references.
PLACEHOLDER = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


class Target(str, Enum):
    both = "both"
    compose = "compose"
    k8s = "k8s"


app = Typer(add_completion=False, pretty_exceptions_show_locals=False)


def cli(
    target: Target = Option(Target.both, "--target", help="Which Score artifact to generate."),
    local: bool = Option(
        False,
        "--local",
        help=(
            "Generate for a local cluster: local-path storage, written to the gitignored "
            "score/manifests.yaml instead of the committed score/deploy/manifests.yaml."
        ),
    ),
) -> None:
    # The same call up, build-docker, and preflight make, so every image tag is a pure function
    # of committed source rather than a hand-typed value.
    os.environ.update(compute_service_shas(REPO_ROOT, BAKE_FILE))
    os.environ[STORAGE_CLASS_VAR] = LOCAL_STORAGE_CLASS if local else CLOUD_STORAGE_CLASS

    if target in (Target.both, Target.compose):
        _generate_compose()

    if target in (Target.both, Target.k8s):
        _generate_k8s(K8S_LOCAL_OUTPUT if local else K8S_OUTPUT)


def _generate_compose() -> None:
    _init_state("score-compose init --project placeframe --no-sample", COMPOSE_PROVISIONERS, COMPOSE_PATCH_TEMPLATES)

    with _rendered_workloads() as workloads:
        bash(
            f"score-compose generate {workloads} --output {COMPOSE_OUTPUT.as_posix()}"
            " --publish 8000:api:8000 --publish 8443:gateway:8443",
            cwd=SCORE_DIR,
        )


def _generate_k8s(output: Path) -> None:
    _init_state("score-k8s init --no-sample", K8S_PROVISIONERS, [])

    (SCORE_DIR / output).parent.mkdir(parents=True, exist_ok=True)

    with _rendered_workloads() as workloads:
        bash(f"score-k8s generate {workloads} --output {output.as_posix()}", cwd=SCORE_DIR)

    _sort_documents(SCORE_DIR / output)
    _normalise_state_paths(SCORE_DIR / K8S_STATE / "state.yaml")


def _init_state(command: str, provisioners: list[str], patch_templates: list[str]) -> None:
    # init is idempotent over an existing state directory: it rewrites the provisioner copies
    # without disturbing state. The state must survive, because score-k8s mints a random uid per
    # workload on first add and emits it as the app.kubernetes.io/instance label — discarding it
    # would change the generated manifests on every run.
    flags = " ".join(f"--provisioners ./{name}" for name in provisioners)
    if patch_templates:
        flags += " " + " ".join(f"--patch-templates ./{name}" for name in patch_templates)

    bash(f"{command} {flags}", cwd=SCORE_DIR)


@contextmanager
def _rendered_workloads() -> Iterator[str]:
    # Workload files are Score spec documents, not Go templates, so they cannot read the
    # environment the way the provisioner files can. Expanding ${API_SHA} into a rendered copy
    # keeps one mechanism across both halves.
    with TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)

        for name in WORKLOADS:
            (directory / name).write_text(_expand((SCORE_DIR / name).read_text(encoding="utf-8"), name), "utf-8")

        yield " ".join((directory / name).as_posix() for name in WORKLOADS)


def _expand(text: str, name: str) -> str:
    def replace(match: re.Match[str]) -> str:
        variable = match.group(1)
        value = os.environ.get(variable)
        if not value:
            raise SystemExit(f"{name}: ${{{variable}}} is not set. Is it a service in {BAKE_FILE}?")
        return value

    return PLACEHOLDER.sub(replace, text)


def _normalise_state_paths(path: Path) -> None:
    # score-k8s records the absolute path each workload was read from. Ours are rendered into a
    # per-run temporary directory, so the recorded path — and therefore the committed state file —
    # would differ on every run and on every machine. The field is provenance only; the workloads
    # are passed explicitly on each generate, so reducing it to the bare filename is safe and makes
    # the state reproducible.
    text = path.read_text(encoding="utf-8")
    for name in WORKLOADS:
        text = re.sub(rf"(?m)^(\s*file:\s*).*/{re.escape(name)}$", rf"\g<1>{name}", text)
    _write(path, text)


def _sort_documents(path: Path) -> None:
    # score-k8s emits workloads in Go map order, which is randomised, so two runs otherwise
    # produce the same documents in a different sequence. Documents are parsed only to derive the
    # sort key and re-emitted as their original text, so Score's formatting is preserved.
    documents = [block for block in re.split(r"(?m)^---$\n", path.read_text(encoding="utf-8")) if block.strip()]

    def sort_key(item: tuple[int, str]) -> tuple[str, str, str, int]:
        index, block = item
        document = cast(dict[str, object], yaml.safe_load(block) or {})
        metadata = cast(dict[str, object], document.get("metadata") or {})
        return (
            str(document.get("kind", "")),
            str(metadata.get("namespace", "")),
            str(metadata.get("name", "")),
            index,
        )

    ordered = [block for _, block in sorted(enumerate(documents), key=sort_key)]
    _write(path, "".join(f"---\n{block}" for block in ordered))


def _write(path: Path, text: str) -> None:
    # newline="" suppresses the platform translation Python applies by default. Without it a
    # Windows run rewrites every line ending as CRLF while git stores LF, so the regenerated file
    # differs from the committed one on content that never changed and the staleness gate can
    # never pass.
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)

    # score-k8s writes its state file executable. Git records the mode, so on Linux that alone
    # shows up as a diff and fails the staleness gate — invisibly on Windows, where core.fileMode
    # is false and the bit is never tracked. These are data files; normalise them to 0644.
    path.chmod(0o644)


app.command()(cli)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
