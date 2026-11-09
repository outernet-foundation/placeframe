"""Metric scale and true gravity for a map of a spherical capture that carries its own IMU.

A spherical video's map comes out in arbitrary units, levelled only by the assumption that the
sphere was held upright: an imported video has no poses, so its frames.csv is a made-up straight
line. An .insv's importer adds the camera's IMU and frame times (panorama.motion) beside frames.csv,
and panorama.imu_scale fits them against the finished map. When the fit passes its checks the map
is scaled to metres and turned so gravity is +y, about its origin -- so the first registered frame
stays the origin, as the map-frame contract requires. When it does not, the map is left as it was.
Either way the full report is written beside the model (imu_scale.json) and the headline numbers
land in the metrics, so a map that was not scaled says why.

A failed fit never fails the reconstruction: the map is as good as it would be without an IMU.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from panorama import imu_scale
from panorama.motion import MOTION_MEMBER, read_motion
from pycolmap import Reconstruction, Rigid3d, Sim3d
from scipy.spatial.transform import Rotation

from .metrics_builder import MetricsBuilder

REPORT_FILE = "imu_scale.json"


def scale_from_imu(
    reconstruction: Reconstruction,
    registered: list[tuple[str, int, Rigid3d]],
    capture_path: Path,
    output_path: Path,
    metrics: MetricsBuilder,
) -> None:
    """Fit and, if the fit is sound, apply the IMU's scale and gravity to `reconstruction` in place.

    `registered` is (rig id, frame id, rig_from_world) per registered frame, as the map now stands.
    Only a single-rig capture is fitted: one sphere, one IMU.
    """
    rig_ids = {rig_id for rig_id, _, _ in registered}
    if len(rig_ids) != 1:
        return
    (rig_id,) = rig_ids
    motion_path = capture_path / rig_id / MOTION_MEMBER
    if not motion_path.is_file():
        return

    frame_ids = np.array([frame_id for _, frame_id, _ in registered], dtype=np.int64)
    world_from_rig = np.stack([pose.rotation.matrix().T for _, _, pose in registered])
    positions = np.stack([
        -matrix @ pose.translation for matrix, (_, _, pose) in zip(world_from_rig, registered, strict=True)
    ])
    try:
        motion = read_motion(motion_path)
        keys = imu_scale.keyframes(motion, frame_ids, positions, Rotation.from_matrix(world_from_rig))
        report, sim3 = imu_scale.fit(keys, motion.imu)
    except Exception as error:  # noqa: BLE001 — any failure leaves the map unscaled, never fails the job
        reason = f"the fit could not run: {error}"
        print(f"IMU scale: {reason}")
        metrics.metrics.imu_scale_applied = False
        metrics.metrics.imu_scale_rejected_because = reason
        _write_report(output_path, {"applied": False, "rejected_because": reason})
        return

    reason = imu_scale.rejection(report)
    applied = reason is None
    if applied:
        # The 3x4 form [scale * R | t], as the map-frame alignment builds its own Sim3d.
        scaled_rotation = float(sim3["scale"]) * np.asarray(sim3["R"], dtype=np.float64)
        reconstruction.transform(Sim3d(np.concatenate([scaled_rotation, np.zeros((3, 1))], axis=1)))
    print(
        f"IMU scale: {report['scale']:.4f} +- {report['scale_sigma']:.4f} m per map unit, "
        + ("applied" if applied else f"not applied: {reason}")
    )

    m = metrics.metrics
    m.imu_scale_applied = applied
    m.imu_scale_rejected_because = reason
    m.imu_scale_m_per_unit = float(report["scale"])
    m.imu_scale_sigma_m_per_unit = float(report["scale_sigma"])
    m.imu_sync_residual_deg = float(report["sync"]["residual_deg_median"])
    m.imu_free_gravity_mps2 = float(report["free_gravity_norm_mps2"])
    p_value = float(report["drift_p_value"])
    m.imu_scale_drift_p_value = None if math.isnan(p_value) else p_value
    _write_report(output_path, {**report, "sim3": sim3, "applied": applied, "rejected_because": reason})


def _write_report(output_path: Path, report: dict[str, Any]) -> None:
    (output_path / REPORT_FILE).write_text(json.dumps(report, indent=2))
