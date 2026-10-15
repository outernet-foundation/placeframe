"""Insta360 .insv: a native dual-fisheye recording, stitched here into equirectangular frames.

An .insv (checked against an Insta360 X4, firmware v1.2.31) is an mp4 holding one HEVC track per
lens -- two square circular-fisheye videos, lens 0 and lens 1 back to back -- plus an audio track,
followed by a proprietary trailer. OpenCV decodes only the first video track, so decoding goes
through PyAV. A spherical capture's tar holds equirectangular frames and the reconstructor renders
its views from those, so stitching at import keeps everything downstream unchanged: to the rest of
Placeframe an .insv is simply an equirectangular video.

The trailer
-----------
The file ends with a 72-byte footer: 32 bytes, the trailer's total size (u32 LE), a version (u32
LE), and the ASCII magic below. Before the footer sits an index record (id 0): 10-byte entries of
record id (u8), format (u8), size (u32 LE) and offset (u32 LE, from the trailer start). Record 1 is
a protobuf of camera metadata; its field 54 (one per file) is the factory lens calibration as an
underscore-separated string:

    2 _ [xi fx fy cx cy yaw pitch roll tx ty tz k1 k2 k3 p1 p2 W H n] x 2 lenses

i.e. a unified (Mei) omnidirectional model per lens on the 8000 x 6000 sensor: a ray at angle theta
off the lens axis lands at rho = sin(theta) / (cos(theta) + xi), distorted radially by
(1 + k1 rho^2 + k2 rho^4 + k3 rho^6), at f * rho sensor pixels from the centre. Field 27 gives the
sensor and the square crop the video is scaled from (8000 x 6000 -> 5632 x 5632 -> 3840 x 3840).
The radial model is used as calibrated, scaled by video / crop size; it reproduces the trailer's
own image-circle radius (2894 sensor px at 100 degrees, 1973 video px) to the pixel.

Fitted per file
---------------
Each lens's image centre comes from the factory calibration (the video is the sensor's centred
square crop); how the two lenses are turned relative to each other is fitted per file: SIFT
features matched across the seam (where both lenses see the same scene) on a few frames, then
least squares on the chord between the two lenses' rays for each match, about a fixed half turn.
On the X4 file lens 1 sits ~2.8 degrees off a clean half turn and the seam residual is ~11 arcmin
median -- what the lenses' ~3 cm separation produces for objects a few metres away, so that is the
precision the seam itself allows (freeing the centres too gains 2 arcmin by absorbing parallax).
With too few matches the fit falls back to a clean half turn.

Not used (yet): tangential distortion (p1, p2 ~ 1e-3) and fx != fy (0.03%), and the trailer's IMU
record (id 3: 56-byte samples, timestamp + accelerometer + gyroscope, ~358 Hz), which could give
real orientation priors in place of the synthetic trajectory a video import writes.
"""

from __future__ import annotations

import mmap
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from fractions import Fraction
from typing import Iterator, cast

import av
import numpy as np
from av.container import InputContainer
from av.packet import Packet
from av.video.frame import VideoFrame
from av.stream import Stream
from av.video.stream import VideoStream
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233

MAGIC = b"8db42d694ccc418790edff439fe026bf"
FOOTER = 72
METADATA_RECORD = 1
CALIBRATION_FIELD = 54  # the Mei model, both lenses
VIDEO_SIZE_FIELD = 19  # {1: width, 2: height} of each lens video
CROP_FIELD = 27  # {1: sensor w, 2: sensor h, 3: crop w, 4: crop h}
FIT_FRAMES = 5  # frames the seam fit samples, spread over the video
SEAM_RING = 0.78  # features only beyond this fraction of the half-width: the overlap
MIN_SEAM_MATCHES = 60
BLEND_DEG = 3.0  # half-width of the cross-fade at the seam
THETA_MAX_DEG = 100.0  # a lens is sampled no further than this off its axis


