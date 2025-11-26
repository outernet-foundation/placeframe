#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Mapping, Sequence

from .auth import get_or_refresh_token  # used only for the token endpoint

# ...imports stay the same...


def curl(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json_data: Mapping[str, Any] | Sequence[Any] | None = None,
    form_data: dict[str, str] | None = None,
    connect_timeout_s: float | None = None,
    print_command: bool = False,
) -> Any:
    cmd = [
        "curl",
        "-s",
        "-S",
        "-w",
        "\n%{http_code}",
        "-X",
        method,
        "-H",
        f"Authorization: Bearer {get_or_refresh_token()}",
    ]

    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

    # Send JSON if provided ({} or [] should be sent too)
    if json_data is not None:
        cmd.extend(["-H", "Content-Type: application/json"])
        cmd.extend(["-d", json.dumps(json_data, default=str)])  # default=str handles UUIDs

    if form_data:
        for key, value in form_data.items():
            cmd.extend(["-F", f"{key}={value}"])

    if connect_timeout_s is not None:
        cmd.extend(["--connect-timeout", str(connect_timeout_s)])

    cmd.append(url)

    if print_command:
        print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    lines = result.stdout.rsplit("\n", 1)
    if len(lines) == 2:
        body, status_text = lines
        try:
            status = int(status_text)
        except ValueError:
            body, status = result.stdout, 0
    else:
        body, status = result.stdout, 0

    if not (200 <= status < 300):
        if result.stderr:
            print(f"stderr: {result.stderr}", file=sys.stderr)
        print(f"Error: curl command failed with status {status}", file=sys.stderr)
        print(f"body: {body}", file=sys.stderr)
        sys.exit(1)

    return json.loads(body)
