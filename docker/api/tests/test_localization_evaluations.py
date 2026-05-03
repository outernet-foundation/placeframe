from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import httpx
import pytest

DEFAULT_API_CONTAINER = "placeframe-api-1"
DEFAULT_API_PORT = 8000
DEFAULT_REALM = "placeframe-dev"
DEFAULT_CLIENT_ID = "placeframe-api"
ENV_FILE_CANDIDATES = (Path("/placeframe/.env"), Path.cwd() / ".env")


def _public_domain_from_env_file() -> str | None:
    for env_file in ENV_FILE_CANDIDATES:
        if not env_file.is_file():
            continue
        for line in env_file.read_text().splitlines():
            if line.startswith("PUBLIC_DOMAIN="):
                return line.split("=", 1)[1].strip()
    return None


def _resolve_api_base_url() -> str | None:
    env_url = os.environ.get("API_BASE_URL")
    if env_url:
        return env_url
    container = os.environ.get("API_CONTAINER", DEFAULT_API_CONTAINER)
    try:
        ip = subprocess.check_output(
            [
                "docker",
                "inspect",
                container,
                "-f",
                '{{ (index .NetworkSettings.Networks "placeframe_default").IPAddress }}',
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not ip:
        return None
    return f"http://{ip}:{DEFAULT_API_PORT}"


def _resolve_auth_base_url() -> str | None:
    explicit = os.environ.get("AUTH_BASE_URL")
    if explicit:
        return explicit
    public_domain = os.environ.get("PUBLIC_DOMAIN") or _public_domain_from_env_file()
    if public_domain:
        return f"https://{public_domain}/auth"
    return None


def _fetch_access_token(auth_base_url: str) -> str | None:
    url = f"{auth_base_url}/realms/{DEFAULT_REALM}/protocol/openid-connect/token"
    try:
        resp = httpx.post(
            url,
            data={
                "grant_type": "password",
                "client_id": DEFAULT_CLIENT_ID,
                "username": os.environ.get("PLACEFRAME_TEST_USER", "user"),
                "password": os.environ.get("PLACEFRAME_TEST_PASSWORD", "password"),
                "scope": "openid",
            },
            timeout=10.0,
        )
    except httpx.RequestError:
        return None
    if resp.status_code != 200:
        return None
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def api_client() -> httpx.Client:
    base_url = _resolve_api_base_url()
    if base_url is None:
        pytest.skip("API not reachable; set API_BASE_URL or run inside the placeframe stack")
    auth_base_url = _resolve_auth_base_url()
    if auth_base_url is None:
        pytest.skip("Auth not reachable; set AUTH_BASE_URL or PUBLIC_DOMAIN")
    token = _fetch_access_token(auth_base_url)
    if token is None:
        pytest.skip("Could not obtain Keycloak token; check PLACEFRAME_TEST_USER/PASSWORD env")
    return httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {token}"}, timeout=30.0)


@pytest.fixture(scope="module")
def reconstruction_id(api_client: httpx.Client) -> str:
    capture = api_client.post(
        "/capture_sessions",
        json={"name": f"pytest-loceval-{uuid.uuid4()}", "device_type": "Zed"},
    )
    capture.raise_for_status()
    capture_session_id = capture.json()["id"]

    recon = api_client.post(
        "/reconstructions",
        json={"create": {"capture_session_id": capture_session_id}},
    )
    recon.raise_for_status()
    return recon.json()["id"]


@pytest.fixture
def pipeline_version() -> str:
    return f"pytest-{uuid.uuid4()}"


def _evaluation_body(
    reconstruction_id: str, pipeline_version: str, frame_timestamp: int, *, succeeded: bool, num_inliers: int = 60
) -> dict[str, object]:
    body: dict[str, object] = {
        "reconstruction_id": reconstruction_id,
        "frame_timestamp": frame_timestamp,
        "retrieval_top_k": 10,
        "ransac_threshold": 8.0,
        "pipeline_version": pipeline_version,
        "succeeded": succeeded,
        "num_correspondences": 100,
        "num_matches": 80,
        "num_inliers": num_inliers,
        "inlier_ratio": num_inliers / 100.0,
        "inlier_coverage": 0.5,
        "reproj_error_median": 1.2,
        "query_image_diagonal_px": 1414.2,
    }
    if succeeded:
        body["err_t_m"] = 0.05
        body["err_r_deg"] = 0.8
        body["se3_residual"] = [0.01, 0.02, 0.03, 0.001, 0.002, 0.003]
        body["pnp_covariance"] = [0.1] * 36
    return body


def test_post_creates_row_and_returns_read_dto(api_client: httpx.Client, reconstruction_id: str, pipeline_version: str):
    body = _evaluation_body(reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_001, succeeded=True)
    resp = api_client.post(f"/reconstructions/{reconstruction_id}/localization-evaluations", json=body)
    assert resp.status_code == 201, resp.text
    row = resp.json()
    assert row["reconstruction_id"] == reconstruction_id
    assert row["pipeline_version"] == pipeline_version
    assert row["num_inliers"] == 60
    assert row["succeeded"] is True
    assert row["err_t_m"] == pytest.approx(0.05)
    assert len(row["pnp_covariance"]) == 36
    assert len(row["se3_residual"]) == 6


def test_post_same_key_upserts_overwriting_value_columns(
    api_client: httpx.Client, reconstruction_id: str, pipeline_version: str
):
    initial = _evaluation_body(
        reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_002, succeeded=True, num_inliers=40
    )
    first = api_client.post(f"/reconstructions/{reconstruction_id}/localization-evaluations", json=initial).json()

    updated = _evaluation_body(
        reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_002, succeeded=True, num_inliers=99
    )
    second = api_client.post(f"/reconstructions/{reconstruction_id}/localization-evaluations", json=updated).json()

    assert second["id"] == first["id"], "upsert must reuse the row id, not allocate a new one"
    assert second["num_inliers"] == 99
    assert second["inlier_ratio"] == pytest.approx(0.99)


def test_different_pipeline_version_creates_distinct_row(
    api_client: httpx.Client, reconstruction_id: str, pipeline_version: str
):
    other_version = f"{pipeline_version}-alt"
    api_client.post(
        f"/reconstructions/{reconstruction_id}/localization-evaluations",
        json=_evaluation_body(reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_003, succeeded=True),
    ).raise_for_status()
    api_client.post(
        f"/reconstructions/{reconstruction_id}/localization-evaluations",
        json=_evaluation_body(reconstruction_id, other_version, frame_timestamp=1_700_000_000_003, succeeded=False),
    ).raise_for_status()

    resp = api_client.get(f"/reconstructions/{reconstruction_id}/localization-evaluations")
    resp.raise_for_status()
    rows = resp.json()
    versions = {r["pipeline_version"] for r in rows if r["frame_timestamp"] == 1_700_000_000_003}
    assert {pipeline_version, other_version}.issubset(versions)


def test_get_filters_by_pipeline_version(api_client: httpx.Client, reconstruction_id: str, pipeline_version: str):
    other_version = f"{pipeline_version}-alt"
    api_client.post(
        f"/reconstructions/{reconstruction_id}/localization-evaluations",
        json=_evaluation_body(reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_004, succeeded=True),
    ).raise_for_status()
    api_client.post(
        f"/reconstructions/{reconstruction_id}/localization-evaluations",
        json=_evaluation_body(reconstruction_id, other_version, frame_timestamp=1_700_000_000_004, succeeded=False),
    ).raise_for_status()

    resp = api_client.get(
        f"/reconstructions/{reconstruction_id}/localization-evaluations",
        params={"pipeline_version": pipeline_version},
    )
    resp.raise_for_status()
    rows = resp.json()
    matching = [r for r in rows if r["frame_timestamp"] == 1_700_000_000_004]
    assert len(matching) == 1
    assert matching[0]["pipeline_version"] == pipeline_version


def test_failed_evaluation_persists_without_truth_labels(
    api_client: httpx.Client, reconstruction_id: str, pipeline_version: str
):
    body = _evaluation_body(reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_005, succeeded=False)
    resp = api_client.post(f"/reconstructions/{reconstruction_id}/localization-evaluations", json=body)
    assert resp.status_code == 201, resp.text
    row = resp.json()
    assert row["succeeded"] is False
    assert row["err_t_m"] is None
    assert row["err_r_deg"] is None
    assert row["se3_residual"] is None
    assert row["pnp_covariance"] is None


def test_post_path_id_must_match_body_id(api_client: httpx.Client, reconstruction_id: str, pipeline_version: str):
    other_id = "00000000-0000-0000-0000-000000000000"
    body = _evaluation_body(reconstruction_id, pipeline_version, frame_timestamp=1_700_000_000_006, succeeded=True)
    resp = api_client.post(f"/reconstructions/{other_id}/localization-evaluations", json=body)
    assert resp.status_code == 400, resp.text
