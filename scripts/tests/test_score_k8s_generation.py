from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _documents() -> dict[str, dict]:
    return {
        f"{document['kind']}/{document['metadata']['name']}": document
        for document in yaml.safe_load_all(
            (REPO_ROOT / "stack" / "generated" / "k8s" / "manifests.yaml").read_text(encoding="utf-8")
        )
        if document
    }


def _index_reference(name: str) -> str:
    lock = yaml.safe_load((REPO_ROOT / "boatyard.lock.yml").read_text(encoding="utf-8"))
    return lock["images"][name]["index"]


def test_gpu_workloads_carry_the_nvidia_contract_and_scale_to_zero() -> None:
    documents = _documents()

    reconstructor = documents["Deployment/reconstructor"]
    reconstructor_spec = reconstructor["spec"]["template"]["spec"]
    assert reconstructor_spec["runtimeClassName"] == "nvidia"
    assert reconstructor_spec["nodeSelector"] == {"placeframe.io/gpu": "true"}
    assert reconstructor_spec["containers"][0]["resources"]["limits"] == {"nvidia.com/gpu": "1"}
    assert reconstructor["spec"]["replicas"] == 0
    lease_url = next(
        variable["value"]
        for variable in reconstructor_spec["containers"][0]["env"]
        if variable["name"] == "LEASE_SERVER_URL"
    )
    assert lease_url == "http://lease-server:8000"

    localizer = documents["Deployment/localizer"]
    localizer_spec = localizer["spec"]["template"]["spec"]
    assert localizer_spec["runtimeClassName"] == "nvidia"
    assert localizer_spec["nodeSelector"] == {"placeframe.io/gpu": "true"}
    assert localizer_spec["containers"][0]["resources"]["limits"] == {"nvidia.com/gpu": "1"}
    assert "replicas" not in localizer["spec"]

    api_spec = documents["Deployment/api"]["spec"]["template"]["spec"]
    assert "runtimeClassName" not in api_spec
    localizer_url = next(
        variable["value"]
        for variable in api_spec["containers"][0]["env"]
        if variable["name"] == "LOCALIZER_CONTAINER_URL"
    )
    assert localizer_url == "http://localizer:8000"


def test_keda_crs_derive_from_the_declared_resource() -> None:
    documents = _documents()

    scaled_object = documents["ScaledObject/reconstructor"]
    trigger = scaled_object["spec"]["triggers"][0]
    assert trigger["type"] == "postgresql"
    assert trigger["metadata"]["host"] == "pf-postgres"
    assert trigger["metadata"]["userName"] == "placeframe_orchestration_user"
    assert trigger["authenticationRef"]["name"] == "reconstructor-pg-trigger"
    assert scaled_object["spec"]["minReplicaCount"] == 0
    assert scaled_object["spec"]["cooldownPeriod"] == 300

    authentication = documents["TriggerAuthentication/reconstructor-pg-trigger"]
    assert authentication["spec"]["secretTargetRef"] == [
        {"parameter": "password", "name": "placeframe-secrets", "key": "DATABASE_ORCHESTRATION_USER_PASSWORD"}
    ]

    assert "Deployment/keda-operator" not in documents


def test_keycloak_renders_tier_neutral() -> None:
    documents = _documents()

    keycloak = documents["Deployment/keycloak"]
    container = keycloak["spec"]["template"]["spec"]["containers"][0]
    assert container["image"] == _index_reference("KEYCLOAK_IMAGE")
    assert container["readinessProbe"]["httpGet"] == {"path": "/health/ready", "port": 9000}
    env = {variable["name"]: variable for variable in container["env"]}
    assert env["KC_BOOTSTRAP_ADMIN_PASSWORD"]["valueFrom"]["secretKeyRef"]["key"] == "KEYCLOAK_ADMIN_PASSWORD"
    assert env["KC_HOSTNAME"]["valueFrom"]["secretKeyRef"]["key"] == "KEYCLOAK_HOSTNAME"

    realm_job = documents["Job/keycloak-realm"]
    job_env = {variable["name"]: variable for variable in realm_job["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert job_env["KEYCLOAK_URL"]["value"] == "http://keycloak:8080"

    assert documents["Service/keycloak"]["spec"]["ports"][0]["port"] == 8080
    assert "Keycloak/keycloak" not in documents
    assert not [name for name in documents if name.startswith("Service/") and name.endswith("-service")]
    assert not [name for name in documents if "keycloak-operator" in name]
