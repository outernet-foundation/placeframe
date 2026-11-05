"""A run folder (export.py's output), loaded into arrays.

Frames: the camera's pose in Unity world from the tracker (VIO), for every video frame and every
still. Fixes: one VPS localization per still, against the map. The map: its points and the map
images that saw them, for choosing which points a camera could see.

Frames of reference:
  Unity world  the device's tracking frame (VIO), y up.
  ECEF         where the alignment points; the map sits in it at fix.ecef_from_map (identity for a map
               that is not georegistered).
  map          the reconstruction's own frame, Unity axes.
An alignment is Unity-from-ECEF, so a map point x lands in Unity world at
alignment @ ecef_from_map @ x, and a camera at unity_from_camera sees it at
inv(unity_from_camera) @ alignment @ ecef_from_map @ x.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from . import se3

Matrix = np.ndarray


@dataclass(frozen=True)
class Intrinsics:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float

    def project(self, points_camera: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Pixels and depths of points in a Unity camera's frame (x right, y up, z forward)."""
        z = points_camera[:, 2]
        with np.errstate(divide="ignore", invalid="ignore"):
            u = self.cx + self.fx * points_camera[:, 0] / z
            v = self.cy - self.fy * points_camera[:, 1] / z
        return np.stack([u, v], axis=1), z


@dataclass(frozen=True)
class Frame:
    index: int
    t: float
    timestamp_ns: int
    image: Path
    tracking_state: str
    unity_from_camera: Matrix


@dataclass
class Fix:
    """One still's localization."""

    still: int
    t: float
    ok: bool
    error: str | None
    camera_from_map: Matrix | None = None
    ecef_from_map: Matrix | None = None
    covariance: Matrix | None = None  # 6x6, [rotation, translation], as the filter takes it
    metrics: dict[str, Any] = field(default_factory=dict)
    gate_passed: bool | None = None
    inlier_uv: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))  # still pixels
    inlier_points: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))

    @property
    def num_inliers(self) -> int:
        return int(self.metrics.get("num_inliers") or 0)

    @property
    def map_from_camera(self) -> Matrix:
        assert self.camera_from_map is not None
        return np.linalg.inv(self.camera_from_map)


class Map:
    def __init__(self, path: Path) -> None:
        data = np.load(path)
        self.points: np.ndarray = data["points"].astype(np.float64)
        self.colors: np.ndarray = data["colors"]
        self.track_length: np.ndarray = data["track_length"]
        self.image_centres: np.ndarray = data["image_centres"].astype(np.float64)
        self.image_forwards: np.ndarray = data["image_forwards"].astype(np.float64)
        self.image_names: np.ndarray = data["image_names"]
        self._offsets: np.ndarray = data["image_point_offsets"]
        self._image_points: np.ndarray = data["image_points"]

    def points_seen_by(self, image: int) -> np.ndarray:
        return self._image_points[self._offsets[image] : self._offsets[image + 1]]

    def visible_points(
        self, map_from_camera: Matrix, radius_m: float = 12.0, max_angle_deg: float = 75.0, max_images: int = 10
    ) -> np.ndarray:
        """Indices of points a camera here could see: those seen by the map images nearest it that
        look the same way. Points behind walls, which a plain frustum test keeps, drop out."""
        centre = map_from_camera[:3, 3]
        forward = map_from_camera[:3, 2] / np.linalg.norm(map_from_camera[:3, 2])  # it may carry a scale
        distance = np.linalg.norm(self.image_centres - centre, axis=1)
        facing = self.image_forwards @ forward > np.cos(np.radians(max_angle_deg))
        candidates = np.flatnonzero((distance < radius_m) & facing)
        if not len(candidates):
            return np.flatnonzero(np.linalg.norm(self.points - centre, axis=1) < 2 * radius_m)
        nearest = candidates[np.argsort(distance[candidates])[:max_images]]
        return np.unique(np.concatenate([self.points_seen_by(i) for i in nearest]))


@dataclass
class Run:
    directory: Path
    video: list[Frame]
    stills: list[Frame]
    still_video_index: list[int]
    fixes: list[Fix]
    live: list[dict[str, Any]]
    video_intrinsics: Intrinsics
    still_intrinsics: Intrinsics
    map: Map
    meta: dict[str, Any]

    @property
    def times(self) -> np.ndarray:
        return np.array([f.t for f in self.video])

    def frame_at(self, t: float) -> int:
        """The last video frame at or before `t`."""
        return max(0, int(np.searchsorted(self.times, t, side="right")) - 1)

    def video_poses(self) -> np.ndarray:
        return np.stack([f.unity_from_camera for f in self.video])


def _frames(directory: Path, entries: list[dict[str, Any]]) -> list[Frame]:
    return [
        Frame(
            e["index"],
            e["t"],
            e["timestamp_ns"],
            directory / e["image"],
            e["tracking_state"],
            se3.from_dict(e["unity_from_camera"]),
        )
        for e in entries
    ]


def _fix(entry: dict[str, Any]) -> Fix:
    fix = Fix(entry["still"], entry["t"], entry["ok"], entry.get("error"))
    if not entry["ok"]:
        return fix
    fix.camera_from_map = se3.from_dict(entry["camera_from_map"])
    fix.ecef_from_map = se3.from_dict(entry["ecef_from_map"])
    fix.covariance = np.array(entry["measurement_covariance"], dtype=np.float64)
    fix.metrics = entry["metrics"]
    fix.gate_passed = (entry.get("gate") or {}).get("passed")
    inliers = entry["inliers"]
    fix.inlier_uv = np.array(inliers["uv"], dtype=np.float64).reshape(-1, 2)
    fix.inlier_points = np.array(inliers["point"], dtype=np.int64)
    return fix


def load(directory: str | Path) -> Run:
    directory = Path(directory)
    camera = json.loads((directory / "camera.json").read_text())
    vio = json.loads((directory / "vio.json").read_text())
    vps = json.loads((directory / "vps.json").read_text())
    stills = _frames(directory, vio["stills"])
    return Run(
        directory=directory,
        video=_frames(directory, vio["video"]),
        stills=stills,
        still_video_index=[e["video_index"] for e in vio["stills"]],
        fixes=[_fix(e) for e in vps["fixes"]],
        live=vps.get("live", []),
        video_intrinsics=Intrinsics(**camera["video"]),
        still_intrinsics=Intrinsics(**camera["stills"]),
        map=Map(directory / "map.npz"),
        meta={
            "recording": vio["recording"],
            "reconstruction_id": vps["reconstruction_id"],
            "device_model": vio.get("device_model"),
            "pose_space_fit": vio.get("pose_space_fit"),
        },
    )
