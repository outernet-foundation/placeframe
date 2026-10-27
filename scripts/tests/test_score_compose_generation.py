from importlib.metadata import version
from pathlib import Path
from shutil import which

import pytest
import yaml
from packaging.version import Version

from docker_devkit.config import load_config
from docker_devkit.documents import compute_service_shas, parse_bake
from docker_devkit.lifecycle import require_manifest
from docker_devkit.score_generate import compose_seams, generate_compose

REPO_ROOT = Path(__file__).resolve().parents[2]

# The generated compose sources need the seam config fields.
_required_devkit = Version("0.4.9")
pytestmark = [
    pytest.mark.skipif(which("score-compose") is None, reason="pinned score-compose not on PATH"),
    pytest.mark.skipif(
        Version(version("docker-devkit")) < _required_devkit
        and Version(version("docker-devkit")) != Version("0.0.0.dev0"),
        reason=f"docker-devkit >= {_required_devkit} required for the seam fields",
    ),
]


def _seam_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, dict]:
    config = load_config(REPO_ROOT)
    assert config is not None and config.generate_score is not None
    # Redirect outputs into the test tmpdir so regeneration never touches the committed
    # artifacts; {gpu} tokens ride along for the variant-carrying seam.
    redirected = config.generate_score.model_copy(
        update={
            "seams": [
                seam.model_copy(update={"output": tmp_path / seam.output.name}) for seam in config.generate_score.seams
            ]
        }
    )

    for name, value in compute_service_shas(REPO_ROOT, parse_bake(require_manifest(REPO_ROOT))).items():
        monkeypatch.setenv(name, value)

    lock_images: dict[str, str] = {}
    for line in (
        (REPO_ROOT / config.generate_score.bake_file.with_suffix(".lock")).read_text(encoding="utf-8").splitlines()
    ):
        name, separator, reference = line.partition("=")
        if separator and name.strip() and not name.startswith("#"):
            lock_images[name.strip()] = reference

    generate_compose(REPO_ROOT, redirected, lock_images)
    return {
        seam.name: yaml.safe_load((tmp_path / seam.output.name).read_text(encoding="utf-8"))
        for seam in compose_seams(redirected)
    }


def test_seam_generation_splits_the_stack_by_assembly_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = _seam_artifacts(tmp_path, monkeypatch)

    assert sorted(artifacts) == [
        "core-cuda",
        "core-rocm",
        "gateway-keycloak",
        "gateway-open",
        "tunnel-ngrok",
    ]

    for name, artifact in artifacts.items():
        services = artifact.get("services") or {}
        assert services, f"{name} carries no services"
        for service_name, service in services.items():
            assert "profiles" not in service, f"{name}/{service_name} still declares compose profiles"
            for volume in service.get("volumes") or []:
                assert volume.get("type") != "bind", f"{name}/{service_name} carries a non-inlined bind"

    core = artifacts["core-cuda"]["services"]
    assert set(core) == {
        "api-api",
        "lease-server-lease-server",
        "localizer-localizer",
        "reconstructor-reconstructor",
        "pf-postgres",
        "pf-postgres-create",
        "pf-postgres-migrate",
        "seaweedfs",
        "seaweedfs-admin",
        "seaweedfs-audit",
        "loki",
        "initialize-loki",
        "initialize-s3",
        "alloy",
        "grafana",
        "wait-for-resources",
    }
    assert core["api-api"]["environment"]["AUTH_JWKS_URL"] == "${AUTH_JWKS_URL:-}"

    keycloak_gateway = artifacts["gateway-keycloak"]["services"]["gateway-gateway"]
    assert keycloak_gateway["environment"]["AUTH_REALM"] == "placeframe-dev"
    assert sorted(config["target"] for config in keycloak_gateway["configs"]) == [
        "/etc/caddy/snippets/loki/auth-loki.conf",
        "/etc/caddy/snippets/site/auth-site.conf",
    ]
    assert "keycloak" in artifacts["gateway-keycloak"]["services"]

    open_gateway = artifacts["gateway-open"]["services"]["gateway-gateway"]
    assert "AUTH_REALM" not in open_gateway["environment"]
    assert "configs" not in open_gateway
    assert "keycloak" not in artifacts["gateway-open"]["services"]

    ngrok = artifacts["tunnel-ngrok"]["services"]["tunnel-ngrok-ngrok"]
    assert ngrok["restart"] == "on-failure"
    assert ngrok["image"] == "${NGROK_IMAGE:?err}"
    assert "exec ngrok http --domain=$${NGROK_DOMAIN:-}" in " ".join(ngrok["entrypoint"])
    assert ngrok["ports"] == [{"target": 4040, "published": "4040"}]
