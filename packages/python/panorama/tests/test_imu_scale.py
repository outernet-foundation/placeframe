"""The IMU's metric-scale fit, against a synthetic walk whose scale, gravity and sync are known.

The walk is simulated in metres with gravity down +y, its IMU read off it at 1 kHz (biased), and
its map made from it the way SfM would leave it: in arbitrary units, tilted, with the camera turned
from the IMU and the frame stamps running ahead of the IMU's clock.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from panorama import imu_scale
from panorama.motion import STANDARD_GRAVITY, Imu, Motion, motion_bytes, read_motion

METRES_PER_UNIT = 2.5
OFFSET_S = 0.2  # IMU time = frame-stamp time + offset
CAM_FROM_IMU = Rotation.from_euler("x", 11.0, degrees=True)
MAP_FROM_WORLD = Rotation.from_euler("xz", [20.0, -15.0], degrees=True)  # how unlevel SfM leaves it
ACCEL_BIAS = np.array([0.05, -0.2, 0.01])
GYRO_BIAS = np.array([0.002, -0.001, 0.0005])


def _walk(t: np.ndarray) -> tuple[np.ndarray, Rotation]:
    """Position (m) and world_from_body of a walk with a stride's bob and a slow weave."""
    position = np.stack(
        [
            1.2 * t + 0.3 * np.sin(2 * np.pi * 0.3 * t),
            0.04 * np.sin(2 * np.pi * 1.8 * t),
            0.8 * np.sin(2 * np.pi * 0.07 * t),
        ],
        -1,
    )
    turn = Rotation.from_euler(
        "yxz",
        np.stack([0.6 * np.sin(0.21 * t), 0.15 * np.sin(0.7 * t), 0.1 * np.sin(1.1 * t)], -1),
    )
    return position, turn


def _synthetic(duration_s: float = 60.0) -> tuple[Motion, imu_scale.Keyframes, imu_scale.Keyframes]:
    """The capture's motion, its map's keyframes, and the same map stabilised (rotations held still)."""
    dt = 1e-3
    t = np.arange(0.0, duration_s, dt)
    position, world_from_body = _walk(t)
    acceleration = np.gradient(np.gradient(position, dt, axis=0), dt, axis=0)
    gravity = np.array([0.0, STANDARD_GRAVITY, 0.0])
    accel = world_from_body.inv().apply(acceleration - gravity) + ACCEL_BIAS
    # body rate over each step, from the turn between consecutive samples
    _, ahead = _walk(t + dt)
    gyro = (world_from_body.inv() * ahead).as_rotvec() / dt + GYRO_BIAS
    imu = Imu(t, accel, gyro)

    stamps = np.arange(1.0, duration_s - 1.0, 1.0)  # one keyframe a second, as frame-stamp time
    true_t = stamps + OFFSET_S
    key_position, key_body = _walk(true_t)
    timestamps_ms = np.rint(stamps * 1000).astype(np.int64)
    motion = Motion(imu, timestamps_ms, stamps)
    map_position = MAP_FROM_WORLD.apply(key_position) / METRES_PER_UNIT
    map_from_cam = MAP_FROM_WORLD * key_body * CAM_FROM_IMU.inv()
    keys = imu_scale.keyframes(motion, timestamps_ms, map_position, map_from_cam)
    still = Rotation.from_quat(np.tile(map_from_cam[0].as_quat(), (len(stamps), 1)))
    stabilised = imu_scale.keyframes(motion, timestamps_ms, map_position, still)
    return motion, keys, stabilised


def test_the_fit_recovers_scale_gravity_and_sync() -> None:
    motion, keys, _ = _synthetic()
    report, sim3 = imu_scale.fit(keys, motion.imu)

    assert abs(report["sync"]["offset_s"] - OFFSET_S) <= 0.002
    assert report["sync"]["residual_deg_median"] < 0.05
    assert abs(report["free_gravity_norm_mps2"] / STANDARD_GRAVITY - 1) < 0.01
    assert abs(sim3["scale"] / METRES_PER_UNIT - 1) < 0.01
    # applied to the map, the Sim(3) puts gravity back on +y
    down_in_map = MAP_FROM_WORLD.apply([0.0, 1.0, 0.0])
    assert np.degrees(np.arccos(np.clip(np.asarray(sim3["R"]) @ down_in_map @ [0.0, 1.0, 0.0], -1, 1))) < 0.5
    assert imu_scale.rejection(report) is None


def test_a_stabilised_map_is_rejected_on_its_sync() -> None:
    motion, _, stabilised = _synthetic()
    report, _ = imu_scale.fit(stabilised, motion.imu)
    reason = imu_scale.rejection(report)
    assert reason is not None
    assert "camera body" in reason


def test_too_few_keyframes_are_rejected() -> None:
    motion, keys, _ = _synthetic(duration_s=12.0)
    report, _ = imu_scale.fit(keys, motion.imu)
    assert report["keyframes"] < imu_scale.MIN_KEYFRAMES
    assert "keyframes" in (imu_scale.rejection(report) or "")


def test_motion_round_trips_and_looks_frames_up_by_timestamp() -> None:
    imu = Imu(np.array([0.0, 0.001]), np.ones((2, 3)), np.zeros((2, 3)))
    motion = Motion(imu, np.array([0, 1001, 2002], dtype=np.int64), np.array([5.0, 6.0, 7.0]))
    back = read_motion(motion_bytes(motion))
    assert np.array_equal(back.frame_timestamps_ms, motion.frame_timestamps_ms)
    assert np.allclose(back.imu.accel, imu.accel)
    assert np.allclose(back.frame_times(np.array([2002, 0], dtype=np.int64)), [7.0, 5.0])
    with pytest.raises(ValueError, match="3003"):
        back.frame_times(np.array([3003], dtype=np.int64))
