from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket
from sys import stderr
from time import monotonic, sleep

# The SDK reaches the sensors through all three: argus_socket is nvargus-daemon;
# nvscsock and camsock are the zed_x_daemon (GMSL) sockets. Waiting only on argus
# lets a Camera.open race zed_x_daemon, which surfaces as "Failed to connect to
# zed_x_daemon" / CAMERA STREAM FAILED TO START.
CAMERA_SOCKETS = (Path("/tmp/argus_socket"), Path("/tmp/nvscsock"), Path("/tmp/camsock"))
VIDEO_NODES = (Path("/dev/video0"), Path("/dev/video1"))
TIMEOUT_SECONDS = 60.0
POLL_INTERVAL_SECONDS = 0.5


def socket_ready(path: Path) -> str | None:
    try:
        connection = socket(AF_UNIX, SOCK_STREAM)
        connection.settimeout(1.0)
        connection.connect(str(path))
        connection.close()
    except FileNotFoundError:
        return f"{path} does not exist yet"
    except ConnectionRefusedError:
        return f"{path} exists but is not accepting connections (stale inode or daemon not bound)"
    return None


def main() -> int:
    deadline = monotonic() + TIMEOUT_SECONDS
    last_error: str | None = None
    while monotonic() < deadline:
        socket_errors = [error for path in CAMERA_SOCKETS if (error := socket_ready(path)) is not None]
        missing_nodes = [str(node) for node in VIDEO_NODES if not node.exists()]
        if not socket_errors and not missing_nodes:
            return 0
        last_error = next(iter(socket_errors), None) or f"V4L2 device nodes not yet present: {', '.join(missing_nodes)}"
        sleep(POLL_INTERVAL_SECONDS)

    print(
        f"timed out after {TIMEOUT_SECONDS:.0f}s waiting for ZED camera readiness: {last_error}",
        file=stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
