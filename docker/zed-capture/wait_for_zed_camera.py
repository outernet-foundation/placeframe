from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket
from sys import stderr
from time import monotonic, sleep

ARGUS_SOCKET = Path("/tmp/argus_socket")
VIDEO_NODES = (Path("/dev/video0"), Path("/dev/video1"))
TIMEOUT_SECONDS = 60.0
POLL_INTERVAL_SECONDS = 0.5


def argus_socket_ready() -> str | None:
    try:
        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(str(ARGUS_SOCKET))
        sock.close()
    except FileNotFoundError:
        return f"{ARGUS_SOCKET} does not exist yet"
    except ConnectionRefusedError:
        return f"{ARGUS_SOCKET} exists but is not accepting connections (stale inode or daemon not bound)"
    return None


def main() -> int:
    deadline = monotonic() + TIMEOUT_SECONDS
    last_error: str | None = None
    while monotonic() < deadline:
        argus_error = argus_socket_ready()
        missing_nodes = [str(node) for node in VIDEO_NODES if not node.exists()]
        if argus_error is None and not missing_nodes:
            return 0
        last_error = argus_error or f"V4L2 device nodes not yet present: {', '.join(missing_nodes)}"
        sleep(POLL_INTERVAL_SECONDS)

    print(
        f"timed out after {TIMEOUT_SECONDS:.0f}s waiting for ZED camera readiness: {last_error}",
        file=stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
