import json
from typing import Any, cast
from unittest.mock import patch

import httpx
import pytest
from httpx import MockTransport, Request, Response
from litestar.exceptions import InternalServerException
from src.routers.zed_box_logs import (
    UNKNOWN_BOX_ID,
    LogRelayBatch,
    push_zed_box_logs,
)


class _Settings:
    def __init__(self, loki_url: str):
        self.loki_url = loki_url


async def _push(entries: list[str], response: Response) -> dict[str, Any]:
    # Intercept the handler's AsyncClient with a MockTransport that captures
    # the request and returns the stubbed response.
    captured: dict[str, Request] = {}

    def _transport_handler(request: Request) -> Response:
        captured["request"] = request
        return response

    def _factory(**kwargs: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=MockTransport(_transport_handler), **kwargs)

    with (
        patch("src.routers.zed_box_logs.AsyncClient", _factory),
        patch("src.routers.zed_box_logs.get_settings", lambda: _Settings("http://loki.test")),
    ):
        await push_zed_box_logs.fn(LogRelayBatch(entries=entries))

    return cast(dict[str, Any], json.loads(captured["request"].content))


@pytest.mark.asyncio
async def test_extracts_iso_timestamp_as_nanoseconds():
    payload = await _push(
        ['{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00","message":"hi"}'],
        Response(204),
    )
    # 2026-04-22T14:33:04.412803 UTC
    assert payload["streams"][0]["values"][0][0] == "1776868384412803000"


@pytest.mark.asyncio
async def test_falls_back_to_now_when_timestamp_missing():
    payload = await _push(['{"box_id":"box-42","message":"hi"}'], Response(204))
    ts = int(payload["streams"][0]["values"][0][0])
    # Falls back to "now" — should be a recent epoch-ns value, not 0.
    assert ts > 1_700_000_000_000_000_000


@pytest.mark.asyncio
async def test_falls_back_on_invalid_json():
    payload = await _push(["not json at all"], Response(204))
    assert payload["streams"][0]["stream"]["box_id"] == UNKNOWN_BOX_ID
    assert int(payload["streams"][0]["values"][0][0]) > 1_700_000_000_000_000_000


@pytest.mark.asyncio
async def test_falls_back_on_non_string_timestamp():
    payload = await _push(['{"box_id":"box-42","timestamp":12345,"level":"INFO"}'], Response(204))
    assert int(payload["streams"][0]["values"][0][0]) > 1_700_000_000_000_000_000


@pytest.mark.asyncio
async def test_falls_back_on_unparseable_timestamp():
    payload = await _push(['{"box_id":"box-42","timestamp":"yesterday","level":"INFO"}'], Response(204))
    assert int(payload["streams"][0]["values"][0][0]) > 1_700_000_000_000_000_000


@pytest.mark.asyncio
async def test_routes_missing_box_id_to_sentinel():
    payload = await _push(
        ['{"timestamp":"2026-04-22T14:33:04.412803+00:00","message":"a"}'],
        Response(204),
    )
    assert payload["streams"][0]["stream"]["box_id"] == UNKNOWN_BOX_ID


@pytest.mark.asyncio
async def test_non_string_box_id_routes_to_sentinel():
    payload = await _push(
        ['{"box_id":42,"timestamp":"2026-04-22T14:33:04.412803+00:00"}'],
        Response(204),
    )
    assert payload["streams"][0]["stream"]["box_id"] == UNKNOWN_BOX_ID


@pytest.mark.asyncio
async def test_loki_payload_labels_and_values():
    entry1 = '{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00","message":"a"}'
    entry2 = '{"box_id":"box-42","timestamp":"2026-04-22T14:33:05.000000+00:00","message":"b"}'
    payload = await _push([entry1, entry2], Response(204))

    assert payload == {
        "streams": [
            {
                "stream": {"service": "zed-capture", "box_id": "box-42", "source": "phone-relay"},
                "values": [
                    ["1776868384412803000", entry1],
                    ["1776868385000000000", entry2],
                ],
            }
        ]
    }


@pytest.mark.asyncio
async def test_loki_payload_groups_by_box_id():
    entry_a = '{"box_id":"box-a","timestamp":"2026-04-22T14:33:04.412803+00:00","message":"a"}'
    entry_b = '{"box_id":"box-b","timestamp":"2026-04-22T14:33:05.000000+00:00","message":"b"}'
    payload = await _push([entry_a, entry_b], Response(204))
    streams = {s["stream"]["box_id"]: s for s in payload["streams"]}

    assert streams["box-a"]["values"] == [["1776868384412803000", entry_a]]
    assert streams["box-b"]["values"] == [["1776868385000000000", entry_b]]


@pytest.mark.asyncio
async def test_loki_payload_preserves_opaque_entry_strings():
    # Entries must go through unchanged — Grafana needs the original JSON.
    entry = '{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00","extra":{"nested":[1,2,3]}}'
    payload = await _push([entry], Response(204))

    stream = payload["streams"][0]
    assert stream["values"][0][1] == entry
    assert json.loads(stream["values"][0][1])["extra"]["nested"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_partial_success_swallowed():
    body = (
        "entry with timestamp 2026-04-25 ignored, reason: 'entry too far behind', "
        "user 'fake', total ignored: 362 out of 453 for stream: {service=\"zed-capture\"}"
    )
    # No exception raised → partial success treated as success.
    await _push(
        ['{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00"}'],
        Response(400, text=body),
    )


@pytest.mark.asyncio
async def test_full_rejection_raises():
    body = "user 'fake', total ignored: 5 out of 5 for stream: {...}"
    with pytest.raises(InternalServerException):
        await _push(
            ['{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00"}'],
            Response(400, text=body),
        )


@pytest.mark.asyncio
async def test_400_without_count_raises():
    with pytest.raises(InternalServerException):
        await _push(
            ['{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00"}'],
            Response(400, text="some other 400"),
        )


@pytest.mark.asyncio
async def test_500_raises_even_with_partial_count_body():
    body = "user 'fake', total ignored: 1 out of 2"
    with pytest.raises(InternalServerException):
        await _push(
            ['{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00"}'],
            Response(500, text=body),
        )
