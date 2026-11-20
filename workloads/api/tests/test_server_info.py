from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator

import httpx
import pytest
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient
from placeframe_common.litestar import create_litestar_app

from src.routers.server_info import router as server_info_router
from src.settings import get_settings
from test_settings import KEYCLOAK_ENV, REQUIRED_ENV, apply_env

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
    assert isinstance(body["gpu_mode_managed"], bool)

    # The internal JWKS hostname (auth_certs_url) is server-side only and must never reach a client.
    assert "certs_url" not in body

    if body["auth_mode"] == "disabled":
        assert body["token_url"] is None
        assert body["audience"] is None
    else:
        assert body["token_url"]
        assert body["audience"]


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    yield
    get_settings.cache_clear()


def _configure(monkeypatch: pytest.MonkeyPatch, keycloak: bool, managed: str) -> None:
    apply_env(monkeypatch, REQUIRED_ENV)
    monkeypatch.setenv("GPU_MODE_MANAGED", managed)
    if keycloak:
        apply_env(monkeypatch, KEYCLOAK_ENV)

    get_settings.cache_clear()


def make_client() -> TestClient[Litestar]:
    app = create_litestar_app([server_info_router], OpenAPIConfig("Placeframe", "0.1.0"), logging_config=None)
    return TestClient(app=app)


def test_server_info_reports_gpu_mode_managed_anonymous(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure(monkeypatch, keycloak=False, managed="true")

    with make_client() as client:
        response = client.get("/server-info")

    assert response.status_code == 200
    body = response.json()
    assert body["auth_mode"] == "disabled"
    assert body["gpu_mode_managed"] is True


def test_server_info_reports_gpu_mode_managed_keycloak(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure(monkeypatch, keycloak=True, managed="false")

    with make_client() as client:
        response = client.get("/server-info")

    assert response.status_code == 200
    body = response.json()
    assert body["auth_mode"] == "keycloak"
    assert body["gpu_mode_managed"] is False
