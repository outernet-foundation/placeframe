from __future__ import annotations

import os
import subprocess

import httpx
import pytest

DEFAULT_API_CONTAINER = "placeframe-api-1"
DEFAULT_API_PORT = 8000


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


@pytest.fixture(scope="module")
def base_url() -> str:
    url = _resolve_api_base_url()
    if url is None:
        pytest.skip("API not reachable; set API_BASE_URL or run inside the placeframe stack")
    return url


def test_server_info_is_unauthenticated_and_typed(base_url: str) -> None:
    response = httpx.get(f"{base_url}/server-info", timeout=10.0)

    assert response.status_code == 200
    body = response.json()

    assert body["auth_mode"] in ("keycloak", "disabled")

    # The internal JWKS hostname (auth_certs_url) is server-side only and must never reach a client.
    assert "certs_url" not in body

    if body["auth_mode"] == "disabled":
        assert body["token_url"] is None
        assert body["audience"] is None
    else:
        assert body["token_url"]
        assert body["audience"]
