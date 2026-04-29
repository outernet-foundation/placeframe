import importlib
from pathlib import Path

import pytest

from src.cursor_store import CursorStore


@pytest.fixture
def fresh_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> CursorStore:
    monkeypatch.setenv("ZED_STATE_DIR", str(tmp_path))
    import src.cursor_store

    importlib.reload(src.cursor_store)
    return src.cursor_store.cursor_store


def test_initial_committed_is_empty(fresh_store: CursorStore) -> None:
    assert fresh_store.committed == ""


def test_ack_matching_pending_advances_committed(fresh_store: CursorStore) -> None:
    fresh_store.set_pending("inode:100")
    committed = fresh_store.ack_and_get_committed("inode:100")
    assert committed == "inode:100"
    assert fresh_store.committed == "inode:100"


def test_ack_not_matching_pending_is_ignored(fresh_store: CursorStore) -> None:
    fresh_store.set_pending("inode:100")
    committed = fresh_store.ack_and_get_committed("inode:50")
    assert committed == ""
    assert fresh_store.committed == ""


def test_empty_ack_does_not_advance(fresh_store: CursorStore) -> None:
    fresh_store.set_pending("inode:100")
    committed = fresh_store.ack_and_get_committed("")
    assert committed == ""
    assert fresh_store.committed == ""


def test_committed_persists_across_reload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ZED_STATE_DIR", str(tmp_path))
    import src.cursor_store

    importlib.reload(src.cursor_store)
    src.cursor_store.cursor_store.set_pending("inode:200")
    src.cursor_store.cursor_store.ack_and_get_committed("inode:200")

    importlib.reload(src.cursor_store)
    assert src.cursor_store.cursor_store.committed == "inode:200"


def test_pending_resets_to_committed_on_reload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ZED_STATE_DIR", str(tmp_path))
    import src.cursor_store

    importlib.reload(src.cursor_store)
    src.cursor_store.cursor_store.set_pending("inode:100")
    src.cursor_store.cursor_store.ack_and_get_committed("inode:100")
    src.cursor_store.cursor_store.set_pending("inode:200")  # handed out but not acked

    importlib.reload(src.cursor_store)
    # After reload, the in-memory pending of "inode:200" is gone; committed wins.
    # A stale ack of "inode:200" must NOT advance, since we never persisted it.
    committed = src.cursor_store.cursor_store.ack_and_get_committed("inode:200")
    assert committed == "inode:100"


def test_repeated_matching_ack_is_idempotent(fresh_store: CursorStore) -> None:
    fresh_store.set_pending("inode:100")
    fresh_store.ack_and_get_committed("inode:100")
    # Same ack again, with pending unchanged — already committed, no-op.
    committed = fresh_store.ack_and_get_committed("inode:100")
    assert committed == "inode:100"
