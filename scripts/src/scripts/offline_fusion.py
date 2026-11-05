"""Replay a recorded localization run's VPS and VIO/VPS fusion offline, frame by frame.

A localization recording (the Capture Tool's LocalizationRecorder.cs) holds every camera frame as
video, full-resolution stills a few times a second, and the tracker's (VIO) pose for every frame,
all on the camera clock. This module runs what the device would have run over it:

1. Schedule. The device asks for a VPS fix every `vps_interval_s` (ThrottleLast) and drops a request
   while one is in flight (AwaitOperation.Drop); a fix arrives `vps_latency_s` after it was asked
   for. Each request localizes the latest still at that moment, against the map.
2. Fuse. RelocalizationFilter.cs, ported: an SE(3) Kalman filter over the Unity-from-ECEF alignment,
   with a chi-square innovation gate, and snap-or-slew of the published alignment.
3. Render. Each video frame with the map's points projected through the published alignment and the
   frame's VIO pose -- what the device would have drawn -- so jumps and drift are visible.

Every pose and point is in Unity's axes (x right, y up, z forward), as the device works; the map's
ECEF placement changes basis by diag(1, -1, 1), as LocationUtilities does.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation, Slerp

Matrix = NDArray[np.float64]

# ECEF and OpenCV are y-down; Unity is y-up (MathUtil.cs LocationUtilities).
BASIS_UNITY_FROM_ECEF = np.diag([1.0, -1.0, 1.0])

MAP_POINT_COLOR = (64, 255, 128)
FEATURE_COLOR = (255, 214, 10)
HUD_BACKGROUND = (0, 0, 0, 150)


# --- parameters ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class VpsParams:
    interval_s: float = 1.0  # VisualPositioningSystem.StartLocalizing(1.0f) in the Capture Tool
    latency_s: float = 2.0  # request to response, as measured on the device over Wi-Fi
    retrieval_top_k: int | None = None  # None: the server's default, as the device sends
    ransac_threshold: float | None = None
    use_chunking: bool = True


@dataclass(frozen=True)
class FusionParams:
    # Defaults are RelocalizationFilter.cs's constants.
    gate_chi2: float = 16.81
    bypass_gate: bool = False
    bypass_kalman: bool = False
    snap_sigmas_sq: float = 36.0
    slew_s: float = 0.5
    drift_per_m: float = 0.01
    base_translation_variance: float = 1e-4
    base_rotation_variance: float = 1e-6
    bootstrap_sigma_translation_m: float = 100.0
    bootstrap_sigma_rotation_rad: float = math.pi


# --- SE(3) (Se3.cs, MathUtil.cs) -----------------------------------------------------------------


def _skew(v: NDArray[np.float64]) -> Matrix:
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def _skew_inverse(m: Matrix) -> NDArray[np.float64]:
    return np.array([(m[2, 1] - m[1, 2]) * 0.5, (m[0, 2] - m[2, 0]) * 0.5, (m[1, 0] - m[0, 1]) * 0.5])


def se3_exp(xi: NDArray[np.float64]) -> Matrix:
    omega, rho = xi[:3], xi[3:]
    theta = float(np.linalg.norm(omega))
    skew = _skew(omega)
    if theta < 1e-6:
        rotation = np.eye(3) + skew
        v = np.eye(3) + 0.5 * skew
    else:
        skew2 = skew @ skew
        s = math.sin(theta) / theta
        c = (1.0 - math.cos(theta)) / theta**2
        k = (theta - math.sin(theta)) / theta**3
        rotation = np.eye(3) + s * skew + c * skew2
        v = np.eye(3) + c * skew + k * skew2
    return transform(rotation, v @ rho)


def se3_log(matrix: Matrix) -> NDArray[np.float64]:
    rotation, translation = matrix[:3, :3], matrix[:3, 3]
    theta = math.acos(min(1.0, max(-1.0, (np.trace(rotation) - 1.0) / 2.0)))
    if theta < 1e-6:
        omega = _skew_inverse(rotation - np.eye(3))
        v_inverse = np.eye(3) - 0.5 * _skew(omega)
    else:
        omega = (theta / (2.0 * math.sin(theta))) * _skew_inverse(rotation - rotation.T)
        skew = _skew(omega)
        b = 1.0 / theta**2 - (1.0 + math.cos(theta)) / (2.0 * theta * math.sin(theta))
        v_inverse = np.eye(3) - 0.5 * skew + b * skew @ skew
    return np.concatenate([omega, v_inverse @ translation])


def transform(rotation: Matrix, translation: NDArray[np.float64]) -> Matrix:
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    return matrix


def pose_matrix(position: list[float] | NDArray[np.float64], quaternion_xyzw: list[float]) -> Matrix:
    return transform(Rotation.from_quat(quaternion_xyzw).as_matrix(), np.asarray(position, dtype=np.float64))


def interpolate(a: Matrix, b: Matrix, t: float) -> Matrix:
    rotations = Rotation.from_matrix(np.stack([a[:3, :3], b[:3, :3]]))
    rotation = Slerp([0.0, 1.0], rotations)([t]).as_matrix()[0]
    return transform(rotation, a[:3, 3] + (b[:3, 3] - a[:3, 3]) * t)


def smooth_step(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


# --- the filter (RelocalizationFilter.cs) --------------------------------------------------------


@dataclass
class FilterState:
    mean: Matrix
    covariance: Matrix
    current: Matrix
    slew_start: Matrix
    slew_progress: float = 1.0
    last_accepted_vio_position: NDArray[np.float64] | None = None
    has_accepted: bool = False
    consecutive_rejections: int = 0


@dataclass
class StepResult:
    accepted: bool
    mahalanobis_sq: float
    snapped: bool
    measurement: Matrix


def bootstrap_covariance(params: FusionParams) -> Matrix:
    rotation = params.bootstrap_sigma_rotation_rad**2
    translation = params.bootstrap_sigma_translation_m**2
    return np.diag([rotation] * 3 + [translation] * 3)


def initial_state(params: FusionParams) -> FilterState:
    return FilterState(np.eye(4), bootstrap_covariance(params), np.eye(4), np.eye(4))


def process_noise(params: FusionParams, vio_position: NDArray[np.float64], last: NDArray[np.float64] | None) -> Matrix:
    noise = np.diag([params.base_rotation_variance] * 3 + [params.base_translation_variance] * 3)
    if last is None:
        return noise
    sigma = params.drift_per_m * float(np.linalg.norm(vio_position - last))
    return noise + np.eye(6) * sigma * sigma


def unity_from_map_basis(map_position: NDArray[np.float64], map_rotation: Matrix) -> Matrix:
    """The map's ECEF placement in Unity basis (LocationUtilities.ChangeBasisUnityFromEcef)."""
    basis = BASIS_UNITY_FROM_ECEF
    return transform(basis @ map_rotation @ basis.T, basis @ map_position)


