from __future__ import annotations

import json
import shlex
import urllib.parse
from datetime import datetime, timezone
from typing import Annotated, cast

import typer
from placeframe_bash import bash_output

LOKI_CONTAINER = "placeframe-loki-1"

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(
    query: Annotated[
        str,
        typer.Argument(
            help='LogQL query. Single-quote it. Example: \'{app="capture-tool"} | json | logGroup="Android"\''
        ),
    ],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max entries to return")] = 50,
    direction: Annotated[
        str, typer.Option("--direction", "-d", help="forward (oldest first) or backward (newest first)")
    ] = "backward",
    since: Annotated[str, typer.Option("--since", "-s", help="Time range, e.g. 5m, 30m, 1h, 24h")] = "30m",
    raw: Annotated[
        bool, typer.Option("--raw", help="Print the raw Loki JSON response instead of formatted summaries")
    ] = False,
) -> None:
    parameters = urllib.parse.urlencode({"query": query, "limit": str(limit), "direction": direction, "since": since})
    url = f"http://localhost:3100/loki/api/v1/query_range?{parameters}"
    response = bash_output(f"docker exec {LOKI_CONTAINER} wget -qO- {shlex.quote(url)}")

    if raw:
        print(response)
        return

    data = json.loads(response)
    if data.get("status") != "success":
        print(f"loki error: {data.get('error', response[:500])}")
        raise typer.Exit(1)

    streams = data.get("data", {}).get("result", [])
    total = sum(len(stream["values"]) for stream in streams)
    if total == 0:
        print(f"0 entries in last {since}. LokiSink batches every ~2s; if you just emitted, wait a moment and retry.")
        return

    entries: list[tuple[int, str]] = []
    for stream in streams:
        for timestamp_ns, line in stream["values"]:
            entries.append((int(timestamp_ns), str(line)))
    entries.sort(reverse=(direction == "backward"))

    print(f"{total} entries from {len(streams)} stream(s) over {since}")
    for timestamp_ns, line in entries:
        timestamp = datetime.fromtimestamp(timestamp_ns / 1e9, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        try:
            event: dict[str, object] = json.loads(line)
            level = str(event.get("level") or "?")[:5]
            group = str(event.get("logGroup") or "?")
            message = str(event.get("message") or "")
            raw_exception = event.get("exception")
            print(f"{timestamp} {level:5s} [{group}] {message}")
            if isinstance(raw_exception, dict):
                exception = cast(dict[str, object], raw_exception)
                print(f"            exception: {exception.get('type')}: {exception.get('message')}")
        except json.JSONDecodeError:
            print(f"{timestamp} {line}")
