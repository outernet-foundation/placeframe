import re
from http.client import HTTPConnection

from common.run_command import run_command
from docker.models.containers import Container

from docker import from_env

_CONTAINER_ID_RE = re.compile(r"\b[0-9a-f]{12,64}\b")


def create_service(service_name: str, container_name: str, environment: dict[str, str]):
    environment_string = " ".join(f"-e {key}='{value}'" for key, value in environment.items())

    stdout = run_command(
        f"docker compose -f /compose.yml run -d --no-deps --name {container_name} {environment_string} {service_name}",
        log=True,
    )

    return _parse_container_id(stdout)


def destroy_service(container_id: str):
    container: Container | None = None
    try:
        container = from_env().containers.get(container_id)
    except Exception:
        # Already removed
        return

    container.stop(timeout=10)

    # Don't remove the container, we want to keep logs around for debugging
    # container.remove(force=True)


def get_service_status(container_id: str, session_port: int) -> str:
    container = from_env().containers.get(container_id)
    container.reload()
    assert container.name is not None

    status: str | None = container.attrs.get("State", {}).get("Status")

    if status is None:
        return "unknown"
    if status != "running":
        return status

    try:
        conn = HTTPConnection(container.name, session_port, timeout=2.0)
        conn.request("GET", "/health")
        health_status = conn.getresponse().status
        conn.close()
        if health_status < 500:
            return "ready"
    except Exception:
        pass

    return "running"


def _parse_container_id(stdout: str):
    # docker compose run -d prints the container id (often the only line)
    m = _CONTAINER_ID_RE.search(stdout.strip().splitlines()[-1] if stdout.strip() else "")
    if not m:
        # fall back to searching all output
        m = _CONTAINER_ID_RE.search(stdout)
    if not m:
        raise RuntimeError(f"Failed to parse container id from output:\n{stdout}")
    return m.group(0)