def measurement_alignment(camera_from_map: Matrix, ecef_from_map: Matrix, unity_from_camera: Matrix) -> Matrix:
    """ComputeAlignmentFromResult: the Unity-from-ECEF alignment one localization implies, anchored
    on the camera so rotation noise cannot lever-arm the camera off its VIO position."""
    rotation_camera_from_map = camera_from_map[:3, :3]
    map_from_camera_translation = -rotation_camera_from_map.T @ camera_from_map[:3, 3]
    ecef_from_camera_translation = ecef_from_map[:3, :3] @ map_from_camera_translation + ecef_from_map[:3, 3]
    rotation = unity_from_camera[:3, :3] @ rotation_camera_from_map @ ecef_from_map[:3, :3].T
    translation = unity_from_camera[:3, 3] - rotation @ ecef_from_camera_translation
    return transform(rotation, translation)


def apply_measurement(
    state: FilterState,
    params: FusionParams,
    measurement: Matrix,
    measurement_covariance: Matrix,
    vio_position: NDArray[np.float64],
) -> StepResult:
    sigma_predicted = state.covariance + process_noise(params, vio_position, state.last_accepted_vio_position)
    residual = se3_log(np.linalg.inv(state.mean) @ measurement)
    innovation_covariance = sigma_predicted + measurement_covariance
    mahalanobis_sq = float(residual @ np.linalg.solve(innovation_covariance, residual))

    if not params.bypass_gate and mahalanobis_sq > params.gate_chi2:
        # Let process noise accumulate across rejections so the gate can reopen, capped at bootstrap.
        sigma_predicted[np.diag_indices(6)] = np.minimum(
            np.diag(sigma_predicted), np.diag(bootstrap_covariance(params))
        )
        state.covariance = sigma_predicted
        state.consecutive_rejections += 1
        return StepResult(False, mahalanobis_sq, False, measurement)

    if params.bypass_kalman:
        # The fix as it is, with its own uncertainty, so the next fix is still gated against it.
        new_mean, new_covariance = measurement, measurement_covariance
    else:
        gain = sigma_predicted @ np.linalg.inv(innovation_covariance)
        new_mean = state.mean @ se3_exp(gain @ residual)
        new_covariance = (np.eye(6) - gain) @ sigma_predicted

    snap = not state.has_accepted or params.bypass_kalman
    if not snap:
        shift = se3_log(np.linalg.inv(state.current) @ new_mean)
        snap = float(shift @ np.linalg.solve(new_covariance, shift)) > params.snap_sigmas_sq

    state.mean, state.covariance = new_mean, new_covariance
    if snap:
        state.slew_start = new_mean
        state.current = new_mean
        state.slew_progress = 1.0
    else:
        state.slew_start = state.current
        state.slew_progress = 0.0
    state.has_accepted = True
    state.last_accepted_vio_position = vio_position
    state.consecutive_rejections = 0
    return StepResult(True, mahalanobis_sq, snap, measurement)


