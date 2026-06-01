from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import Any, Iterator, ValuesView, cast

from placeframe_api_client import ReconstructionStatus

from numpy import (
    asarray,
    concatenate,
    diag,
    empty,
    eye,
    float32,
    float64,
    intp,
    median,
    savez_compressed,
    sign,
    stack,
    uint8,
    uint32,
)
from numpy.linalg import det, norm, svd
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Camera as ColmapCamera
from pycolmap import (
    Database,
    Frame,
    GeometricVerifierOptions,
    Point3D,
    PosePrior,
    PosePriorCoordinateSystem,
    Reconstruction,
    Rigid3d,
    SensorType,
    Sim3d,
    TwoViewGeometry,
    TwoViewGeometryConfiguration,
    data_t,
    sensor_t,
)
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, bundle_adjustment, geometric_verification  # noqa: PLC2701 — no public API  # pyright: ignore[reportUnknownVariableType] — upstream stub uses unparameterized os.PathLike
from pycolmap._core import incremental_mapping  # noqa: PLC2701 — no public API  # pyright: ignore[reportUnknownVariableType] — upstream stub uses unparameterized os.PathLike
from scipy.spatial.transform import Rotation

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .progress_publisher import ReconstructionPublisher
from .rig import FramePose, Rig

COLMAP_DB_FILE = "database.db"
COLMAP_SFM_DIRECTORY = "sfm_model"


