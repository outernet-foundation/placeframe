#!/usr/bin/env python3
import json
import subprocess
import sys
from typing import Dict, List, Optional

def run(*args: str) -> str:
    return subprocess.check_output(args, text=True)

def all_container_ids() -> List[str]:
    out = run("bash", "-lc", "docker ps --format '{{json .ID}}'")
    return [json.loads(line) for line in out.splitlines() if line.strip()]

def inspect_one(container_id: str) -> Dict:
    return json.loads(run("docker", "inspect", container_id))[0]

def host_port_5678(info: Dict) -> Optional[str]:
    ports = (info.get("NetworkSettings", {}).get("Ports") or {}).get("5678/tcp") or []
    if not ports:
        return None
    return ports[0].get("HostPort") or None

def main() -> None:
    found = 0
    for container_id in all_container_ids():
        info = inspect_one(container_id)

        labels = (info.get("Config", {}) or {}).get("Labels", {}) or {}
        service = labels.get("service") or ""
        if not service:
            continue

        port = host_port_5678(info)
        if not port:
            continue

        name = (info.get("Name") or "").lstrip("/")
        job = labels.get("job", "-")
        task = labels.get("task", "-")
        # value|label -> the picker returns the first field (port)
        print(f"{port}|{service} | {name} j{job} t{task} → {port}")
        found += 1

    if found == 0:
        print(
            "[list_debug_targets] No attachable worker containers found. "
            "Ensure containers have a 'service' label and publish 5678/tcp.",
            file=sys.stderr,
        )

if __name__ == "__main__":
    main()