def tick_slew(state: FilterState, params: FusionParams, delta_s: float) -> None:
    if state.slew_progress >= 1.0:
        return
    state.slew_progress = min(1.0, state.slew_progress + delta_s / params.slew_s)
    state.current = (
        state.mean
        if state.slew_progress >= 1.0
        else interpolate(state.slew_start, state.mean, smooth_step(state.slew_progress))
    )


# --- the recording -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Frame:
    timestamp_ns: int
    path: Path
    unity_from_camera: Matrix  # the tracker's pose for this frame
    tracking_state: str


@dataclass
class Recording:
    directory: Path
    manifest: dict[str, Any]
    video: list[Frame]
    stills: list[Frame]
    # How the camera poses were brought into Unity world, when they were recorded in a tracking space of
    # their own (a Magic Leap 2): the fit's residuals, for judging it.
    pose_space_fit: dict[str, float] | None = None

    @property
    def camera(self) -> dict[str, Any]:
        return self.manifest["camera"]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def _pose_vector(rows: list[dict[str, str]], prefix: str) -> list[Matrix]:
    return [
        pose_matrix(
            [float(row[f"{prefix}tx"]), float(row[f"{prefix}ty"]), float(row[f"{prefix}tz"])],
            [
                float(row[f"{prefix}qx"]),
                float(row[f"{prefix}qy"]),
                float(row[f"{prefix}qz"]),
                float(row[f"{prefix}qw"]),
            ],
        )
        for row in rows
    ]


def _from_params(params: NDArray[np.float64]) -> Matrix:
    return transform(Rotation.from_rotvec(params[:3]).as_matrix(), params[3:])


def _rms(vectors: Matrix) -> float:
    """Root mean square of the rows' lengths."""
    squared: Matrix = vectors * vectors
    return math.sqrt(float(squared.sum()) / max(1, len(vectors)))


