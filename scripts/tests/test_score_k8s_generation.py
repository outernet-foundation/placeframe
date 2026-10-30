from importlib.metadata import version
from pathlib import Path
from shutil import which

import pytest
import yaml
from packaging.version import Version

from docker_devkit.config import LOCK_PATH, load_config
from docker_devkit.documents import compute_service_shas, parse_image_lock
from docker_devkit.score_generate import generate_k8s

REPO_ROOT = Path(__file__).resolve().parents[2]

# The generated k8s sources need the services vocabulary.
_required_devkit = Version("0.5.5")
pytestmark = [
    pytest.mark.skipif(which("score-k8s") is None, reason="pinned score-k8s not on PATH"),
    pytest.mark.skipif(
        Version(version("docker-devkit")) < _required_devkit
        and Version(version("docker-devkit")) != Version("0.0.0.dev0"),
        reason=f"docker-devkit >= {_required_devkit} required for the root-config variant fields",
    ),
]


def _generate_k8s_without_charts(output: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, dict]:
    # The committed chart refs fetch through the org mirror, which CI has not populated;
    # stripping charts exercises everything else — provisioners, patch templates,
    # placeholder expansion — against the real sources. The KEDA operator is cluster
    # tier (infra/Pulumi), so the artifact carries only the ScaledObject and
    # TriggerAuthentication CRs.
    config = load_config(REPO_ROOT)
    assert config is not None and config.k8s is not None
    chartless = config.model_copy(update={"k8s": config.k8s.model_copy(update={"charts": {}})})

    for name, value in compute_service_shas(REPO_ROOT, config).items():
        monkeypatch.setenv(name, value)

    generate_k8s(REPO_ROOT, chartless, output, parse_image_lock(REPO_ROOT / LOCK_PATH).root)
    documents = {}
    for document in yaml.safe_load_all(output.read_text(encoding="utf-8")):
        if document:
            documents[f"{document['kind']}/{document['metadata']['name']}"] = document
    return documents


def test_k8s_generation_patches_gpu_workloads_and_renders_keda_crs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documents = _generate_k8s_without_charts(tmp_path / "manifests.yaml", monkeypatch)

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


def test_k8s_generation_renders_the_tier_neutral_keycloak_deployment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documents = _generate_k8s_without_charts(tmp_path / "manifests.yaml", monkeypatch)
    lock = parse_image_lock(REPO_ROOT / LOCK_PATH).root

    keycloak = documents["Deployment/keycloak"]
    container = keycloak["spec"]["template"]["spec"]["containers"][0]
    assert container["image"] == lock["KEYCLOAK_IMAGE"]
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