def is_insv(path: Path) -> bool:
    if path.suffix.lower() == ".insv":
        return True
    try:
        with open(path, "rb") as handle:
            handle.seek(-len(MAGIC), 2)
            return handle.read() == MAGIC
    except OSError:
        return False


# --- trailer -------------------------------------------------------------------------------------


def _varint(data: bytes, i: int) -> tuple[int, int]:
    value = shift = 0
    while True:
        byte = data[i]
        i += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return value, i


ProtobufValue = int | bytes


def _protobuf_fields(data: bytes) -> dict[int, list[ProtobufValue]]:
    """Top-level fields of a protobuf message: ints, and fixed / length-delimited payloads as bytes."""
    fields: dict[int, list[ProtobufValue]] = {}
    i = 0
    while i < len(data):
        key, i = _varint(data, i)
        number, wire = key >> 3, key & 7
        value: ProtobufValue
        if wire == 0:
            value, i = _varint(data, i)
        elif wire == 1:
            value, i = data[i : i + 8], i + 8
        elif wire == 5:
            value, i = data[i : i + 4], i + 4
        elif wire == 2:
            length, i = _varint(data, i)
            value, i = data[i : i + length], i + length
        else:
            break
        fields.setdefault(number, []).append(value)
    return fields


def _bytes_of(fields: dict[int, list[ProtobufValue]], number: int) -> bytes:
    value = fields[number][0]
    if not isinstance(value, bytes):
        raise TypeError(f"protobuf field {number} is not length-delimited")
    return value


def _int_of(fields: dict[int, list[ProtobufValue]], number: int) -> int:
    value = fields[number][0]
    if not isinstance(value, int):
        raise TypeError(f"protobuf field {number} is not an integer")
    return value