def fit_pose_space(camera_poses: list[Matrix], head_poses: list[Matrix]) -> tuple[Matrix, Matrix, dict[str, float]]:
    """unity_from_space and camera_to_head such that head = unity_from_space @ camera @ camera_to_head.

    A Magic Leap 2 reports its camera's pose in its own tracking space, not Unity's world, so each
    camera pose is recorded beside the head's Unity-world pose at about the same moment. The two
    unknowns are fixed: where the tracking space sits in the world, and where the head sits relative
    to the camera. Solved by least squares over all the pairs (hand-eye calibration), which needs the
    head to have turned during the recording.
    """
    head_inverses = [np.linalg.inv(head) for head in head_poses]

    def residuals(params: NDArray[np.float64]) -> NDArray[np.float64]:
        unity_from_space = _from_params(params[:6])
        camera_to_head = _from_params(params[6:])
        return np.concatenate([
            se3_log(inverse @ unity_from_space @ camera @ camera_to_head)
            for inverse, camera in zip(head_inverses, camera_poses, strict=True)
        ])

    # Start with the head on the camera, which puts the space where the first pair says it is.
    first = head_poses[0] @ np.linalg.inv(camera_poses[0])
    initial = np.concatenate([Rotation.from_matrix(first[:3, :3]).as_rotvec(), first[:3, 3], np.zeros(6)])
    solution = least_squares(residuals, initial, loss="huber", f_scale=0.05)
    params = np.asarray(solution.x, dtype=np.float64)
    unity_from_space = _from_params(params[:6])
    camera_to_head = _from_params(params[6:])
    errors: Matrix = residuals(params).reshape(-1, 6)
    fit = {
        "translation_rms_m": _rms(errors[:, 3:]),
        "rotation_rms_deg": math.degrees(_rms(errors[:, :3])),
        "camera_to_head_m": float(np.linalg.norm(camera_to_head[:3, 3])),
        "pairs": float(len(camera_poses)),
    }
    return unity_from_space, camera_to_head, fit


def load_recording(directory: Path) -> Recording:
    """A recording unpacked into `directory`. Version 1 recordings kept one stream of full-resolution
    images, which serve as both the video and the stills."""
    import json  # noqa: PLC0415 — local to keep the module's import surface to what replay needs

    manifest = json.loads((directory / "manifest.json").read_text())
    tracking_rows = _read_csv(directory / "tracking.csv")
    tracking = {int(row["timestamp_ns"]): row for row in tracking_rows}

    # Camera poses in a tracking space of their own come with the head's Unity-world pose: put them in
    # Unity world, where live VPS (and so the alignment the filter estimates) works.
    unity_from_space: Matrix | None = None
    pose_space_fit = None
    paired = [row for row in tracking_rows if row.get("head_tx") and row["tracking_state"] == "Tracking"]
    if paired:
        unity_from_space, _, pose_space_fit = fit_pose_space(_pose_vector(paired, ""), _pose_vector(paired, "head_"))

    def frames(folder: str, csv_name: str) -> list[Frame]:
        result: list[Frame] = []
        for row in _read_csv(directory / csv_name):
            timestamp = int(row["timestamp_ns"])
            # The tracker's own sample for this camera frame when there is one; the pose read when the
            # image was taken otherwise. Both are the same camera frame's pose.
            source = tracking.get(timestamp, row)
            position = [float(source["tx"]), float(source["ty"]), float(source["tz"])]
            rotation = [float(source["qx"]), float(source["qy"]), float(source["qz"]), float(source["qw"])]
            state = tracking[timestamp]["tracking_state"] if timestamp in tracking else "Unknown"
            pose = pose_matrix(position, rotation)
            if unity_from_space is not None:
                pose = unity_from_space @ pose
            result.append(Frame(timestamp, directory / folder / f"{timestamp}.jpg", pose, state))
        return sorted(result, key=lambda frame: frame.timestamp_ns)

    if manifest.get("version", 1) >= 2:
        return Recording(
            directory, manifest, frames("video", "video.csv"), frames("stills", "stills.csv"), pose_space_fit
        )
    images = frames("images", "images.csv")
    return Recording(directory, manifest, images, images)


# --- the VPS schedule ----------------------------------------------------------------------------


@dataclass
class VpsRequest:
    still: Frame
    request_ns: int
    apply_ns: int
    # Filled by localizing the still: the server's response, or why there is none.
    response: dict[str, Any] | None = None
    error: str | None = None
    # Filled by fusing it.
    step: StepResult | None = None


