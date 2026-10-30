from importlib.metadata import version
from pathlib import Path
from shutil import which

import pytest
import yaml
from packaging.version import Version

from docker_devkit import config as config_module
from docker_devkit.config import LOCK_PATH, compose_bundles, load_config
from docker_devkit.documents import compute_service_shas, parse_image_lock
from docker_devkit.score_generate import generate_compose

REPO_ROOT = Path(__file__).resolve().parents[2]

# The generated compose sources need the services vocabulary.
_required_devkit = Version("0.5.5")
pytestmark = [
    pytest.mark.skipif(which("score-compose") is None, reason="pinned score-compose not on PATH"),
    pytest.mark.skipif(
        Version(version("docker-devkit")) < _required_devkit
        and Version(version("docker-devkit")) != Version("0.0.0.dev0"),
        reason=f"docker-devkit >= {_required_devkit} required for the services vocabulary",
    ),
]


def _bundle_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, dict]:
    config = load_config(REPO_ROOT)
    assert config is not None
    # Redirect derived bundle outputs into the test tmpdir so regeneration never
    # touches the committed artifacts (bundle_output joins the absolute tmp path).
    monkeypatch.setattr(config_module, "BUNDLE_OUTPUT_DIR", tmp_path)

    for name, value in compute_service_shas(REPO_ROOT, config).items():
        monkeypatch.setenv(name, value)

    generate_compose(REPO_ROOT, config, parse_image_lock(REPO_ROOT / LOCK_PATH).root)
    return {
        bundle.name: yaml.safe_load((tmp_path / bundle.output.name).read_text(encoding="utf-8"))
        for bundle in compose_bundles(config)
    }


def test_bundle_generation_splits_the_stack_by_assembly_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = _bundle_artifacts(tmp_path, monkeypatch)
    lock = parse_image_lock(REPO_ROOT / LOCK_PATH).root

    assert sorted(artifacts) == ["cuda", "keycloak", "ngrok", "rocm"]

    for name, artifact in artifacts.items():
        services = artifact.get("services") or {}
        assert services, f"{name} carries no services"
        for service_name, service in services.items():
            assert "profiles" not in service, f"{name}/{service_name} still declares compose profiles"
            assert "ports" not in service, f"{name}/{service_name} still publishes a host port"
            for volume in service.get("volumes") or []:
                assert volume.get("type") != "bind", f"{name}/{service_name} carries a non-inlined bind"

    for variant in ("cuda", "rocm"):
        core = artifacts[variant]["services"]
        assert set(core) == {
            "api",
            "lease-server",
            "localizer",
            "reconstructor",
            "pf-postgres",
            "pf-postgres-create",
            "pf-postgres-migrate",
            "seaweedfs",
            "seaweedfs-admin",
            "seaweedfs-audit",
            "initialize-s3",
            "loki",
            "initialize-loki",
            "alloy",
            "grafana",
            "wait-for-resources",
        }
    assert core["api"]["environment"]["AUTH_JWKS_URL"] == "${AUTH_JWKS_URL:-}"
    assert core["api"]["environment"]["DEBUG_API"] == "false"

    keycloak_bundle = artifacts["keycloak"]["services"]
    assert set(keycloak_bundle) == {"keycloak", "keycloak-configurator", "wait-for-resources"}
    keycloak = keycloak_bundle["keycloak"]
    assert keycloak["image"] == lock["KEYCLOAK_IMAGE"]
    assert keycloak["environment"]["KC_HOSTNAME"] == "${PUBLIC_URL:?err}/auth"
    assert keycloak["environment"]["KC_BOOTSTRAP_ADMIN_PASSWORD"] == "${KEYCLOAK_ADMIN_PASSWORD:?err}"
    assert "urllib.request" in " ".join(keycloak["healthcheck"]["test"])
    assert keycloak["depends_on"]["wait-for-resources"]["condition"] == "service_completed_successfully"
    assert keycloak_bundle["wait-for-resources"]["depends_on"]["keycloak-configurator"]["condition"] == (
        "service_started"
    )
    configurator = keycloak_bundle["keycloak-configurator"]
    assert configurator["environment"]["KEYCLOAK_URL"] == "http://keycloak:8080"
    assert "depends_on" not in configurator

    ngrok = artifacts["ngrok"]["services"]["ngrok"]
    assert ngrok["restart"] == "on-failure"
    assert ngrok["image"] == lock["NGROK_IMAGE"]
    command = " ".join(ngrok["entrypoint"])
    assert "exec ngrok http --domain=$${NGROK_DOMAIN:-}" in command
    assert "--upstream-protocol=http1" in command
    assert "http://door:8443" in command