def trailer_records(path: Path) -> dict[int, bytes]:
    """{record id: payload} of the Insta360 trailer."""
    with open(path, "rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as m:
        n = len(m)
        if m[n - len(MAGIC) :] != MAGIC:
            raise ValueError(f"{path.name} has no Insta360 trailer")
        total: int = struct.unpack_from("<I", m, n - len(MAGIC) - 8)[0]
        start = n - total
        index_size: int = struct.unpack_from("<I", m, n - FOOTER - 4)[0]
        index = bytes(m[n - FOOTER - 6 - index_size : n - FOOTER - 6])
        records: dict[int, bytes] = {}
        for i in range(0, len(index) - 9, 10):
            rid, _fmt, size, offset = struct.unpack_from("<BBII", index, i)
            if size:
                records[rid] = bytes(m[start + offset : start + offset + size])
        return records


@dataclass(frozen=True)
class Lens:
    """The factory Mei model of one lens, on the sensor."""

    xi: float
    f: float
    k: tuple[float, float, float]

    def radius_px(self, theta: NDArray[np.float64], scale: float) -> NDArray[np.float64]:
        """Distance from the image centre, in video pixels, of a ray `theta` radians off axis."""
        rho = np.sin(theta) / (np.cos(theta) + self.xi)
        k1, k2, k3 = self.k
        return scale * self.f * rho * (1 + k1 * rho**2 + k2 * rho**4 + k3 * rho**6)


@dataclass(frozen=True)
class DualFisheye:
    lenses: tuple[Lens, Lens]
    size: int  # each lens video is size x size
    scale: float  # video px per sensor px
    centres: tuple[tuple[float, float], tuple[float, float]]
    lens1_to_lens0: NDArray[np.float64]  # rotation taking a lens-1 ray into lens 0's frame
    fps: float
    frame_count: int
    seam_matches: int
    seam_error_arcmin: float | None  # median, None when the fit fell back to defaults

    @property
    def equirect_width(self) -> int:
        return equirect_width_for(self.lenses[0], self.scale)


def equirect_width_for(lens: Lens, scale: float) -> int:
    """Equirectangular width carrying a lens's own angular resolution at its axis (multiple of 64)."""
    px_per_rad = lens.radius_px(np.array([0.01]), scale)[0] / 0.01
    return round(float(px_per_rad) * 2 * np.pi / 64) * 64


def read_calibration(
    path: Path,
) -> tuple[tuple[Lens, Lens], int, float, tuple[tuple[float, float], tuple[float, float]]]:
    """(lenses, video size, scale, image centres in video px) from the trailer's metadata record.

    The calibration's centres are on the sensor, both lenses side by side (the second lens's x is
    offset by one sensor width); each video is the sensor's centred square crop, scaled. On the X4
    file this puts both centres within 6 px of what a free fit to the seam finds, i.e. within the
    seam's own parallax noise, so the factory values are used and only the turn is fitted."""
    meta = _protobuf_fields(trailer_records(path)[METADATA_RECORD])
    values = _bytes_of(meta, CALIBRATION_FIELD).decode().split("_")
    if values[0] != "2":
        raise ValueError(f"{path.name}: expected a two-lens calibration, got {values[0]!r}")
    lenses: list[Lens] = []
    sensor_centres: list[tuple[float, float]] = []
    for k in range(2):
        v = [float(x) for x in values[1 + 19 * k : 1 + 19 * k + 16]]
        lenses.append(Lens(xi=v[0], f=0.5 * (v[1] + v[2]), k=(v[11], v[12], v[13])))
        sensor_centres.append((v[3], v[4]))
    size = _int_of(_protobuf_fields(_bytes_of(meta, VIDEO_SIZE_FIELD)), 1)
    crop_fields = _protobuf_fields(_bytes_of(meta, CROP_FIELD))
    sensor_w, sensor_h, crop = _int_of(crop_fields, 1), _int_of(crop_fields, 2), _int_of(crop_fields, 3)
    scale = size / crop
    centres = [
        (((cx % sensor_w) - (sensor_w - crop) / 2) * scale, (cy - (sensor_h - crop) / 2) * scale)
        for cx, cy in sensor_centres
    ]
    return (lenses[0], lenses[1]), size, scale, (centres[0], centres[1])


# --- decoding ------------------------------------------------------------------------------------

Image = NDArray[np.uint8]
Floats = NDArray[np.float64]


def _open(path: Path) -> tuple[InputContainer, list[VideoStream]]:
    container = av.open(str(path))
    streams = list(container.streams.video)
    if len(streams) != 2:
        container.close()
        raise ValueError(f"{path.name}: expected two video tracks (one per lens), found {len(streams)}")
    for stream in streams:
        stream.thread_type = "AUTO"
    return container, streams


def _video_frames(packet: Packet[Stream]) -> list[VideoFrame]:
    return [frame for frame in packet.decode() if isinstance(frame, VideoFrame)]


def _bgr(frame: VideoFrame) -> Image:
    return cast("Image", frame.to_ndarray(format="bgr24"))


def _frame_index(frame: VideoFrame, fps: float) -> int:
    pts = frame.pts if frame.pts is not None else 0
    return round(float(pts * frame.time_base) * fps)


def _stream_slot(streams: list[VideoStream], packet: Packet[Stream]) -> int:
    return 0 if packet.stream.index == streams[0].index else 1


def lens_pairs(path: Path, stride: int = 1) -> Iterator[tuple[int, Image, Image]]:
    """(frame index, lens 0 BGR, lens 1 BGR) for every `stride`-th frame, both tracks decoded in step."""
    container, streams = _open(path)
    fps = float(streams[0].average_rate or 30)
    pending: dict[int, dict[int, Image]] = {}
    try:
        for packet in container.demux(*streams):
            for frame in _video_frames(packet):
                index = _frame_index(frame, fps)
                if index % stride:
                    continue
                slot = pending.setdefault(index, {})
                slot[_stream_slot(streams, packet)] = _bgr(frame)
                if len(slot) == 2:
                    del pending[index]
                    yield index, slot[0], slot[1]
    finally:
        container.close()


def lens_pairs_at(path: Path, indices: list[int]) -> Iterator[tuple[int, Image, Image]]:
    """Both lenses at a few frames, by seeking (for sampling, not for a full pass)."""
    container, streams = _open(path)
    fps = float(streams[0].average_rate or 30)
    time_base = streams[0].time_base or Fraction(1, 30000)
    try:
        for want in indices:
            container.seek(int(want / fps / time_base), stream=streams[0], backward=True)
            got: dict[int, Image] = {}
            for packet in container.demux(*streams):
                for frame in _video_frames(packet):
                    index = _frame_index(frame, fps)
                    if index == want:
                        got[_stream_slot(streams, packet)] = _bgr(frame)
                    elif index > want + 2:
                        got.setdefault(_stream_slot(streams, packet), _bgr(frame))
                if len(got) == 2:
                    break
            if len(got) == 2:
                yield want, got[0], got[1]
    finally:
        container.close()


# --- per-file fit: the turn between the lenses ---------------------------------------------------

RadialTable = tuple[Floats, Floats]


def _ray(points: Floats, centre: Floats, table: RadialTable) -> Floats:
    """Unit rays in a lens's frame for its image points, through the radial table (theta, r)."""
    theta_table, r_table = table
    du, dv = points[:, 0] - centre[0], points[:, 1] - centre[1]
    theta = cast("Floats", np.interp(np.hypot(du, dv), r_table, theta_table))
    phi = np.arctan2(dv, du)
    return np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], -1)


