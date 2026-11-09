"""A spherical camera's own motion data, carried in its capture beside the frames.

An Insta360 .insv records its IMU at 1 kHz and a timestamp per frame on the IMU's clock (decoded by
panorama.insv). The importer writes both into the capture as one npz per rig (MOTION_MEMBER), keyed
by the frame timestamps frames.csv uses, so that the reconstructor -- which never sees the .insv and
has no video decoder -- can fit the map's metric scale from them (panorama.imu_scale). Numpy only,
so reading it costs a service nothing it does not already have.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233

Floats = NDArray[np.float64]

STANDARD_GRAVITY = 9.80665
MOTION_MEMBER = "imu.npz"  # in each rig's directory, beside frames.csv


@dataclass(frozen=True)
class Imu:
    """The IMU's samples, on lens 0's OpenCV axes (the stitched sphere's camera frame)."""

    t_s: Floats  # (n,) seconds, on the clock frame_times reads
    accel: Floats  # (n, 3) specific force, m/s^2: a still, upright camera reads ~(0, -9.81, 0)
    gyro: Floats  # (n, 3) angular velocity, rad/s


@dataclass(frozen=True)
class Motion:
    imu: Imu
    frame_timestamps_ms: NDArray[np.int64]  # (m,) as frames.csv names the frames
    frame_t_s: Floats  # (m,) when each was taken, on the IMU's clock (before any sync offset)

    def frame_times(self, timestamps_ms: NDArray[np.int64]) -> Floats:
        """The IMU-clock time of each frame named, by its frames.csv timestamp."""
        index = {int(t): i for i, t in enumerate(self.frame_timestamps_ms)}
        missing = [int(t) for t in timestamps_ms if int(t) not in index]
        if missing:
            raise ValueError(f"No frame time recorded for frames {missing[:5]}")
        return self.frame_t_s[[index[int(t)] for t in timestamps_ms]]


def motion_bytes(motion: Motion) -> bytes:
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        t_s=motion.imu.t_s,
        accel=motion.imu.accel.astype(np.float32),  # ~1e-7 relative: far below the sensor's own noise
        gyro=motion.imu.gyro.astype(np.float32),
        frame_timestamps_ms=motion.frame_timestamps_ms,
        frame_t_s=motion.frame_t_s,
    )
    return buffer.getvalue()


def read_motion(source: Path | bytes) -> Motion:
    with np.load(io.BytesIO(source) if isinstance(source, bytes) else source) as data:
        return Motion(
            Imu(
                data["t_s"].astype(np.float64),
                data["accel"].astype(np.float64),
                data["gyro"].astype(np.float64),
            ),
            data["frame_timestamps_ms"].astype(np.int64),
            data["frame_t_s"].astype(np.float64),
        )
