from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from json import loads

from typer.testing import CliRunner

from scripts.gpu_mode import app

runner = CliRunner()


class ModeSwitcherStubHandler(BaseHTTPRequestHandler):
    status = 200
    response_body = '{"mode": "reconstruction"}'

    def do_POST(self) -> None:
        if self.path != "/gpu-mode/mode":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.response_body.encode()
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        server = self.server
        assert isinstance(server, RecordingHTTPServer)
        server.requests.append((self.path, self.rfile.read(length)))
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: object) -> None:
        pass


class RecordingHTTPServer(HTTPServer):
    def __init__(self, address: tuple[str, int]) -> None:
        super().__init__(address, ModeSwitcherStubHandler)
        self.requests: list[tuple[str, bytes]] = []


@contextmanager
def mode_switcher_stub(status: int = 200) -> Iterator[RecordingHTTPServer]:
    ModeSwitcherStubHandler.status = status
    server = RecordingHTTPServer(("127.0.0.1", 0))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join()


def public_env(server: RecordingHTTPServer) -> dict[str, str]:
    return {"PUBLIC_URL": f"http://127.0.0.1:{server.server_address[1]}"}


def test_gpu_mode_posts_the_requested_mode() -> None:
    with mode_switcher_stub() as server:
        result = runner.invoke(app, ["reconstruction"], env=public_env(server))

    assert result.exit_code == 0
    assert "reconstruction" in result.output
    assert [(path, loads(body)) for path, body in server.requests] == [("/gpu-mode/mode", {"mode": "reconstruction"})]


def test_gpu_mode_fails_cleanly_when_the_switcher_errors() -> None:
    with mode_switcher_stub(status=500) as server:
        result = runner.invoke(app, ["localization"], env=public_env(server))

    assert result.exit_code == 1
    assert "Failed to reach the mode switcher" in result.output


def test_gpu_mode_help_lists_both_modes() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "localization" in result.output
    assert "reconstruction" in result.output
