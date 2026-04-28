from datetime import datetime, timezone
from json import JSONDecodeError, loads
from logging import getLogger
from re import compile as re_compile
from typing import TypedDict

from httpx import AsyncClient, HTTPError, HTTPStatusError, Response
from litestar import Router, post
from litestar.exceptions import InternalServerException
from pydantic import BaseModel, Field

from ..settings import get_settings

LOKI_PUSH_PATH = "/loki/api/v1/push"
LOKI_PUSH_TIMEOUT_S = 10.0
UNKNOWN_BOX_ID = "unknown"

logger = getLogger(__name__)

# Loki returns 400 with a body like
#   "user 'fake', total ignored: 362 out of 453 for stream: {...}"
# when some entries in a batch fail validation. The other entries in the same
# batch are still durably persisted; the response just surfaces the rejections.
# We treat partial success as success so the drainer's cursor can advance —
# otherwise we re-push the same accepted-and-rejected mix forever.
_PARTIAL_SUCCESS_PATTERN = re_compile(r"total ignored:\s*(\d+)\s*out of\s*(\d+)")


class LogRelayBatch(BaseModel):
    # Raw NDJSON lines as read from the ZED box's /logs endpoint. We parse each
    # to extract a timestamp for Loki; the line itself is pushed verbatim.
    entries: list[str] = Field(min_length=1)


class LokiStream(TypedDict):
    stream: dict[str, str]
    values: list[list[str]]


class LokiPayload(TypedDict):
    streams: list[LokiStream]


def datetime_to_ns(dt: datetime) -> int:
    # Avoid float arithmetic; `int(dt.timestamp() * 1e9)` loses precision at microsecond scale.
    return int(dt.timestamp()) * 1_000_000_000 + dt.microsecond * 1000


def extract_timestamp_ns(entry: str, default_ns: int) -> int:
    try:
        record = loads(entry)
        ts = record.get("timestamp")
        if not isinstance(ts, str):
            return default_ns
        return datetime_to_ns(datetime.fromisoformat(ts))
    except (JSONDecodeError, ValueError, TypeError):
        return default_ns


def extract_box_id(entry: str) -> str | None:
    try:
        record = loads(entry)
    except JSONDecodeError:
        return None
    box_id = record.get("box_id")
    return box_id if isinstance(box_id, str) and box_id else None


def build_loki_payload(entries: list[str]) -> LokiPayload:
    # The box stamps every record with its own box_id (see zed-capture's
    # logging_config.py). We extract it here to drive the per-stream label,
    # rather than trusting the relayer's URL — the box owns its identity, the
    # phone is just a pipe. Entries that fail to parse or lack a box_id get
    # routed to a sentinel stream so they aren't silently dropped.
    now_ns = datetime_to_ns(datetime.now(tz=timezone.utc))
    groups: dict[str, list[list[str]]] = {}
    for entry in entries:
        box_id = extract_box_id(entry) or UNKNOWN_BOX_ID
        if box_id == UNKNOWN_BOX_ID:
            logger.warning("entry missing box_id, routing to '%s' stream", UNKNOWN_BOX_ID)
        groups.setdefault(box_id, []).append([str(extract_timestamp_ns(entry, now_ns)), entry])

    return {
        "streams": [
            {
                "stream": {
                    "service": "zed-capture",
                    "box_id": box_id,
                    "source": "phone-relay",
                },
                "values": values,
            }
            for box_id, values in groups.items()
        ]
    }


def is_loki_partial_success(response: Response) -> bool:
    if response.status_code != 400:
        return False
    match = _PARTIAL_SUCCESS_PATTERN.search(response.text)
    if not match:
        return False
    ignored, total = int(match.group(1)), int(match.group(2))
    return 0 < ignored < total


@post("/zed-boxes/logs")
async def push_zed_box_logs(data: LogRelayBatch) -> None:
    settings = get_settings()
    payload = build_loki_payload(data.entries)
    url = str(settings.loki_url).rstrip("/") + LOKI_PUSH_PATH
    try:
        async with AsyncClient(timeout=LOKI_PUSH_TIMEOUT_S) as client:
            response = await client.post(url, json=payload)
            try:
                response.raise_for_status()
            except HTTPStatusError:
                if is_loki_partial_success(response):
                    logger.warning("Loki partial success: %s", response.text)
                    return
                raise
    except HTTPError as exception:
        raise InternalServerException(f"Loki push failed: {exception}")


router = Router(path="/", tags=["zed-box-logs"], route_handlers=[push_zed_box_logs])
