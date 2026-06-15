from __future__ import annotations

import io
import tarfile
import uuid

import httpx
import pytest

from .test_capture_session_artifacts import MINIMAL_JPEG, _build_capture_tar


@pytest.fixture(scope="module")
def exported_capture(api_client: httpx.Client) -> tuple[str, str, list[int], bytes]:
    timestamps_ms = [1_700_000_100_001, 1_700_000_100_002, 1_700_000_100_003]
    tar_bytes = _build_capture_tar(timestamps_ms, MINIMAL_JPEG)
    name = f"pytest-transport-{uuid.uuid4()}"

    created = api_client.post(
        "/capture_sessions",
        data={"name": name, "device_type": "Zed"},
        files={"data": ("capture.tar", tar_bytes, "application/x-tar")},
    )
    created.raise_for_status()
    capture_id = created.json()["id"]

    export = api_client.get(f"/capture_sessions/{capture_id}/export")
    export.raise_for_status()
    return capture_id, name, timestamps_ms, export.content


def test_export_tar_contains_metadata_and_capture(exported_capture):
    capture_id, name, _, tar_bytes = exported_capture

    members: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:*") as tf:
        for member in tf:
            extracted = tf.extractfile(member)
            if extracted is not None:
                members[member.name] = extracted.read()

    assert "metadata.json" in members
    assert "capture.tar" in members

    metadata = members["metadata.json"]
    assert b'"capture_session"' in metadata
    assert str(capture_id).encode() in metadata
    assert name.encode() in metadata

    # The nested member is itself a valid capture tar carrying the manifest.
    with tarfile.open(fileobj=io.BytesIO(members["capture.tar"]), mode="r:*") as nested:
        assert "manifest.json" in nested.getnames()


def test_import_recreates_capture_with_same_id_and_images(api_client: httpx.Client, exported_capture):
    capture_id, name, timestamps_ms, tar_bytes = exported_capture

    deleted = api_client.delete(f"/capture_sessions/{capture_id}")
    deleted.raise_for_status()
    assert api_client.get(f"/capture_sessions/{capture_id}").status_code == 404

    imported = api_client.post(
        "/capture_sessions/import",
        files={"data": (f"capture-{capture_id}.tar", tar_bytes, "application/x-tar")},
    )
    imported.raise_for_status()
    body = imported.json()
    assert body["id"] == capture_id
    assert body["name"] == name

    image = api_client.get(f"/capture_sessions/{capture_id}/images/{timestamps_ms[1]}")
    assert image.status_code == 200, image.text
    assert image.content == MINIMAL_JPEG


def test_import_existing_capture_conflicts(api_client: httpx.Client, exported_capture):
    capture_id, _, _, tar_bytes = exported_capture

    # The capture was recreated by the previous test, so a second import of the same id must conflict.
    imported = api_client.post(
        "/capture_sessions/import",
        files={"data": (f"capture-{capture_id}.tar", tar_bytes, "application/x-tar")},
    )
    assert imported.status_code == 409, imported.text