def run_colmap_reconstruction(
    root_path: Path,
    output_path: Path,
    images_path: Path,
    options: OptionsBuilder,
    metrics: MetricsBuilder,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
    pairs: list[tuple[str, str]],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    publisher: ReconstructionPublisher,
):
    colmap_db_path = root_path / COLMAP_DB_FILE
    if colmap_db_path.exists():
        colmap_db_path.unlink()

    colmap_sfm_directory = root_path / COLMAP_SFM_DIRECTORY
    if colmap_sfm_directory.exists():
        rmtree(colmap_sfm_directory)

    colmap_sfm_directory.mkdir(parents=True)

    position_covariance = (options.pose_prior_position_sigma_m() ** 2) * eye(3, dtype=float64)

    # Create COLMAP database
    database = Database.open(str(colmap_db_path))  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike
    # Write cameras, images, keypoints, and pose priors to database
    colmap_image_ids: dict[str, int] = {}
    image_cameras: dict[str, ColmapCamera] = {}
    for rig_id, rig in rigs.items():
        for camera_id, camera in rig.cameras.items():
            colmap_camera_id = database.write_camera(camera[1])

            for frame_id, transform in rig.frame_poses.items():
                image_name = f"{rig_id}/{camera_id}/{frame_id}.jpg"

                colmap_image_ids[image_name] = database.write_image(
                    pycolmapImage(name=image_name, camera_id=colmap_camera_id)
                )
                image_cameras[image_name] = camera[1]
                database.write_keypoints(colmap_image_ids[image_name], keypoints[image_name])

                # Pose priors only carry position; write only when the capture supplies a position
                # (ARFoundation does, multi-rig ZED captures don't).
                if camera[0].ref_sensor and transform.translation is not None:
                    database.write_pose_prior(
                        PosePrior(
                            position=transform.translation.reshape(3, 1),
                            position_covariance=position_covariance,
                            coordinate_system=PosePriorCoordinateSystem.CARTESIAN,
                            corr_data_id=data_t(
                                sensor_t(SensorType.CAMERA, colmap_camera_id),
                                colmap_image_ids[image_name],
                            ),
                        ),
                    )

    # Apply rig configuration to database (must be done after writing cameras and images)
    apply_rig_config([rig.colmap_rig_config for rig in rigs.values()], database)

    # COLMAP assigns rig_t IDs at apply_rig_config time; harvest them so the
    # incremental BA loop can pin every rig's sensor_from_rig transform.
    constant_rigs = {rig.rig_id for rig in database.read_all_rigs()}

    # Write matches to database
    for a, b in pairs:
        (image_a_indices, image_b_indices) = match_indices[(a, b)]
        database.write_matches(
            colmap_image_ids[a],
            colmap_image_ids[b],
            stack((image_a_indices, image_b_indices), axis=1).astype(uint32, copy=False),
        )

    # Build the seed two_view_geometry per pair from VIO priors so geometric_verification can run
    # with use_existing_relative_pose=True. The seed pose replaces COLMAP's per-pair EM RANSAC with
    # an inlier-count check against the VIO-derived cam2_from_cam1, collapsing the EM stage from
    # ~30 minutes to seconds on this hardware. The rig pass still runs (and may rewrite the pose)
    # but starts from a near-correct model.
    cam_from_rig_by_image_prefix: dict[str, Rigid3d] = {
        camera.image_prefix: camera.cam_from_rig
        for rig in rigs.values()
        for camera in rig.colmap_rig_config.cameras
        if camera.cam_from_rig is not None
    }
    rig_from_world_by_rig_and_frame: dict[tuple[str, str], Rigid3d] = {}
    for rig_id, rig in rigs.items():
        for frame_id, pose in rig.frame_poses.items():
            if pose.rotation is None or pose.translation is None:
                continue
            rig_from_world_by_rig_and_frame[(rig_id, frame_id)] = Rigid3d(
                rotation=pose.rotation, translation=pose.translation
            )

    seed_skipped = 0
    for a, b in pairs:
        rig_a, _, frame_a_dot = a.split("/", 2)
        rig_b, _, frame_b_dot = b.split("/", 2)
        frame_a = frame_a_dot.rsplit(".", 1)[0]
        frame_b = frame_b_dot.rsplit(".", 1)[0]
        cam_a_from_rig = cam_from_rig_by_image_prefix.get(a.rsplit("/", 1)[0] + "/")
        cam_b_from_rig = cam_from_rig_by_image_prefix.get(b.rsplit("/", 1)[0] + "/")
        rig_a_from_world = rig_from_world_by_rig_and_frame.get((rig_a, frame_a))
        rig_b_from_world = rig_from_world_by_rig_and_frame.get((rig_b, frame_b))
        if cam_a_from_rig is None or cam_b_from_rig is None or rig_a_from_world is None or rig_b_from_world is None:
            seed_skipped += 1
            continue
        cam2_from_cam1 = cam_b_from_rig * rig_b_from_world * rig_a_from_world.inverse() * cam_a_from_rig.inverse()
        seed = TwoViewGeometry()
        seed.config = TwoViewGeometryConfiguration.CALIBRATED
        seed.cam2_from_cam1 = cam2_from_cam1
        database.write_two_view_geometry(colmap_image_ids[a], colmap_image_ids[b], seed)

    print(f"[verification] seeded {len(pairs) - seed_skipped}/{len(pairs)} pairs from VIO priors")

    # Close the database before handing off to geometric_verification — the C++ entry point opens
    # its own connection from the path.
    database.close()

    # Stock pycolmap geometric_verification with rig_verification=True and use_existing_relative_pose
    # so the EM pass becomes an inlier-count check against the VIO seed instead of RANSAC. Single
    # opaque C++ call that holds the GIL throughout — set the phase with no total so the UI shows
    # it as an indeterminate step.
    publisher.set_phase(ReconstructionStatus.VERIFYING_GEOMETRY)
    geometric_verification(
        database_path=str(colmap_db_path),
        verifier_options=GeometricVerifierOptions(rig_verification=True, use_existing_relative_pose=True),
        two_view_geometry_options=options.two_view_geometry_options(),
    )

    # Compute and store verified matches metrics
    metrics.build_verified_matches_metrics(colmap_db_path, pairs)

    progress = _IncrementalMappingProgress(publisher)

    # Phase total is the candidate image count — an upper bound, since COLMAP may drop images that
    # fail to register or get filtered after bundle adjustment.
    publisher.set_phase(ReconstructionStatus.RECONSTRUCTING, len(colmap_image_ids))
    reconstructions = incremental_mapping(
        database_path=str(colmap_db_path),
        image_path=str(images_path),
        output_path=str(colmap_sfm_directory),
        options=options.incremental_pipeline_options(constant_rigs),
        initial_image_pair_callback=progress.on_initial_image_pair,
        next_image_callback=progress.on_next_image,
    )

    # Check that at least one reconstruction was created
    if len(reconstructions) == 0:
        return None

    # Choose the reconstruction with the most registered images
    # TODO: Write information to metrics about this for visibility
    best_reconstruction = max(reconstructions.values(), key=lambda r: r.num_reg_images())

    # Final standalone BA with rig refinement re-enabled. The incremental loop above ran with
    # rig refinement off (every global BA refining rig poses scales N times); one final pass
    # lets sensor_from_rig settle against the converged geometry.
    bundle_adjustment(best_reconstruction, options.final_bundle_adjustment_options())

    metrics.build_reconstruction_metrics(best_reconstruction)

    # Sort registered frames by integer timestamp across rigs so "first registered" is the
    # earliest-captured frame the recon kept, regardless of rig.
    registered = sorted(_registered_frames(rigs, colmap_image_ids, best_reconstruction), key=lambda entry: entry[0])
    if not registered:
        raise RuntimeError("Could not find anchor frame in best reconstruction")

    # Align the map frame to gravity via per-frame samples: each frame's gravity-in-rig-local is
    # projected into recon-world by the recon's own rig-rotation for that frame, then aggregated
    # via per-component median and renormalised. Robust to per-frame IMU noise and to VIO tilt
    # drift over the capture. Falls back to identity rotation when no samples are available.
    gravity_samples_in_recon_world = [
        rig_from_world.rotation.matrix().T @ transform.gravity_in_rig_local
        for _frame_id, transform, rig_from_world in registered
        if transform.gravity_in_rig_local is not None
    ]
    if gravity_samples_in_recon_world:
        gravity_stack = stack(gravity_samples_in_recon_world)
        gravity_in_recon_world_estimate = median(gravity_stack, axis=0)
        gravity_in_recon_world_estimate /= norm(gravity_in_recon_world_estimate)
        # OPENCV convention: +Y is the world's "down" axis, so map-frame down is also [0, 1, 0].
        alignment_rotation, _ = Rotation.align_vectors([[0.0, 1.0, 0.0]], [gravity_in_recon_world_estimate])
        rotation_align = alignment_rotation.as_matrix()
        metrics.metrics.gravity_aligned_in_map_frame = True
        metrics.metrics.gravity_sample_count = len(gravity_samples_in_recon_world)
    else:
        rotation_align = eye(3, dtype=float64)
        metrics.metrics.gravity_aligned_in_map_frame = False
        metrics.metrics.gravity_sample_count = 0

    _first_frame_id, _first_transform, first_rig_from_world = registered[0]
    first_camera_position = -first_rig_from_world.rotation.matrix().T @ first_rig_from_world.translation
    translation_align = -rotation_align @ first_camera_position
    best_reconstruction.transform(Sim3d(concatenate([rotation_align, translation_align.reshape(3, 1)], axis=1)))

    # Rigid Umeyama best-fit of map centers to VIO position priors. Fit is not applied — the
    # residual is the prior-drift diagnostic surfaced for calibration-corpus filtering. No signal
    # without position priors, so this skips for multi-camera captures (which carry no per-frame
    # translations by contract).
    if not options.is_multi_camera_capture:
        truth_centers_list: list[NDArray[float64]] = [
            transform.translation.astype(float64)
            for _frame_id, transform, _ in registered
            if transform.translation is not None
        ]
        map_centers_list: list[NDArray[float64]] = [
            -rig_from_world.rotation.matrix().T @ rig_from_world.translation
            for _frame_id, transform, rig_from_world in registered
            if transform.translation is not None
        ]
        if len(truth_centers_list) >= 3:
            truth_centers = asarray(truth_centers_list, dtype=float64)
            map_centers = asarray(map_centers_list, dtype=float64)
            truth_mean, map_mean = truth_centers.mean(axis=0), map_centers.mean(axis=0)
            u, _, vt = svd((map_centers - map_mean).T @ (truth_centers - truth_mean))
            fit_rotation = vt.T @ diag([1.0, 1.0, sign(det(vt.T @ u.T))]) @ u.T
            fit_translation = truth_mean - fit_rotation @ map_mean
            residuals = norm((fit_rotation @ map_centers.T).T + fit_translation - truth_centers, axis=1)
            metrics.metrics.prior_drift_residual_rms_m = float((residuals**2).mean() ** 0.5)
            metrics.metrics.prior_drift_residual_max_m = float(residuals.max())

    # Write the best reconstruction to disk in COLMAP format
    best_reconstruction.write_text(str(output_path))  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike

    # Write point cloud to disk in NPZ format
    point_cloud_point_count = len(best_reconstruction.points3D)
    point_cloud_positions = empty((point_cloud_point_count, 3), dtype=float32)
    point_cloud_colors = empty((point_cloud_point_count, 3), dtype=uint8)

    for point_cloud_point_index, point_cloud_point in enumerate(
        cast(ValuesView[Point3D], best_reconstruction.points3D.values())  # type: ignore
    ):
        point_cloud_positions[point_cloud_point_index] = point_cloud_point.xyz
        point_cloud_colors[point_cloud_point_index] = point_cloud_point.color

    point_cloud_npz_file_path = output_path / "points3D.npz"
    savez_compressed(str(point_cloud_npz_file_path), positions=point_cloud_positions, colors=point_cloud_colors)

    # Write frame poses to disk in NPZ format
    frame_count = len(best_reconstruction.frames)
    frame_positions = empty((frame_count, 3), dtype=float32)
    frame_orientations = empty((frame_count, 4), dtype=float32)

    for frame_index, frame in enumerate(cast(ValuesView[Frame], best_reconstruction.frames.values())):  # type: ignore
        # Convert from rig_from_world to world_from_rig
        rig_from_world = cast(Rigid3d, frame.rig_from_world)
        world_from_rig_rotation_matrix = rig_from_world.rotation.matrix().T
        world_from_rig_translation = -world_from_rig_rotation_matrix @ rig_from_world.translation

        frame_positions[frame_index] = world_from_rig_translation
        frame_orientations[frame_index] = Rotation.from_matrix(world_from_rig_rotation_matrix).as_quat()

    frame_poses_npz_file_path = output_path / "frame_poses.npz"
    savez_compressed(str(frame_poses_npz_file_path), positions=frame_positions, orientations=frame_orientations)

    return best_reconstruction