def schedule_requests(recording: Recording, params: VpsParams) -> list[VpsRequest]:
    """The VPS requests the device would have made: on each interval tick, the latest still, unless a
    request is still in flight (then the tick is dropped, as AwaitOperation.Drop does)."""
    if not recording.stills or not recording.video:
        return []
    start = recording.video[0].timestamp_ns
    end = recording.video[-1].timestamp_ns
    interval_ns = round(params.interval_s * 1e9)
    latency_ns = round(params.latency_s * 1e9)
    stills = recording.stills
    requests: list[VpsRequest] = []
    busy_until = start
    used: set[int] = set()
    tick = start + interval_ns
    index = 0
    while tick <= end:
        while index + 1 < len(stills) and stills[index + 1].timestamp_ns <= tick:
            index += 1
        still = stills[index]
        if tick >= busy_until and still.timestamp_ns <= tick and still.timestamp_ns not in used:
            used.add(still.timestamp_ns)
            requests.append(VpsRequest(still, tick, tick + latency_ns))
            busy_until = tick + latency_ns
        tick += interval_ns
    return requests


# --- fusion over the video -----------------------------------------------------------------------


@dataclass
class FrameState:
    alignment: Matrix | None  # the published Unity-from-ECEF alignment; None before the first fix
    slewing: bool
    sigma_translation_m: float
    sigma_rotation_deg: float
    applied: list[int] = field(default_factory=list)  # indices of requests applied at this frame


def _measurement_from_response(response: dict[str, Any]) -> tuple[Matrix, Matrix, Matrix]:
    def matrix(t: dict[str, Any]) -> Matrix:
        r = t["rotation"]
        return pose_matrix(
            [t["translation"]["x"], t["translation"]["y"], t["translation"]["z"]], [r["x"], r["y"], r["z"], r["w"]]
        )

    camera_from_map = matrix(response["camera_from_map_transform"])
    map_transform = matrix(response["map_transform"])
    ecef_from_map = unity_from_map_basis(map_transform[:3, 3], map_transform[:3, :3])
    covariance = np.array(response["metrics"]["measurement_covariance"], dtype=np.float64)
    return camera_from_map, ecef_from_map, covariance


def fuse(recording: Recording, requests: list[VpsRequest], params: FusionParams) -> list[FrameState]:
    state = initial_state(params)
    states: list[FrameState] = []
    pending = sorted(range(len(requests)), key=lambda i: requests[i].apply_ns)
    next_request = 0
    previous_ns: int | None = None
    for frame in recording.video:
        applied: list[int] = []
        while next_request < len(pending) and requests[pending[next_request]].apply_ns <= frame.timestamp_ns:
            request = requests[pending[next_request]]
            next_request += 1
            applied.append(pending[next_request - 1])
            if request.response is None:
                continue
            camera_from_map, ecef_from_map, covariance = _measurement_from_response(request.response)
            measurement = measurement_alignment(camera_from_map, ecef_from_map, request.still.unity_from_camera)
            request.step = apply_measurement(
                state, params, measurement, covariance, request.still.unity_from_camera[:3, 3]
            )
        if previous_ns is not None:
            tick_slew(state, params, (frame.timestamp_ns - previous_ns) / 1e9)
        previous_ns = frame.timestamp_ns
        diagonal = np.diag(state.covariance)
        states.append(
            FrameState(
                state.current.copy() if state.has_accepted else None,
                state.slew_progress < 1.0,
                math.sqrt(float(diagonal[3:].sum())),
                math.degrees(math.sqrt(float(diagonal[:3].sum()))),
                applied,
            )
        )
    return states


# --- rendering -----------------------------------------------------------------------------------


