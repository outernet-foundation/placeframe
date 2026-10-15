"""Insta360 .insv: trailer parsing, the factory lens model, and the stitching geometry.

None of these need a real recording: the trailer is synthesised with the X4's own calibration
string, and the stitching is checked through its sampling tables.
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

from panorama import insv

# An Insta360 X4's factory calibration (metadata field 54), as recorded in a real file.
X4_CALIBRATION = (
    "2_1.948170_4619.730_4618.530_3988.670_3007.060_0.076_0.171_90.219_0.000000_0.000000_0.000000_"
    "0.41673359_1.16904235_-3.78381848_-0.00182471_-0.00124408_16000_6000_71_"
    "1.948170_4629.140_4628.570_12012.390_3009.750_-0.144_0.160_89.060_0.000000_0.000000_0.000000_"
    "0.41673359_1.16904235_-3.78381848_0.00089602_0.00086604_16000_6000_71"
)


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _field(number: int, payload: bytes) -> bytes:
    return _varint(number << 3 | 2) + _varint(len(payload)) + payload


def _int_field(number: int, value: int) -> bytes:
    return _varint(number << 3) + _varint(value)


def _metadata() -> bytes:
    size = _int_field(1, 3840) + _int_field(2, 3840)
    crop = _int_field(1, 8000) + _int_field(2, 6000) + _int_field(3, 5632) + _int_field(4, 5632)
    return (
        _field(2, b"Insta360 X4")
        + _field(insv.VIDEO_SIZE_FIELD, size)
        + _field(insv.CROP_FIELD, crop)
        + _field(insv.CALIBRATION_FIELD, X4_CALIBRATION.encode())
    )


def _insv_with_trailer(tmp_path: Path) -> Path:
    """A file whose tail is a trailer laid out as the X4 writes it: records, an index record, a
    72-byte footer ending in the size, version and magic."""
    meta = _metadata()
    body = b"\x00" * 128 + meta  # the trailer starts at the first byte of `body`
    meta_offset = 128
    index = b"\x00" * 10 + struct.pack("<BBII", 1, 1, len(meta), meta_offset)
    index_record = index + struct.pack("<HI", 0, len(index))
    footer_lead = b"\x00" * 32
    trailer_wo_size = body + index_record + footer_lead
    total = len(trailer_wo_size) + 8 + len(insv.MAGIC)
    trailer = trailer_wo_size + struct.pack("<II", total, 3) + insv.MAGIC
    path = tmp_path / "VID_test_00_000.insv"
    path.write_bytes(b"\x11" * 256 + trailer)
    return path


def test_trailer_and_calibration_are_read(tmp_path: Path) -> None:
    path = _insv_with_trailer(tmp_path)
    assert insv.is_insv(path)
    lenses, size, scale, centres = insv.read_calibration(path)
    assert size == 3840
    assert abs(scale - 3840 / 5632) < 1e-12
    assert abs(lenses[0].xi - 1.948170) < 1e-9
    assert abs(lenses[0].f - 0.5 * (4619.730 + 4618.530)) < 1e-9
    # the crop is centred on each lens's half of the sensor
    assert abs(centres[0][0] - (3988.670 - 1184) * scale) < 1e-6
    assert abs(centres[1][0] - (12012.390 - 8000 - 1184) * scale) < 1e-6
    assert abs(centres[1][1] - (3009.750 - 184) * scale) < 1e-6


def test_factory_model_reproduces_the_trailers_image_circle() -> None:
    """The compact calibration (field 5) gives the image-circle radius, 2893.893 sensor px; the
    full Mei model puts a ray 100 degrees off axis there."""
    lens = insv.Lens(xi=1.948170, f=0.5 * (4619.730 + 4618.530), k=(0.41673359, 1.16904235, -3.78381848))
    radius = lens.radius_px(np.radians(np.array([100.0])), 1.0)[0]
    assert abs(radius - 2893.893) < 5.0
    # monotonic over the field the stitcher samples, so it can be inverted by table lookup
    theta = np.radians(np.linspace(0, insv.THETA_MAX_DEG + 10, 2000))
    assert np.all(np.diff(lens.radius_px(theta, 1.0)) > 0)


def _calibration() -> insv.DualFisheye:
    lens = insv.Lens(xi=1.948170, f=4619.13, k=(0.41673359, 1.16904235, -3.78381848))
    return insv.DualFisheye(
        lenses=(lens, lens),
        size=3840,
        scale=3840 / 5632,
        centres=((1912.3, 1924.8), (1928.4, 1926.6)),
        lens1_to_lens0=insv.HALF_TURN.copy(),
        fps=29.97,
        frame_count=10,
        seam_matches=0,
        seam_error_arcmin=None,
    )


def test_stitch_sends_front_to_lens_0_and_back_to_lens_1() -> None:
    cal = _calibration()
    maps = insv.build_stitch_maps(cal, 640)
    h, w = maps.weight0.shape
    centre_row = h // 2
    # yaw 0 is the panorama's centre column: lens 0's axis, at lens 0's image centre
    front = (centre_row, w // 2)
    assert maps.weight0[front] == 1.0
    assert abs(maps.maps[0][0][front] - cal.centres[0][0]) < 15
    assert abs(maps.maps[0][1][front] - cal.centres[0][1]) < 15
    # yaw 180 (the edge column) is lens 1's axis
    back = (centre_row, 0)
    assert maps.weight0[back] == 0.0
    assert abs(maps.maps[1][0][back] - cal.centres[1][0]) < 15
    # the seam (yaw +-90) is a cross-fade, not a cut
    seam = maps.weight0[centre_row, w // 4]
    assert 0.0 < seam < 1.0


def test_equirect_width_carries_the_lens_resolution() -> None:
    cal = _calibration()
    # ~1073 video px per radian at the axis -> a 2*pi circumference of ~6740 px, rounded to 64
    assert cal.equirect_width == 6720
