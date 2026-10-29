from importlib.metadata import version
from pathlib import Path
from shutil import which

import pytest
import yaml
from packaging.version import Version

from docker_devkit.config import load_config
from docker_devkit.documents import compute_service_shas, parse_bake
from docker_devkit.lifecycle import LOCK_PATH, require_manifest
from docker_devkit.score_generate import generate_k8s

REPO_ROOT = Path(__file__).resolve().parents[2]

# The generated k8s sources need the variant config fields.
_required_devkit = Version("0.4.11")
pytestmark = [
    pytest.mark.skipif(which("score-k8s") is None, reason="pinned score-k8s not on PATH"),
    pytest.mark.skipif(
        Version(version("docker-devkit")) < _required_devkit
        and Version(version("docker-devkit")) != Version("0.0.0.dev0"),
        reason=f"docker-devkit >= {_required_devkit} required for the variant fields",
    ),
]


def _generate_k8s_without_charts(output: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, dict]:
    # The committed chart refs fetch through the org mirror, which CI has not populated;
    # stripping charts exercises everything else — provisioners, patch templates,
    # placeholder expansion — against the real sources. The KEDA operator is cluster
    # tier (infra/Pulumi), so the artifact carries only the ScaledObject and
    # TriggerAuthentication CRs.
    config = load_config(REPO_ROOT)
    assert config is not None and config.generate_score is not None
    chartless = config.generate_score.model_copy(update={"charts": []})

    for name, value in compute_service_shas(REPO_ROOT, parse_bake(require_manifest(REPO_ROOT))).items():
        monkeypatch.setenv(name, value)

    lock_images: dict[str, str] = {}
    for line in (REPO_ROOT / LOCK_PATH).read_text(encoding="utf-8").splitlines():
        name, separator, reference = line.partition("=")
        if separator and name.strip() and not name.startswith("#"):
            lock_images[name.strip()] = reference

    generate_k8s(REPO_ROOT, chartless, output, None, lock_images)
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
