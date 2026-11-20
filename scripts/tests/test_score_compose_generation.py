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
    "mode-switcher",
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
    # Artifacts bake the decorated spelling; the lock records the upstream one
    lock = yaml.safe_load((REPO_ROOT / "boatyard.lock.yml").read_text(encoding="utf-8"))
    return f"ghcr.io/outernet-foundation/mirror/{lock['images'][name]['platforms']['linux/amd64']}"


def test_each_bundle_artifact_carries_services_under_the_project_name() -> None:
    for entry in ("core-cuda", "core-rocm", "auth-keycloak", "tunnel-ngrok"):
        artifact = _artifact(entry)
        assert artifact["services"], f"{entry} carries no services"
        assert artifact["name"] == "placeframe"


def test_every_service_is_bare_declares_no_network_and_is_hermetic() -> None:
    for entry in ("core-cuda", "core-rocm", "auth-keycloak", "tunnel-ngrok"):
        artifact = _artifact(entry)
        assert "networks" not in artifact, f"{entry} declares a network"
        for service_name, service in artifact["services"].items():
            assert "networks" not in service, f"{entry}/{service_name} declares a network attachment"
            assert "profiles" not in service, f"{entry}/{service_name} still declares compose profiles"
            assert "ports" not in service, f"{entry}/{service_name} still publishes a host port"
            for volume in service.get("volumes") or []:
                if volume.get("type") == "bind":
                    # The one audited exception: the mode switcher's Docker socket
                    assert service_name == "mode-switcher", f"{entry}/{service_name} carries a non-inlined bind"
                    assert volume["source"] == volume["target"] == "/var/run/docker.sock", (
                        f"{entry}/mode-switcher carries a bind other than the Docker socket"
                    )


def test_the_core_variants_carry_the_full_stack_each() -> None:
    for variant in ("cuda", "rocm"):
        assert set(_artifact(f"core-{variant}")["services"]) == CORE_SERVICES


def test_the_api_carries_soft_auth_slots_prod_safe_toggles_and_its_route_claim() -> None:
    api = _artifact("core-cuda")["services"]["api"]
    assert api["environment"]["AUTH_JWKS_URL"] == "${AUTH_JWKS_URL:-}"
    assert api["environment"]["DEBUG_API"] == "false"
    assert api["environment"]["SERVICE_PORT"] == "8000"
    assert api["annotations"]["boatyard/route"] == "/*"


def test_the_mode_switcher_claims_its_route_mounts_the_docker_socket_and_gates_the_barrier() -> None:
    for variant in ("cuda", "rocm"):
        artifact = _artifact(f"core-{variant}")
        switcher = artifact["services"]["mode-switcher"]
        assert switcher["annotations"]["boatyard/route"] == "/gpu-mode/*"
        assert switcher["annotations"]["boatyard/port"] == "8000"
        assert switcher["environment"]["LOCALIZER_URL"] == "http://localizer:8000", (
            "the localizer URL must derive from the localizer workload's service.ports declaration"
        )
        assert switcher["volumes"] == [
            {"type": "bind", "source": "/var/run/docker.sock", "target": "/var/run/docker.sock"}
        ]
        assert artifact["services"]["wait-for-resources"]["depends_on"]["mode-switcher"] == {
            "condition": "service_healthy",
            "required": True,
        }


def test_the_keycloak_bundle_pins_its_image_adopts_its_route_and_gates_boot() -> None:
    bundle = _artifact("auth-keycloak")["services"]
    assert set(bundle) == {"keycloak", "keycloak-configurator", "wait-for-resources"}

    keycloak = bundle["keycloak"]
    assert keycloak["image"] == _platform_manifest("KEYCLOAK_IMAGE")
    assert keycloak["annotations"]["boatyard/route"] == "/auth/*, strip"
    assert keycloak["annotations"]["boatyard/port"] == "8080"
    assert keycloak["environment"]["KC_HOSTNAME"] == "${PUBLIC_URL:?err}/auth"
    assert "${KEYCLOAK_ADMIN_PASSWORD:?err}" in list(keycloak["environment"].values())
    assert keycloak["healthcheck"]["test"][:3] == ["CMD", "bash", "-c"]
    assert "/dev/tcp/127.0.0.1/9000" in keycloak["healthcheck"]["test"][3]
    assert "/health/ready" in keycloak["healthcheck"]["test"][3]
    assert keycloak["depends_on"]["wait-for-resources"]["condition"] == "service_completed_successfully"
    assert bundle["wait-for-resources"]["depends_on"]["keycloak-configurator"]["condition"] == "service_started"

    configurator = bundle["keycloak-configurator"]
    assert configurator["environment"]["KEYCLOAK_URL"] == "http://keycloak:8080"
    assert "depends_on" not in configurator


def test_the_relay_restarts_on_failure_and_targets_the_gateway() -> None:
    ngrok = _artifact("tunnel-ngrok")["services"]["ngrok"]
    assert ngrok["restart"] == "on-failure"
    assert ngrok["image"] == _platform_manifest("NGROK_IMAGE")
    command = " ".join(ngrok["entrypoint"])
    assert "exec ngrok http --domain=$${NGROK_DOMAIN:-}" in command
    assert "--upstream-protocol=http1" in command
    assert "http://boatyard-gateway:8443" in command
