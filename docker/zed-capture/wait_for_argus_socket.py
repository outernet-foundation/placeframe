from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket
from sys import stderr
from time import monotonic, sleep

SOCKET_PATH = Path("/tmp/argus_socket")
TIMEOUT_SECONDS = 60.0
POLL_INTERVAL_SECONDS = 0.5


def main() -> int:
    deadline = monotonic() + TIMEOUT_SECONDS
    last_error: str | None = None
    while monotonic() < deadline:
        try:
            sock = socket(AF_UNIX, SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect(str(SOCKET_PATH))
            sock.close()
            return 0
        except FileNotFoundError:
            last_error = f"{SOCKET_PATH} does not exist yet"
        except ConnectionRefusedError:
            last_error = f"{SOCKET_PATH} exists but is not accepting connections (stale inode or daemon not bound)"
        sleep(POLL_INTERVAL_SECONDS)

    print(
        f"timed out after {TIMEOUT_SECONDS:.0f}s waiting for {SOCKET_PATH}: {last_error}",
        file=stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