def _rotvec_to_matrix(w: Floats) -> Floats:
    angle = float(np.linalg.norm(w))
    if angle < 1e-12:
        return np.eye(3)
    k = w / angle
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(angle) * kx + (1 - np.cos(angle)) * kx @ kx


def _seam_matches(a: Image, b: Image) -> tuple[Floats, Floats]:
    """SIFT matches between the outer rings of the two lens images, where both see the seam."""
    import cv2

    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    h, w = ga.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    ring = ((np.hypot(xx - w / 2, yy - h / 2) > SEAM_RING * w / 2) * 255).astype(np.uint8)
    sift = cv2.SIFT.create(nfeatures=20000)
    ka, da = sift.detectAndCompute(ga, ring)
    kb, db = sift.detectAndCompute(gb, ring)
    if len(ka) < 2 or len(kb) < 2:
        return np.zeros((0, 2)), np.zeros((0, 2))
    pairs = cv2.BFMatcher().knnMatch(da, db, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
    pa = np.array([ka[m.queryIdx].pt for m in good], dtype=np.float64).reshape(-1, 2)
    pb = np.array([kb[m.trainIdx].pt for m in good], dtype=np.float64).reshape(-1, 2)
    return pa, pb


HALF_TURN = np.array([[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]])  # 180 degrees about the vertical


def lens1_to_lens0(correction: Floats) -> Floats:
    """Lens 1 faces backwards: a fixed half turn about the vertical, corrected by a small rotation
    (parameterised this way because a rotation vector is singular at exactly 180 degrees)."""
    return _rotvec_to_matrix(correction) @ HALF_TURN


@dataclass(frozen=True)
class TurnFit:
    correction: Floats  # rotation vector applied to the half turn
    kept: NDArray[np.bool_]
    angles: Floats  # per match, radians


def fit_turn(
    pa: Floats, pb: Floats, centres: tuple[Floats, Floats], tables: tuple[RadialTable, RadialTable]
) -> TurnFit:
    """Gauss-Newton on the chord between the two lenses' rays for each match (smooth where the
    angle itself is not), reweighted against outliers, then the worst matches trimmed and refit."""

    def rays(w: Floats, a: Floats, b: Floats) -> tuple[Floats, Floats]:
        return _ray(a, centres[0], tables[0]), _ray(b, centres[1], tables[1]) @ lens1_to_lens0(w).T

    def residual(w: Floats, a: Floats, b: Floats) -> Floats:
        r0, r1 = rays(w, a, b)
        return (r0 - r1).ravel()

    def angles(w: Floats) -> Floats:
        r0, r1 = rays(w, pa, pb)
        return 2 * np.arcsin(np.clip(np.linalg.norm(r0 - r1, axis=1) / 2, 0.0, 1.0))

    w = np.zeros(3)
    keep = np.ones(len(pa), dtype=bool)
    for _round in range(4):
        for _iteration in range(20):
            a_, b_ = pa[keep], pb[keep]
            r = residual(w, a_, b_)
            per = np.linalg.norm(r.reshape(-1, 3), axis=1)
            robust = max(float(np.radians(0.3)), 1.4826 * float(np.median(per)))
            weight = np.sqrt(np.repeat(np.minimum(1.0, robust / np.maximum(per, 1e-12)), 3))
            jac = np.empty((len(r), 3))
            for j in range(3):
                step = np.zeros(3)
                step[j] = 1e-5
                jac[:, j] = (residual(w + step, a_, b_) - r) / 1e-5
            delta = np.linalg.lstsq(jac * weight[:, None], -r * weight, rcond=None)[0]
            w = w + delta
            if float(np.abs(delta).max()) < 1e-7:
                break
        ang = angles(w)
        keep = ang < max(float(np.radians(0.5)), 3 * float(np.median(ang[keep])))
    return TurnFit(w, keep, angles(w))


@lru_cache(maxsize=4)
def _calibrate_cached(path_str: str, mtime: float) -> DualFisheye:  # noqa: ARG001 — mtime keys the cache
    path = Path(path_str)
    lenses, size, scale, centres = read_calibration(path)
    container, streams = _open(path)
    fps = float(streams[0].average_rate or 30)
    frame_count = int(streams[0].frames)
    container.close()
    theta = np.radians(np.linspace(0.0, THETA_MAX_DEG + 10, 4000))
    tables = ((theta, lenses[0].radius_px(theta, scale)), (theta, lenses[1].radius_px(theta, scale)))

    picks = [int(frame_count * (i + 0.5) / FIT_FRAMES) for i in range(FIT_FRAMES)]
    found = [_seam_matches(a, b) for _index, a, b in lens_pairs_at(path, picks)]
    pa = np.vstack([m[0] for m in found]) if found else np.zeros((0, 2))
    pb = np.vstack([m[1] for m in found]) if found else np.zeros((0, 2))
    if len(pa) >= MIN_SEAM_MATCHES:
        fit = fit_turn(pa, pb, (np.array(centres[0]), np.array(centres[1])), tables)
        kept = int(fit.kept.sum())
        # a plausible turn is a few degrees off a clean half turn, not a different solution
        if float(np.linalg.norm(fit.correction)) < np.radians(10) and kept >= MIN_SEAM_MATCHES:
            median_arcmin = float(np.degrees(np.median(fit.angles[fit.kept])) * 60)
            return DualFisheye(
                lenses, size, scale, centres, lens1_to_lens0(fit.correction), fps, frame_count, kept, median_arcmin
            )
    return DualFisheye(lenses, size, scale, centres, HALF_TURN.copy(), fps, frame_count, len(pa), None)


def calibrate(path: Path) -> DualFisheye:
    """Factory lens models plus the per-file fit of the turn between the lenses (cached per file)."""
    return _calibrate_cached(str(path.resolve()), path.stat().st_mtime)


# --- stitching -----------------------------------------------------------------------------------

Map = NDArray[np.float32]


@dataclass(frozen=True)
class StitchMaps:
    width: int
    maps: tuple[tuple[Map, Map], tuple[Map, Map]]
    weight0: Map  # lens 0's share of each output pixel (lens 1 has the rest)


_MAPS: dict[tuple[int, int], StitchMaps] = {}


def _stitch_maps(calibration: DualFisheye, width: int) -> StitchMaps:
    # keyed by identity: a calibration holds a numpy rotation, so it is not hashable
    key = (id(calibration), width)
    if key not in _MAPS:
        _MAPS.clear()
        _MAPS[key] = build_stitch_maps(calibration, width)
    return _MAPS[key]


def build_stitch_maps(calibration: DualFisheye, width: int) -> StitchMaps:
    """Where each pixel of a width x width/2 equirectangular frame samples each lens, and how much
    of it comes from lens 0."""
    height = width // 2
    lon_1d = (np.arange(width, dtype=np.float64) + 0.5) / width * 2 * np.pi - np.pi
    lat_1d = np.pi / 2 - (np.arange(height, dtype=np.float64) + 0.5) / height * np.pi
    lon, lat = np.meshgrid(lon_1d, lat_1d)
    # panorama axes (y up, yaw 0 at the centre column) -> lens 0's OpenCV frame (y down)
    cam0 = np.stack([np.cos(lat) * np.sin(lon), -np.sin(lat), np.cos(lat) * np.cos(lon)], -1)
    cam1 = cam0 @ calibration.lens1_to_lens0  # = R^T applied to each ray
    maps: list[tuple[Map, Map]] = []
    thetas: list[Floats] = []
    for cam, lens, centre in zip((cam0, cam1), calibration.lenses, calibration.centres, strict=True):
        theta = np.arccos(np.clip(cam[..., 2], -1.0, 1.0))
        phi = np.arctan2(cam[..., 1], cam[..., 0])
        r = lens.radius_px(theta, calibration.scale)
        maps.append((
            (centre[0] + r * np.cos(phi)).astype(np.float32),
            (centre[1] + r * np.sin(phi)).astype(np.float32),
        ))
        thetas.append(np.degrees(theta))
    # cross-fade over BLEND_DEG either side of where the two lenses are equally far off axis
    weight0 = np.clip(0.5 + (thetas[1] - thetas[0]) / (2 * BLEND_DEG), 0.0, 1.0)
    weight0[thetas[0] > THETA_MAX_DEG] = 0.0
    weight0[thetas[1] > THETA_MAX_DEG] = 1.0
    return StitchMaps(width, (maps[0], maps[1]), weight0.astype(np.float32))


def stitch(calibration: DualFisheye, lens0: Image, lens1: Image, width: int) -> Image:
    """One equirectangular frame (BGR, width x width/2) from the two lens images."""
    import cv2

    maps = _stitch_maps(calibration, width)
    a = cv2.remap(lens0, maps.maps[0][0], maps.maps[0][1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    b = cv2.remap(lens1, maps.maps[1][0], maps.maps[1][1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    w = maps.weight0[..., None]
    return (a.astype(np.float32) * w + b.astype(np.float32) * (1 - w)).astype(np.uint8)


def equirect_frames(path: Path, stride: int = 1, width: int | None = None) -> Iterator[tuple[int, Image]]:
    """(frame index, stitched equirectangular BGR frame) for every `stride`-th frame."""
    calibration = calibrate(path)
    out_width = width or calibration.equirect_width
    for index, a, b in lens_pairs(path, stride):
        yield index, stitch(calibration, a, b, out_width)


def sample_equirect_frames(path: Path, count: int, width: int | None = None) -> Iterator[Image]:
    """`count` stitched frames spread across the video, by seeking."""
    calibration = calibrate(path)
    out_width = width or calibration.equirect_width
    picks = [int(calibration.frame_count * (i + 0.5) / max(1, count)) for i in range(max(1, count))]
    for _index, a, b in lens_pairs_at(path, picks):
        yield stitch(calibration, a, b, out_width)
