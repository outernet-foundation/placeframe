#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from typing import Dict, List, Mapping, Optional, TypedDict, cast


def run(*args: str):
    return subprocess.check_output(args, text=True)


def all_container_ids():
    out = run("docker", "ps", "--format", "{{json .ID}}")
    return [cast(str, json.loads(line)) for line in out.splitlines() if line.strip()]


class PortBinding(TypedDict, total=False):
    HostIp: str
    HostPort: str


PortsMapping = Mapping[str, Optional[List[PortBinding]]]


class NetworkSettingsTD(TypedDict, total=False):
    Ports: Optional[PortsMapping]


class ConfigTD(TypedDict, total=False):
    Labels: Optional[Dict[str, str]]


class ContainerInfo(TypedDict, total=False):
    NetworkSettings: Optional[NetworkSettingsTD]
    Config: Optional[ConfigTD]
    Name: Optional[str]


def inspect_one(container_id: str):
    raw = json.loads(run("docker", "inspect", container_id))
    if not isinstance(raw, list) or not raw or not isinstance(raw[0], dict):
        raise RuntimeError(f"Unexpected docker inspect payload for {container_id!r}")
    return cast(ContainerInfo, raw[0])


def host_port_5678(info: ContainerInfo):
    net = info.get("NetworkSettings")
    if not net:
        return None
    ports = net.get("Ports")
    if not ports:
        return None
    candidates = ports.get("5678/tcp")
    if not candidates:
        return None
    first = candidates[0]
    host_port = first.get("HostPort")
    return host_port if host_port else None


if __name__ == "__main__":
    found = 0
    for container_id in all_container_ids():
        info = inspect_one(container_id)

        cfg = info.get("Config")
        labels: Dict[str, str] = dict((cfg.get("Labels") if cfg else None) or {})

        service: str = labels.get("service", "")
        if not service:
            continue

        port = host_port_5678(info)
        if not port:
            continue

        name: str = str(info.get("Name") or "").lstrip("/")
        job: str = labels.get("job", "-")
        task: str = labels.get("task", "-")

        # value|label (VS Code picker expects the first field to be the value)
        print(f"{port}|{service} | {name} {job} {task}")
        found += 1

    if found == 0:
        print(
            "[list_debug_targets] No attachable task containers found. "
            "Ensure containers have a 'service' label and publish 5678/tcp.",
            file=sys.stderr,
        )
