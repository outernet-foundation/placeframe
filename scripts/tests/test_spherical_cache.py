"""Whether a capture is spherical is asked of the API once per capture, ever.

Listing captures polls every capture's flag, and each uncached answer is a manifest fetch the API
serves by scanning the capture's tar; these tests pin that a cached or tarless capture costs none.
"""

from __future__ import annotations

import asyncio
from json import dumps
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from scripts import howard_test


def _session(capture_id: str, size_bytes: int) -> Any:
    return SimpleNamespace(id=capture_id, size_bytes=size_bytes)


def test_cached_and_tarless_captures_never_reach_the_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "capture_spherical.json"
    cache.write_text(dumps({"a": True, "b": False, "gone": True}))
    monkeypatch.setattr(howard_test, "SPHERICAL_FLAGS_CACHE", cache)

    def no_api() -> None:
        raise AssertionError("a cached or tarless capture must not fetch its manifest")

    monkeypatch.setattr(howard_test, "authenticated_api_client", no_api)
    sessions = [_session("a", 10), _session("b", 10), _session("imported", 0)]
    assert asyncio.run(howard_test.spherical_flags(sessions)) == [True, False, None]
