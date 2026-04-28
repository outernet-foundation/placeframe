import json

from httpx import Response
from src.routers.zed_box_logs import (
    UNKNOWN_BOX_ID,
    build_loki_payload,
    extract_box_id,
    extract_timestamp_ns,
    is_loki_partial_success,
)


def test_extracts_iso_timestamp_as_nanoseconds():
    entry = '{"timestamp":"2026-04-22T14:33:04.412803+00:00","level":"INFO","message":"hi"}'
    ns = extract_timestamp_ns(entry, default_ns=0)
    # 2026-04-22T14:33:04.412803 UTC
    assert ns == 1776868384412803000


def test_falls_back_when_timestamp_missing():
    entry = '{"level":"INFO","message":"hi"}'
    assert extract_timestamp_ns(entry, default_ns=42) == 42


def test_falls_back_on_invalid_json():
    assert extract_timestamp_ns("not json at all", default_ns=42) == 42


def test_falls_back_on_non_string_timestamp():
    entry = '{"timestamp":12345,"level":"INFO"}'
    assert extract_timestamp_ns(entry, default_ns=42) == 42


def test_falls_back_on_unparseable_timestamp():
    entry = '{"timestamp":"yesterday","level":"INFO"}'
    assert extract_timestamp_ns(entry, default_ns=42) == 42


def test_extract_box_id_present():
    entry = '{"box_id":"box-42","level":"INFO"}'
    assert extract_box_id(entry) == "box-42"


def test_extract_box_id_missing():
    assert extract_box_id('{"level":"INFO"}') is None


def test_extract_box_id_non_string():
    assert extract_box_id('{"box_id":42}') is None


def test_extract_box_id_invalid_json():
    assert extract_box_id("not json at all") is None


def test_loki_payload_labels_and_values():
    entry1 = '{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00","message":"a"}'
    entry2 = '{"box_id":"box-42","timestamp":"2026-04-22T14:33:05.000000+00:00","message":"b"}'

    payload = build_loki_payload([entry1, entry2])

    assert payload == {
        "streams": [
            {
                "stream": {
                    "service": "zed-capture",
                    "box_id": "box-42",
                    "source": "phone-relay",
                },
                "values": [
                    ["1776868384412803000", entry1],
                    ["1776868385000000000", entry2],
                ],
            }
        ]
    }


def test_loki_payload_groups_by_box_id():
    entry_a = '{"box_id":"box-a","timestamp":"2026-04-22T14:33:04.412803+00:00","message":"a"}'
    entry_b = '{"box_id":"box-b","timestamp":"2026-04-22T14:33:05.000000+00:00","message":"b"}'

    payload = build_loki_payload([entry_a, entry_b])
    streams = {s["stream"]["box_id"]: s for s in payload["streams"]}

    assert streams["box-a"]["values"] == [["1776868384412803000", entry_a]]
    assert streams["box-b"]["values"] == [["1776868385000000000", entry_b]]


def test_loki_payload_routes_missing_box_id_to_sentinel():
    entry = '{"timestamp":"2026-04-22T14:33:04.412803+00:00","message":"a"}'
    payload = build_loki_payload([entry])
    assert payload["streams"][0]["stream"]["box_id"] == UNKNOWN_BOX_ID


def test_partial_success_recognised_when_some_entries_ignored():
    body = (
        "entry with timestamp 2026-04-25 ignored, reason: 'entry too far behind', "
        "user 'fake', total ignored: 362 out of 453 for stream: {service=\"zed-capture\"}"
    )
    assert is_loki_partial_success(Response(status_code=400, text=body)) is True


def test_full_rejection_is_not_partial_success():
    body = "user 'fake', total ignored: 5 out of 5 for stream: {...}"
    assert is_loki_partial_success(Response(status_code=400, text=body)) is False


def test_no_count_in_body_is_not_partial_success():
    assert is_loki_partial_success(Response(status_code=400, text="some other 400")) is False


def test_non_400_is_not_partial_success():
    body = "user 'fake', total ignored: 1 out of 2"
    assert is_loki_partial_success(Response(status_code=500, text=body)) is False


def test_loki_payload_preserves_opaque_entry_strings():
    # Entries must go through unchanged — Grafana needs the original JSON.
    entry = '{"box_id":"box-42","timestamp":"2026-04-22T14:33:04.412803+00:00","extra":{"nested":[1,2,3]}}'
    payload = build_loki_payload([entry])

    stream = payload["streams"][0]
    assert stream["values"][0][1] == entry
    # And the entry is still valid JSON the server never tampered with.
    assert json.loads(stream["values"][0][1])["extra"]["nested"] == [1, 2, 3]