def upright_intrinsics(camera: dict[str, Any], width: int, height: int) -> tuple[float, float, float, float]:
    """fx, fy, cx, cy of the upright image of a frame `width` x `height` as stored. Only the
    orientations devices record are handled: LEFT_TOP (a phone in portrait), BOTTOM_LEFT (a Magic Leap
    2, whose frames are stored bottom row first) and TOP_LEFT (as stored)."""
    scale = width / camera["width"]
    if camera["orientation"] == "LEFT_TOP":
        return camera["fy"] * scale, camera["fx"] * scale, camera["cy"] * scale, camera["cx"] * scale
    if camera["orientation"] == "BOTTOM_LEFT":
        return (
            camera["fx"] * scale,
            camera["fy"] * scale,
            camera["cx"] * scale,
            (camera["height"] - camera["cy"]) * scale,
        )
    if camera["orientation"] == "TOP_LEFT":
        return camera["fx"] * scale, camera["fy"] * scale, camera["cx"] * scale, camera["cy"] * scale
    raise ValueError(f"Unsupported orientation {camera['orientation']}")


def upright(image: Image.Image, orientation: str) -> Image.Image:
    if orientation == "LEFT_TOP":
        return image.transpose(Image.Transpose.TRANSPOSE)
    if orientation == "BOTTOM_LEFT":
        return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return image


def project(
    points_unity: NDArray[np.float64], camera_from_unity: Matrix, intrinsics: tuple[float, float, float, float]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Pixel positions in the upright image and depths of the points in front of a Unity camera
    (x right, y up, z forward)."""
    fx, fy, cx, cy = intrinsics
    camera = points_unity @ camera_from_unity[:3, :3].T + camera_from_unity[:3, 3]
    in_front = camera[:, 2] > 0.05
    camera = camera[in_front]
    pixels = np.stack([cx + fx * camera[:, 0] / camera[:, 2], cy - fy * camera[:, 1] / camera[:, 2]], axis=1)
    return pixels, camera[:, 2]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def render_frame(
    frame: Frame,
    orientation: str,
    intrinsics: tuple[float, float, float, float],
    points_map: NDArray[np.float64],
    unity_from_map: Matrix | None,
    hud: list[str],
    features: NDArray[np.float64] | None,
) -> Image.Image:
    """One video frame as the device would have shown it: the map's points drawn where the published
    alignment and the frame's VIO pose put them, and on a frame VPS localized, the features it matched."""
    image = upright(Image.open(frame.path).convert("RGB"), orientation)
    pixels = np.asarray(image).copy()
    height, width = pixels.shape[:2]
    if unity_from_map is not None:
        points_unity = points_map @ unity_from_map[:3, :3].T + unity_from_map[:3, 3]
        uv, _ = project(points_unity, np.linalg.inv(frame.unity_from_camera).astype(np.float64), intrinsics)
        u = np.round(uv[:, 0]).astype(np.int64)
        v = np.round(uv[:, 1]).astype(np.int64)
        for du in (0, 1):
            for dv in (0, 1):
                inside = (u + du >= 0) & (u + du < width) & (v + dv >= 0) & (v + dv < height)
                pixels[v[inside] + dv, u[inside] + du] = MAP_POINT_COLOR
    image = Image.fromarray(pixels)
    draw = ImageDraw.Draw(image, "RGBA")
    if features is not None:
        for x, y in features:
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), outline=FEATURE_COLOR, width=1)
    font = _font(13)
    line_height = 16
    draw.rectangle((0, 0, width, 6 + line_height * len(hud)), fill=HUD_BACKGROUND)
    for row, text in enumerate(hud):
        draw.text((6, 3 + row * line_height), text, fill=(255, 255, 255), font=font)
    return image


def inlier_features(detail: dict[str, Any] | None, scale: float) -> NDArray[np.float64] | None:
    """The query keypoints PnP kept as inliers, from a localization's detail, scaled from the
    localizer's canonical image (upright, 1024 px shorter side) to the rendered one."""
    if not detail:
        return None
    points = [
        xy
        for pair in detail.get("pairs", [])
        for xy, status in zip(pair.get("query_xy", []), pair.get("status", []), strict=False)
        if status == 2  # MATCH_INLIER
    ]
    if not points:
        return None
    return np.unique(np.round(np.asarray(points, dtype=np.float64) * scale, 1), axis=0)
