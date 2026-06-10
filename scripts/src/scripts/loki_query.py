from __future__ import annotations

import json
import shlex
import urllib.parse
from datetime import datetime, timezone
from typing import Annotated

import typer
from placeframe_bash import bash_output

LOKI_CONTAINER = "placeframe-loki-1"

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(
    query: Annotated[
        str,
        typer.Argument(
            help='LogQL query. Single-quote it. Example: \'{service_name="capture-tool"} | logGroup="Android"\''
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

    # Native OTLP ingestion: the line is the OTel body (the human message); level,
    # log group, and exception fields ride as structured metadata, which Loki merges
    # into each stream's label set in the query response. So they are read per-stream,
    # not parsed out of the line.
    entries: list[tuple[int, str, dict[str, str]]] = []
    for stream in streams:
        metadata = stream.get("stream", {})
        for timestamp_ns, line in stream["values"]:
            entries.append((int(timestamp_ns), str(line), metadata))
    entries.sort(key=lambda entry: entry[0], reverse=(direction == "backward"))

    print(f"{total} entries from {len(streams)} stream(s) over {since}")
    for timestamp_ns, line, metadata in entries:
        timestamp = datetime.fromtimestamp(timestamp_ns / 1e9, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        level = str(metadata.get("detected_level") or metadata.get("severity_text") or "?")[:5]
        group = str(metadata.get("logGroup") or "?")
        print(f"{timestamp} {level:5s} [{group}] {line}")
        exception_type = metadata.get("exception_type")
        if exception_type:
            print(f"            exception: {exception_type}: {metadata.get('exception_message') or ''}")
