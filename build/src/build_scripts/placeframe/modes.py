from os import environ
from pathlib import Path
from urllib.parse import urlparse

VALID_AUTH_MODES = ("keycloak", "disabled")
DEFAULT_AUTH_MODE = "keycloak"


def parse_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip("'\"")
    return result


def resolve_auth_mode(env_file: Path) -> str:
    file_values = parse_env_file(env_file)
    public_url = environ.get("PUBLIC_URL") or file_values.get("PUBLIC_URL")
    auth_mode = environ.get("AUTH_MODE") or file_values.get("AUTH_MODE", DEFAULT_AUTH_MODE)

    if not public_url:
        raise RuntimeError("PUBLIC_URL is required; set it in .env")
    if auth_mode not in VALID_AUTH_MODES:
        raise RuntimeError(f"AUTH_MODE={auth_mode!r} is invalid; expected one of {list(VALID_AUTH_MODES)}")

    scheme = urlparse(public_url).scheme
    if scheme not in ("http", "https"):
        raise RuntimeError(f"PUBLIC_URL={public_url!r} must use http:// or https://")
    if scheme == "http" and auth_mode == "keycloak":
        raise RuntimeError(
            f"AUTH_MODE=keycloak with PUBLIC_URL={public_url!r} is rejected: OAuth credentials must "
            f"not flow in cleartext. Use https:// (e.g. via ngrok), or set AUTH_MODE=disabled."
        )

    return auth_mode
