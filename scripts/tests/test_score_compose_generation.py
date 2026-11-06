from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_DIR = REPO_ROOT / "stack" / "generated" / "compose"

CORE_SERVICES = {
    "api",
    "lease-server",
    "reconstructor",
    "localizer",
    "alloy",
    "grafana",
    "initialize-loki",
    "initialize-s3",
    "loki",
    "pf-postgres",
    "pf-postgres-create",
    "pf-postgres-migrate",
    "seaweedfs",
    "seaweedfs-admin",
    "seaweedfs-audit",
    "wait-for-resources",
}


def _artifact(entry: str) -> dict[str, dict]:
    return yaml.safe_load((COMPOSE_DIR / f"compose.{entry}.yaml").read_text(encoding="utf-8"))


def _platform_manifest(name: str) -> str:
    lock = yaml.safe_load((REPO_ROOT / "boatyard.lock.yml").read_text(encoding="utf-8"))
    return lock["images"][name]["platforms"]["linux/amd64"]


def test_each_bundle_artifact_carries_services_under_the_project_name() -> None:
    for entry in ("core-cuda", "core-rocm", "auth-keycloak", "tunnel-ngrok"):
        artifact = _artifact(entry)
        assert artifact["services"], f"{entry} carries no services"
        assert artifact["name"] == "placeframe"


def test_every_service_is_entry_namespaced_with_a_bare_alias_and_hermetic() -> None:
    for entry in ("core-cuda", "core-rocm", "auth-keycloak", "tunnel-ngrok"):
        artifact = _artifact(entry)
        for service_name, service in artifact["services"].items():
            assert service_name.startswith(f"{entry}-"), f"{entry}: {service_name} is not namespaced"
            assert "profiles" not in service, f"{entry}/{service_name} still declares compose profiles"
            assert "ports" not in service, f"{entry}/{service_name} still publishes a host port"
            for volume in service.get("volumes") or []:
                assert volume.get("type") != "bind", f"{entry}/{service_name} carries a non-inlined bind"
            aliases = service["networks"][f"{entry}-net"]["aliases"]
            assert service_name.removeprefix(f"{entry}-") in aliases, f"{entry}/{service_name} lacks its bare alias"


def test_the_core_variants_carry_the_full_stack_each() -> None:
    for variant in ("cuda", "rocm"):
        services = _artifact(f"core-{variant}")["services"]
        assert {name.removeprefix(f"core-{variant}-") for name in services} == CORE_SERVICES


def test_the_api_carries_soft_auth_slots_and_prod_safe_toggles() -> None:
    api = _artifact("core-cuda")["services"]["core-cuda-api"]
    assert api["environment"]["AUTH_JWKS_URL"] == "${AUTH_JWKS_URL:-}"
    assert api["environment"]["DEBUG_API"] == "false"


def test_the_keycloak_bundle_pins_its_image_from_the_lock_and_gates_boot() -> None:
    bundle = _artifact("auth-keycloak")["services"]
    assert set(bundle) == {
        "auth-keycloak-keycloak",
        "auth-keycloak-keycloak-configurator",
        "auth-keycloak-wait-for-resources",
    }

    keycloak = bundle["auth-keycloak-keycloak"]
    assert keycloak["image"] == _platform_manifest("KEYCLOAK_IMAGE")
    assert keycloak["environment"]["KC_HOSTNAME"] == "${PUBLIC_URL:?err}/auth"
    assert "${KEYCLOAK_ADMIN_PASSWORD:?err}" in list(keycloak["environment"].values())
    assert keycloak["healthcheck"]["test"][:3] == ["CMD", "bash", "-c"]
    assert "/dev/tcp/127.0.0.1/9000" in keycloak["healthcheck"]["test"][3]
    assert "/health/ready" in keycloak["healthcheck"]["test"][3]
    assert keycloak["depends_on"]["auth-keycloak-wait-for-resources"]["condition"] == "service_completed_successfully"
    assert (
        bundle["auth-keycloak-wait-for-resources"]["depends_on"]["auth-keycloak-keycloak-configurator"]["condition"]
        == "service_started"
    )

    configurator = bundle["auth-keycloak-keycloak-configurator"]
    assert configurator["environment"]["KEYCLOAK_URL"] == "http://keycloak:8080"
    assert "depends_on" not in configurator


def test_the_relay_restarts_on_failure_and_targets_the_edge() -> None:
    ngrok = _artifact("tunnel-ngrok")["services"]["tunnel-ngrok-ngrok"]
    assert ngrok["restart"] == "on-failure"
    assert ngrok["image"] == _platform_manifest("NGROK_IMAGE")
    command = " ".join(ngrok["entrypoint"])
    assert "exec ngrok http --domain=$${NGROK_DOMAIN:-}" in command
    assert "--upstream-protocol=http1" in command
    assert "http://edge:8443" in command
