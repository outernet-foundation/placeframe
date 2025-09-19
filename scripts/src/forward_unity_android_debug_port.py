#!/usr/bin/env python3
from __future__ import annotations

from typing import List, Set

from common.run_command import run_command

PORT_MIN: int = 56000
PORT_MAX: int = 57000  # exclusive
LOCAL_PORT: int = 56000


def main():
    tcp = run_command("adb -d shell cat /proc/net/tcp")
    try:
        tcp6 = run_command("adb -d shell cat /proc/net/tcp6")
    except Exception:
        tcp6 = ""

    ports: List[int] = sorted(_parse_ports(tcp) | _parse_ports(tcp6))
    if len(ports) == 0:
        raise RuntimeError("No Android Unity debugger port found (56000–56999).")
    if len(ports) > 1:
        raise RuntimeError(f"Multiple Android Unity ports found: {ports}. Expected exactly one.")

    # Remove any prior forward on 56000 (ignore failure)
    try:
        run_command(f"adb -d forward --remove tcp:{LOCAL_PORT}")
    except Exception:
        pass

    run_command(f"adb -d forward tcp:{LOCAL_PORT} tcp:{ports[0]}")

    print(f"forwarded localhost:{LOCAL_PORT} -> device:{ports[0]}")

    return 0


def _parse_ports(command_output: str):
    out: Set[int] = set()

    for line in command_output.splitlines():
        line = line.strip()

        if not line or "local_address" in line:
            continue

        parts: List[str] = line.split()

        if len(parts) < 3 or not parts[2].endswith(":0000"):
            continue

        port = int(parts[1].split(":")[1], 16)

        if PORT_MIN <= port < PORT_MAX:
            out.add(port)

    return out


if __name__ == "__main__":
    raise SystemExit(main())
