from __future__ import annotations

import os
import subprocess
from pathlib import Path

import httpx
import pytest

DEFAULT_API_CONTAINER = "placeframe-api-1"
DEFAULT_API_PORT = 8000
DEFAULT_REALM = "placeframe-dev"
DEFAULT_CLIENT_ID = "placeframe-api"
ENV_FILE_CANDIDATES = (Path("/placeframe/.env"), Path.cwd() / ".env")


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
