#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Set

from common.run_command import run_command

PORT_MIN: int = 56000
PORT_MAX: int = 57000  # exclusive
LOCAL_PORT: int = 56000


def main():
    serial = _pick_serial()

    tcp = _adb(serial, "shell cat /proc/net/tcp")
    try:
        tcp6 = _adb(serial, "shell cat /proc/net/tcp6")
    except Exception:
        tcp6 = ""

    ports: List[int] = sorted(_parse_ports(tcp) | _parse_ports(tcp6))
    if len(ports) == 0:
        raise RuntimeError("No Android Unity debugger port found (56000–56999).")
    if len(ports) > 1:
        raise RuntimeError(f"Multiple Android Unity ports found: {ports}. Expected exactly one.")

    # Remove any prior forward on 56000 (ignore failure)
    try:
        _adb(serial, f"forward --remove tcp:{LOCAL_PORT}")
    except Exception:
        pass

    _adb(serial, f"forward tcp:{LOCAL_PORT} tcp:{ports[0]}")

    print(f"({serial}) forwarded localhost:{LOCAL_PORT} -> device:{ports[0]}")
    return 0


def _adb(serial: str, args: str) -> str:
    # Always target the chosen device (works for USB and Wi-Fi: ip:port)
    return run_command(f'adb -s "{serial}" {args}')


def _pick_serial() -> str:
    # Honor standard env if user sets it
    serial = os.environ.get("ANDROID_SERIAL") or os.environ.get("ADB_SERIAL")
    if serial:
        return serial

    out = run_command("adb devices")
    serials: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        cols = line.split()
        if len(cols) >= 2 and cols[1] == "device":
            serials.append(cols[0])

    if not serials:
        raise RuntimeError("No adb devices. Use `adb connect <ip:port>` or plug in USB.")

    if len(serials) == 1:
        return serials[0]

    # Prefer a Wi-Fi device if exactly one is present
    wifi = [s for s in serials if ":" in s]
    if len(wifi) == 1:
        return wifi[0]

    raise RuntimeError(f"Multiple adb devices: {serials}. Set ANDROID_SERIAL or unplug extras.")


def _parse_ports(command_output: str) -> Set[int]:
    out: Set[int] = set()
    for line in command_output.splitlines():
        line = line.strip()
        if not line or "local_address" in line:
            continue

        parts: List[str] = line.split()
        if len(parts) < 4:
            continue

        # In /proc/net/tcp{,6}: fields are local_address, rem_address, st...
        # Listening sockets have rem_address ...:0000 or state 0A (LISTEN).
        rem = parts[2]
        state = parts[3]
        if not (rem.endswith(":0000") or state == "0A"):
            continue

        port = int(parts[1].split(":")[1], 16)
        if PORT_MIN <= port < PORT_MAX:
            out.add(port)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
