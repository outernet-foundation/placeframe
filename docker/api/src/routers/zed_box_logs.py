from datetime import datetime, timezone
from json import JSONDecodeError, loads
from logging import getLogger
from re import compile as re_compile
from typing import cast

from httpx import AsyncClient, HTTPError, HTTPStatusError
from litestar import Router, post
from litestar.exceptions import InternalServerException
from pydantic import BaseModel, Field

from ..settings import get_settings

LOKI_PUSH_PATH = "/loki/api/v1/push"
LOKI_PUSH_TIMEOUT_S = 10.0
UNKNOWN_BOX_ID = "unknown"

# Loki returns 400 with a body like
#   "user 'fake', total ignored: 362 out of 453 for stream: {...}"
# when some entries in a batch fail validation. The other entries in the same
# batch are still durably persisted; the response just surfaces the rejections.
# We treat partial success as success so the drainer's cursor can advance —
# otherwise we re-push the same accepted-and-rejected mix forever.
_PARTIAL_SUCCESS_PATTERN = re_compile(r"total ignored:\s*(\d+)\s*out of\s*(\d+)")

logger = getLogger(__name__)


class LogRelayBatch(BaseModel):
    # Raw NDJSON lines as read from the ZED box's /logs endpoint. We parse each
    # to extract a timestamp for Loki; the line itself is pushed verbatim.
    entries: list[str] = Field(min_length=1)


def datetime_to_ns(dt: datetime) -> int:
    # Avoid float arithmetic; `int(dt.timestamp() * 1e9)` loses precision at microsecond scale.
    return int(dt.timestamp()) * 1_000_000_000 + dt.microsecond * 1000


@post("/zed-boxes/logs")
async def push_zed_box_logs(data: LogRelayBatch) -> None:
    # The box stamps every record with its own box_id (see zed-capture's
    # logging_config.py). We use that to drive the per-stream label, rather
    # than trusting the relayer's URL — the box owns its identity, the phone
    # is just a pipe. Entries that fail to parse or lack a box_id get routed
    # to a sentinel stream so they aren't silently dropped.
    now_ns = datetime_to_ns(datetime.now(tz=timezone.utc))
    groups: dict[str, list[list[str]]] = {}
    for entry in data.entries:
        try:
            parsed: object = loads(entry)
        except JSONDecodeError:
            parsed = None
        record = cast("dict[str, object]", parsed) if isinstance(parsed, dict) else None

        box_id_value = record.get("box_id") if record is not None else None
        box_id = box_id_value if isinstance(box_id_value, str) and box_id_value else UNKNOWN_BOX_ID
        if box_id == UNKNOWN_BOX_ID:
            logger.warning("entry missing box_id, routing to '%s' stream", UNKNOWN_BOX_ID)

        ts_ns = now_ns
        ts_value = record.get("timestamp") if record is not None else None
        if isinstance(ts_value, str):
            try:
                ts_ns = datetime_to_ns(datetime.fromisoformat(ts_value))
            except ValueError:
                pass

        groups.setdefault(box_id, []).append([str(ts_ns), entry])

    try:
        async with AsyncClient(timeout=LOKI_PUSH_TIMEOUT_S) as client:
            response = await client.post(
                str(get_settings().loki_url).rstrip("/") + LOKI_PUSH_PATH,
                json={
                    "streams": [
                        {
                            "stream": {"service": "zed-capture", "box_id": box_id, "source": "phone-relay"},
                            "values": values,
                        }
                        for box_id, values in groups.items()
                    ]
                },
            )
            response.raise_for_status()
    except HTTPStatusError as exception:
        match = _PARTIAL_SUCCESS_PATTERN.search(exception.response.text)
        if exception.response.status_code == 400 and match and 0 < int(match.group(1)) < int(match.group(2)):
            logger.warning("Loki partial success: %s", exception.response.text)
            return
        raise InternalServerException(f"Loki push failed: {exception}")
    except HTTPError as exception:
        raise InternalServerException(f"Loki push failed: {exception}")


router = Router(path="/", tags=["zed-box-logs"], route_handlers=[push_zed_box_logs])
