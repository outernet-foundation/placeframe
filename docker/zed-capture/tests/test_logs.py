import json
from pathlib import Path

import pytest

from src.routers.logs import read_logs


def _write_line(path: Path, text: str) -> None:
    with path.open("ab") as f:
        f.write(text.encode("utf-8"))


def _log_file(tmp_path: Path, name: str = "app.jsonl") -> Path:
    return tmp_path / name


def test_reads_all_lines_with_empty_cursor(tmp_path: Path):
    log = _log_file(tmp_path)
    _write_line(log, '{"msg":"a"}\n{"msg":"b"}\n{"msg":"c"}\n')

    batch = read_logs(tmp_path, cursor="", limit=100, max_bytes=1_000_000)

    assert [json.loads(e)["msg"] for e in batch.entries] == ["a", "b", "c"]
    assert batch.has_more is False
    assert batch.dropped_before is False
    assert batch.bytes_returned == log.stat().st_size


def test_resumes_from_cursor(tmp_path: Path):
    log = _log_file(tmp_path)
    _write_line(log, '{"msg":"a"}\n{"msg":"b"}\n')
    first = read_logs(tmp_path, cursor="", limit=100, max_bytes=1_000_000)

    _write_line(log, '{"msg":"c"}\n{"msg":"d"}\n')
    second = read_logs(tmp_path, cursor=first.next_cursor, limit=100, max_bytes=1_000_000)

    assert [json.loads(e)["msg"] for e in second.entries] == ["c", "d"]
    assert second.has_more is False


def test_skips_partial_trailing_line(tmp_path: Path):
    log = _log_file(tmp_path)
    _write_line(log, '{"msg":"a"}\n{"msg":"partial-no-newline"')
    batch = read_logs(tmp_path, cursor="", limit=100, max_bytes=1_000_000)

    assert [json.loads(e)["msg"] for e in batch.entries] == ["a"]

    _write_line(log, "}\n")
    next_batch = read_logs(tmp_path, cursor=batch.next_cursor, limit=100, max_bytes=1_000_000)
    assert [json.loads(e)["msg"] for e in next_batch.entries] == ["partial-no-newline"]


def test_halts_at_limit_and_reports_has_more(tmp_path: Path):
    log = _log_file(tmp_path)
    for i in range(10):
        _write_line(log, f'{{"msg":"line-{i}"}}\n')

    batch = read_logs(tmp_path, cursor="", limit=3, max_bytes=1_000_000)
    assert len(batch.entries) == 3
    assert batch.has_more is True

    rest = read_logs(tmp_path, cursor=batch.next_cursor, limit=100, max_bytes=1_000_000)
    assert len(rest.entries) == 7
    assert rest.has_more is False


def test_resumes_across_rotation(tmp_path: Path):
    current = _log_file(tmp_path)
    _write_line(current, '{"msg":"old-a"}\n{"msg":"old-b"}\n')
    first = read_logs(tmp_path, cursor="", limit=100, max_bytes=1_000_000)
    assert [json.loads(e)["msg"] for e in first.entries] == ["old-a", "old-b"]

    # Simulate RotatingFileHandler rollover: current → .1 (inode preserved), new current.
    rotated = _log_file(tmp_path, "app.jsonl.1")
    current.rename(rotated)
    _write_line(current, '{"msg":"new-a"}\n')

    # Prior cursor's inode is on the rotated file; resume should read .1 to EOF (nothing new there)
    # then move to current.
    second = read_logs(tmp_path, cursor=first.next_cursor, limit=100, max_bytes=1_000_000)
    assert [json.loads(e)["msg"] for e in second.entries] == ["new-a"]
    assert second.dropped_before is False


def test_flags_dropped_before_when_cursor_inode_missing(tmp_path: Path):
    log = _log_file(tmp_path)
    _write_line(log, '{"msg":"a"}\n')

    batch = read_logs(tmp_path, cursor="999999999999:0", limit=100, max_bytes=1_000_000)
    assert [json.loads(e)["msg"] for e in batch.entries] == ["a"]
    assert batch.dropped_before is True


def test_empty_dir_returns_empty_batch(tmp_path: Path):
    batch = read_logs(tmp_path, cursor="", limit=100, max_bytes=1_000_000)
    assert batch.entries == []
    assert batch.has_more is False
    assert batch.dropped_before is False


def test_rejects_malformed_cursor(tmp_path: Path):
    _write_line(_log_file(tmp_path), '{"msg":"a"}\n')
    with pytest.raises(Exception, match="Invalid cursor format"):
        read_logs(tmp_path, cursor="not-a-cursor", limit=100, max_bytes=1_000_000)
