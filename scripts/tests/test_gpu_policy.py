from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from json import loads

import pytest
import typer
from typer.testing import CliRunner

from scripts.gpu_policy import app, parse_duration

runner = CliRunner()

STATE_BODY = (
    '{"running": ["localizer"], "managed": ["localizer", "reconstructor"], '
    '"localization_demand_active": true, "reconstruction_demand_active": false, '
    '"queued": 2, "in_flight": 0, "gpu_contended": true, "idle_window_seconds": 600, '
    '"poll_interval_seconds": 15, "last_pass_at": "2026-11-21T00:00:00+00:00"}'
)


class OrchestratorStubHandler(BaseHTTPRequestHandler):
    patch_status = 200
    patch_body = '{"idle_window_seconds": 1800, "poll_interval_seconds": 15}'

    def do_GET(self) -> None:
        if self.path != "/state":
            self.send_error(404)
            return
        body = STATE_BODY.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PATCH(self) -> None:
        if self.path != "/policy":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        server = self.server
        assert isinstance(server, RecordingHTTPServer)
        server.requests.append((self.path, self.rfile.read(length)))
        body = self.patch_body.encode()
        self.send_response(self.patch_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: object) -> None:
        pass


class RecordingHTTPServer(HTTPServer):
    def __init__(self, address: tuple[str, int]) -> None:
        super().__init__(address, OrchestratorStubHandler)
        self.requests: list[tuple[str, bytes]] = []


@contextmanager
def orchestrator_stub(patch_status: int = 200, patch_body: str | None = None) -> Iterator[RecordingHTTPServer]:
    if patch_body is not None:
        OrchestratorStubHandler.patch_body = patch_body
    OrchestratorStubHandler.patch_status = patch_status
    server = RecordingHTTPServer(("127.0.0.1", 0))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join()


def orchestrator_env(server: RecordingHTTPServer) -> dict[str, str]:
    return {"GPU_ORCHESTRATOR_URL": f"http://127.0.0.1:{server.server_address[1]}"}


@pytest.mark.parametrize(
    ("spelling", "expected"),
    [("45", 45), ("45s", 45), ("30m", 1800), ("2h", 7200), ("  60s  ", 60)],
)
def test_parse_duration_normalizes_spellings(spelling: str, expected: int) -> None:
    assert parse_duration(spelling) == expected


@pytest.mark.parametrize("spelling", ["10x", "abc", "-5", "", "1.5s", "m"])
def test_parse_duration_rejects_non_spellings(spelling: str) -> None:
    with pytest.raises(typer.BadParameter):
        parse_duration(spelling)


def test_set_patches_normalized_durations() -> None:
    with orchestrator_stub() as server:
        result = runner.invoke(
            app, ["set", "--idle-window", "30m", "--poll-interval", "45s"], env=orchestrator_env(server)
        )

    assert result.exit_code == 0
    assert [(path, loads(body)) for path, body in server.requests] == [
        ("/policy", {"idle_window_seconds": 1800, "poll_interval_seconds": 45})
    ]
    assert "idle_window_seconds: 1800" in result.output


def test_set_reports_a_floor_rejection_and_exits_non_zero() -> None:
    with orchestrator_stub(
        patch_status=400, patch_body='{"detail": "idle_window_seconds must be at least 60"}'
    ) as server:
        result = runner.invoke(app, ["set", "--idle-window", "30s"], env=orchestrator_env(server))

    assert result.exit_code == 1
    assert "rejected the policy" in result.output
    assert "must be at least 60" in result.output


def test_set_without_options_exits_non_zero() -> None:
    result = runner.invoke(app, ["set"])

    assert result.exit_code == 2
    assert "Nothing to set" in result.output


def test_status_pretty_prints_the_state_report() -> None:
    with orchestrator_stub() as server:
        result = runner.invoke(app, ["status"], env=orchestrator_env(server))

    assert result.exit_code == 0
    assert "running: localizer" in result.output
    assert "managed: localizer, reconstructor" in result.output
    assert "idle_window_seconds: 600" in result.output


def test_unreachable_orchestrator_exits_non_zero() -> None:
    result = runner.invoke(app, ["status"], env={"GPU_ORCHESTRATOR_URL": "http://127.0.0.1:1"})

    assert result.exit_code == 1
    assert "Failed to reach the gpu orchestrator" in result.output
