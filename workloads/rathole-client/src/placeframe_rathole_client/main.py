import logging
import os
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("rathole-client")

RATHOLE_BINARY = "/usr/local/bin/rathole"
CONFIG_PATH = Path("/tmp/rathole-client.toml")
TEMPLATES_DIRECTORY = Path(__file__).resolve().parent / "templates"


# Each relayed service forwards to a sibling container by its Docker DNS name on
# the shared compose network. LiveKit advertises a single ICE candidate
# (node_ip) and pion registers each session on the one socket behind it, so the
# container forwards to LiveKit's single bridge interface — no host networking
# or docker0 rendezvous, which makes the stack portable to Docker Desktop where
# host networking cannot listen.
@dataclass(frozen=True)
class Service:
    name: str
    protocol: str
    host: str
    port: int


def main() -> None:
    engineer_name = os.environ["ENGINEER_NAME"]
    control_endpoint = os.environ["TUNNEL_CONTROL_ENDPOINT"]
    token = os.environ["TUNNEL_TOKEN"]
    missing = [name for name in ("ENGINEER_NAME", "TUNNEL_CONTROL_ENDPOINT", "TUNNEL_TOKEN") if not os.environ[name]]
    if missing:
        raise RuntimeError(f"Required env vars are unset or empty: {', '.join(missing)}")

    services: list[Service] = []
    for raw_entry in os.environ["RATHOLE_SERVICES"].split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid RATHOLE_SERVICES entry {entry!r}: expected 'name:protocol:host:port', got {len(parts)} parts."
            )
        name, protocol, host, port = parts
        if protocol not in ("tcp", "udp"):
            raise ValueError(f"Invalid protocol {protocol!r} in RATHOLE_SERVICES entry {entry!r}: must be tcp or udp.")
        services.append(Service(name=name, protocol=protocol, host=host, port=int(port)))
    if not services:
        raise ValueError("RATHOLE_SERVICES must list at least one service.")

    template_environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIRECTORY),
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    config = template_environment.get_template("client.toml.j2").render(
        engineer_name=engineer_name,
        control_endpoint=control_endpoint,
        token=token,
        services=services,
    )
    CONFIG_PATH.write_text(config)
    CONFIG_PATH.chmod(0o600)

    logger.info(
        "Registering %d services on relay %s as engineer %s: %s",
        len(services),
        control_endpoint,
        engineer_name,
        ", ".join(
            f"{engineer_name}-{service.name}->{service.host}:{service.port}/{service.protocol}" for service in services
        ),
    )
    os.execv(RATHOLE_BINARY, [RATHOLE_BINARY, "--client", str(CONFIG_PATH)])


if __name__ == "__main__":
    main()
