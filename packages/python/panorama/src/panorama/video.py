"""What kind of video is this, and how to get frames out of it.

Spherical video declares itself: the Google spatial-media v2 boxes `sv3d` ->
`proj` -> `prhd` + a projection box name the projection, `equi` being
equirectangular. That is read here rather than guessed from a 2:1 aspect ratio,
so an ordinary wide video is not mistaken for a panorama (and a cropped or
padded panorama is not missed).

Decoding needs OpenCV, which is an optional extra of this package: services that
only render views from already-extracted frames need not carry it.
"""

from __future__ import annotations

import mmap
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, cast

import numpy as np
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233

# ISO base media file format container boxes worth descending into while
# looking for sv3d, which lives under the video sample entry.
_CONTAINER_BOXES = {
    b"moov",
    b"trak",
    b"mdia",
    b"minf",
    b"stbl",
    b"stsd",
    b"sv3d",
    b"proj",
    b"avc1",
    b"hev1",
    b"hvc1",
    b"encv",
    b"mp4v",
    b"av01",
}
# Visual sample entries carry a fixed 78-byte header after their box header,
# before any child boxes (sv3d among them).
_SAMPLE_ENTRY_BOXES = {b"avc1", b"hev1", b"hvc1", b"encv", b"mp4v", b"av01"}
_SAMPLE_ENTRY_HEADER = 78
_PROJECTIONS = {b"equi": "EQUIRECTANGULAR", b"cbmp": "CUBEMAP", b"mshp": "MESH"}


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    width: int
    height: int
    fps: float
    frame_count: int
    projection: str | None  # None when the file declares no spherical projection

    @property
    def is_spherical(self) -> bool:
        return self.projection is not None

    @property
    def is_equirectangular(self) -> bool:
        return self.projection == "EQUIRECTANGULAR"

    @property
    def duration_s(self) -> float:
        return self.frame_count / self.fps if self.fps else 0.0


def _walk(data: memoryview, offset: int, end: int, found: list[bytes]) -> None:
    while offset + 8 <= end:
        size = struct.unpack_from(">I", data, offset)[0]
        kind = bytes(data[offset + 4 : offset + 8])
        header = 8
        if size == 1:  # 64-bit size follows the type
            if offset + 16 > end:
                return
            size = struct.unpack_from(">Q", data, offset + 8)[0]
            header = 16
        elif size == 0:  # extends to the end of the file
            size = end - offset
        if size < header or offset + size > end:
            return
        if kind in _PROJECTIONS:
            found.append(kind)
        if kind in _CONTAINER_BOXES:
            child = offset + header + (_SAMPLE_ENTRY_HEADER if kind in _SAMPLE_ENTRY_BOXES else 0)
            if kind == b"stsd":
                child += 8  # version/flags + entry count
            _walk(data, child, offset + size, found)
        offset += size


def projection_of(path: Path) -> str | None:
    """The declared spherical projection of an mp4, or None if it declares none.

    Mapped rather than read: the boxes that matter are a few hundred bytes, and
    a video file can be many gigabytes.
    """
    found: list[bytes] = []
    with open(path, "rb") as handle:
        if path.stat().st_size < 8:
            return None
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
            _walk(memoryview(mapped), 0, len(mapped), found)
    return _PROJECTIONS[found[0]] if found else None


def inspect(path: Path) -> VideoInfo:
    """Size, frame rate, length and declared projection. Needs the `video` extra."""
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"could not open {path}")
    try:
        return VideoInfo(
            path=path,
            width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=float(capture.get(cv2.CAP_PROP_FPS)),
            frame_count=int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            projection=projection_of(path),
        )
    finally:
        capture.release()


def frames(path: Path, stride: int = 1) -> Iterator[tuple[int, NDArray[np.uint8]]]:
    """Yield (frame index, BGR frame) for every `stride`-th frame. Needs the `video` extra."""
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"could not open {path}")
    try:
        index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                return
            if index % stride == 0:
                # cv2 types frames as MatLike; every decoded frame is an 8-bit array.
                yield index, cast("NDArray[np.uint8]", frame)
            index += 1
    finally:
        capture.release()