def _registered_frames(
    rigs: dict[str, Rig],
    colmap_image_ids: dict[str, int],
    reconstruction: Reconstruction,
) -> Iterator[tuple[int, FramePose, Rigid3d]]:
    # Multi-camera rigs (e.g. ZED stereo) share one Frame per rig+frame, so any registered
    # image of any camera in that frame yields the Frame's rig_from_world.
    for rig_id, rig in rigs.items():
        for frame_id, transform in rig.frame_poses.items():
            for camera_id in rig.cameras.keys():
                image_id = colmap_image_ids[f"{rig_id}/{camera_id}/{frame_id}.jpg"]
                if image_id in reconstruction.images:
                    rig_from_world = cast(Rigid3d, cast(Frame, reconstruction.images[image_id].frame).rig_from_world)  # type: ignore
                    yield int(frame_id), transform, rig_from_world
                    break


class _IncrementalMappingProgress:
    # Tracks per-image registration count across COLMAP's multi-model retries.
    # Each new model attempt begins with the seed pair (count = 2); attempt index
    # bumps when initial_image_pair fires after a previous attempt has registered.

    def __init__(self, publisher: ReconstructionPublisher) -> None:
        self._publisher = publisher
        self._registered = 0
        self._attempt = 1

    def on_initial_image_pair(self) -> None:
        if self._registered > 0:
            self._attempt += 1
        self._registered = 2
        self._publisher.on_progress(self._registered, self._attempt)

    def on_next_image(self) -> None:
        self._registered += 1
        self._publisher.on_progress(self._registered, self._attempt)
