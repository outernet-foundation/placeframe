import fcntl
import logging
import os
import socket
import struct
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("rathole-client")

RATHOLE_BINARY = "/usr/local/bin/rathole"
CONFIG_PATH = Path("/tmp/rathole-client.toml")
TEMPLATES_DIRECTORY = Path(__file__).resolve().parent / "templates"

# Forward relayed traffic to the host's docker0 bridge gateway rather than
# 127.0.0.1. LiveKit (Pion) enumerates non-loopback interfaces and binds the
# RTC UDP socket per-interface, skipping `lo` — so datagrams arriving at
# 127.0.0.1:<rtc_port> get dropped. docker0's gateway IP is one of the
# interfaces LiveKit does bind. Requires network_mode: host on this container
# so the host's docker0 is visible.
FORWARD_INTERFACE = "docker0"
SIOCGIFADDR = 0x8915


@dataclass(frozen=True)
class Service:
    name: str
    protocol: str
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
        if len(parts) != 3:
            raise ValueError(
                f"Invalid RATHOLE_SERVICES entry {entry!r}: expected 'name:protocol:port', got {len(parts)} parts."
            )
        name, protocol, port = parts
        if protocol not in ("tcp", "udp"):
            raise ValueError(f"Invalid protocol {protocol!r} in RATHOLE_SERVICES entry {entry!r}: must be tcp or udp.")
        services.append(Service(name=name, protocol=protocol, port=int(port)))
    if not services:
        raise ValueError("RATHOLE_SERVICES must list at least one service.")

    forward_address = resolve_interface_ipv4(FORWARD_INTERFACE)

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
        forward_address=forward_address,
        services=services,
    )
    CONFIG_PATH.write_text(config)
    CONFIG_PATH.chmod(0o600)

    logger.info(
        "Registering %d services on relay %s as engineer %s, forwarding to %s (%s): %s",
        len(services),
        control_endpoint,
        engineer_name,
        forward_address,
        FORWARD_INTERFACE,
        ", ".join(f"{engineer_name}-{service.name}->{service.port}/{service.protocol}" for service in services),
    )
    os.execv(RATHOLE_BINARY, [RATHOLE_BINARY, "--client", str(CONFIG_PATH)])


def resolve_interface_ipv4(interface_name: str) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        request = struct.pack("256s", interface_name.encode("utf-8")[:15])
        try:
            response = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, request)
        except OSError as exception:
            raise RuntimeError(
                f"Could not resolve IPv4 for interface {interface_name!r}. "
                f"This container must run with network_mode: host and the host "
                f"must have a {interface_name} interface (default Docker daemon)."
            ) from exception
    return socket.inet_ntoa(response[20:24])


if __name__ == "__main__":
    main()
