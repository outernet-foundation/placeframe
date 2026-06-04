from __future__ import annotations

import io
import json
import os
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

import httpx
import pytest

DEFAULT_API_CONTAINER = "placeframe-api-1"
DEFAULT_API_PORT = 8000
DEFAULT_REALM = "placeframe-dev"
DEFAULT_CLIENT_ID = "placeframe-api"
ENV_FILE_CANDIDATES = (Path("/placeframe/.env"), Path.cwd() / ".env")

# 1×1 JPEG (smallest valid baseline JPEG; produced by `convert -size 1x1 xc:black -quality 10 out.jpg`)
MINIMAL_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912"
    "130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffdb004301090909"
    "0c0b0c180d0d1832211c213232323232323232323232323232323232323232323232323232323232323232323232323232"
    "32323232323232323232323232ffc00011080001000103012200021101031101ffc4001f0000010501010101010100000000"
    "00000000010203040506070809000a0bffc400b5100002010303020403050504040000017d010203000411051221314106"
    "1361227181143291a1b1c109233352f1156272d10a162434e125f11718191a262728292a3536373839"
)


def _public_url_from_env_file() -> str | None:
    for env_file in ENV_FILE_CANDIDATES:
        if not env_file.is_file():
            continue
        for line in env_file.read_text().splitlines():
            if line.startswith("PUBLIC_URL="):
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
    public_url = os.environ.get("PUBLIC_URL") or _public_url_from_env_file()
    if public_url:
        return f"{public_url}/auth"
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
        pytest.skip("Auth not reachable; set AUTH_BASE_URL or PUBLIC_URL")
    token = _fetch_access_token(auth_base_url)
    if token is None:
        pytest.skip("Could not obtain Keycloak token; check PLACEFRAME_TEST_USER/PASSWORD env")
    return httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {token}"}, timeout=60.0)


def _build_capture_tar(timestamps_ms: list[int], image_bytes: bytes) -> bytes:
    manifest = {"axis_convention": "OPENCV", "rigs": []}
    frames_csv = "timestamp,tx,ty,tz,qx,qy,qz,qw\n"
    for i, ts in enumerate(timestamps_ms):
        frames_csv += f"{ts},{i * 0.1},{0.0},{0.0},0,0,0,1\n"

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        manifest_bytes = json.dumps(manifest).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        info.mtime = int(time.time())
        tf.addfile(info, io.BytesIO(manifest_bytes))

        frames_bytes = frames_csv.encode("utf-8")
        info = tarfile.TarInfo(name="rig0/frames.csv")
        info.size = len(frames_bytes)
        info.mtime = int(time.time())
        tf.addfile(info, io.BytesIO(frames_bytes))

        for ts in timestamps_ms:
            info = tarfile.TarInfo(name=f"rig0/camera0/{ts}.jpg")
            info.size = len(image_bytes)
            info.mtime = int(time.time())
            tf.addfile(info, io.BytesIO(image_bytes))

    return buf.getvalue()


@pytest.fixture(scope="module")
def capture_with_tar(api_client: httpx.Client) -> tuple[str, list[int], bytes, bytes]:
    timestamps_ms = [1_700_000_000_001, 1_700_000_000_002, 1_700_000_000_003]
    tar_bytes = _build_capture_tar(timestamps_ms, MINIMAL_JPEG)

    capture = api_client.post(
        "/capture_sessions",
        data={"name": f"pytest-artifacts-{uuid.uuid4()}", "device_type": "Zed"},
        files={"data": ("capture.tar", tar_bytes, "application/x-tar")},
    )
    capture.raise_for_status()
    capture_id = capture.json()["id"]

    expected_csv = "timestamp,tx,ty,tz,qx,qy,qz,qw\n" + "".join(
        f"{ts},{i * 0.1},{0.0},{0.0},0,0,0,1\n" for i, ts in enumerate(timestamps_ms)
    )
    return capture_id, timestamps_ms, expected_csv.encode("utf-8"), MINIMAL_JPEG


def test_get_manifest_returns_manifest_json(api_client: httpx.Client, capture_with_tar):
    capture_id, *_ = capture_with_tar
    resp = api_client.get(f"/capture_sessions/{capture_id}/manifest.json")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/json")
    parsed = json.loads(resp.content)
    assert parsed["axis_convention"] == "OPENCV"
    assert parsed["rigs"] == []


def test_get_frames_csv_returns_csv_bytes(api_client: httpx.Client, capture_with_tar):
    capture_id, _, expected_csv, _ = capture_with_tar
    resp = api_client.get(f"/capture_sessions/{capture_id}/frames.csv")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert resp.content == expected_csv


def test_get_image_returns_jpeg_bytes(api_client: httpx.Client, capture_with_tar):
    capture_id, timestamps_ms, _, expected_image = capture_with_tar
    resp = api_client.get(f"/capture_sessions/{capture_id}/images/{timestamps_ms[1]}")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("image/jpeg")
    assert resp.content == expected_image


def test_get_image_for_unknown_timestamp_returns_404(api_client: httpx.Client, capture_with_tar):
    capture_id, *_ = capture_with_tar
    resp = api_client.get(f"/capture_sessions/{capture_id}/images/999999999")
    assert resp.status_code == 404, resp.text


def test_get_frames_csv_for_unknown_capture_returns_404(api_client: httpx.Client):
    missing_id = "00000000-0000-0000-0000-000000000000"
    resp = api_client.get(f"/capture_sessions/{missing_id}/frames.csv")
    assert resp.status_code == 404, resp.text
