from __future__ import annotations

import threading
from asyncio import run
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from litestar.exceptions import HTTPException

from src.routers.localizer_router import UNAVAILABLE_DETAIL, resolve_localizer_address
from src.settings import get_settings
from test_settings import REQUIRED_ENV


class RouterStubHandler(BaseHTTPRequestHandler):
    response_body = '{"address": null}'

    def do_GET(self) -> None:
        if self.path != "/localizer-address":
            self.send_error(404)
            return
        body = self.response_body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: object) -> None:
        pass


@contextmanager
def router_stub(body: str) -> Iterator[str]:
    RouterStubHandler.response_body = body
    server = HTTPServer(("127.0.0.1", 0), RouterStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("GPU_MODE_MANAGED", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def configure(monkeypatch: pytest.MonkeyPatch, managed: str, address: str) -> None:
    monkeypatch.setenv("GPU_MODE_MANAGED", managed)
    monkeypatch.setenv("LOCALIZER_ROUTER_ADDRESS", address)
    get_settings.cache_clear()


def test_managed_query_returns_the_reported_address(monkeypatch: pytest.MonkeyPatch) -> None:
    with router_stub('{"address": "http://localizer:8000"}') as stub_url:
        configure(monkeypatch, "true", stub_url)

        assert run(resolve_localizer_address()) == "http://localizer:8000"


def test_managed_null_address_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    with router_stub('{"address": null}') as stub_url:
        configure(monkeypatch, "true", stub_url)

        with pytest.raises(HTTPException) as excinfo:
            run(resolve_localizer_address())

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == UNAVAILABLE_DETAIL


def test_managed_unreachable_router_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch, "true", "http://127.0.0.1:1")

    with pytest.raises(HTTPException) as excinfo:
        run(resolve_localizer_address())

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail == UNAVAILABLE_DETAIL


def test_unmanaged_forwards_directly_without_querying_the_router(monkeypatch: pytest.MonkeyPatch) -> None:
    with router_stub('{"address": null}') as stub_url:
        configure(monkeypatch, "false", stub_url)

        assert run(resolve_localizer_address()) == f"{stub_url}/"
