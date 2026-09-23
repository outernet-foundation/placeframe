"""Spherical detection reads the file's own declaration, not its shape."""

from __future__ import annotations

import struct
from pathlib import Path

from panorama import video


def box(kind: bytes, payload: bytes = b"") -> bytes:
    return struct.pack(">I", 8 + len(payload)) + kind + payload


def sample_entry(kind: bytes, children: bytes) -> bytes:
    """A visual sample entry: 78 bytes of fixed header, then child boxes."""
    return box(kind, b"\x00" * 78 + children)


def mp4_with(projection: bytes | None, *, sample_entry_kind: bytes = b"hvc1") -> bytes:
    spherical = b""
    if projection is not None:
        spherical = box(
            b"sv3d",
            box(b"svhd", b"test\x00") + box(b"proj", box(b"prhd", b"\x00" * 16) + box(projection, b"\x00" * 20)),
        )
    stsd = box(b"stsd", b"\x00" * 8 + sample_entry(sample_entry_kind, box(b"hvcC", b"\x00" * 8) + spherical))
    moov = box(b"moov", box(b"trak", box(b"mdia", box(b"minf", box(b"stbl", stsd)))))
    return box(b"ftyp", b"isom" + b"\x00" * 8) + box(b"mdat", b"\x00" * 64) + moov


def test_equirectangular_video_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "pano.mp4"
    path.write_bytes(mp4_with(b"equi"))
    assert video.projection_of(path) == "EQUIRECTANGULAR"


def test_cubemap_video_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "cube.mp4"
    path.write_bytes(mp4_with(b"cbmp"))
    assert video.projection_of(path) == "CUBEMAP"


def test_ordinary_video_declares_nothing(tmp_path: Path) -> None:
    path = tmp_path / "flat.mp4"
    path.write_bytes(mp4_with(None))
    assert video.projection_of(path) is None


def test_other_codecs_are_walked_too(tmp_path: Path) -> None:
    for kind in (b"avc1", b"av01", b"encv"):
        path = tmp_path / f"{kind.decode()}.mp4"
        path.write_bytes(mp4_with(b"equi", sample_entry_kind=kind))
        assert video.projection_of(path) == "EQUIRECTANGULAR"


def test_a_file_that_is_not_an_mp4_is_not_spherical(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("this is not a video")
    assert video.projection_of(path) is None
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    assert video.projection_of(empty) is None
