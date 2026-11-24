from __future__ import annotations

import sqlite3
from io import BytesIO
from json import dumps, loads
from math import acos, pi
from pathlib import Path
from shutil import rmtree
from typing import Any, Iterator, ValuesView, cast

from numpy import (
    array,
    asarray,
    concatenate,
    diag,
    empty,
    eye,
    float32,
    float64,
    full,
    int32,
    int64,
    intp,
    isnan,
    load,
    median,
    nan,
    savez_compressed,
    sign,
    stack,
    uint8,
    uint32,
)
from numpy.linalg import det, norm, svd
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from placeframe_lease_server_client import ReconstructionStatus
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
    Rotation3d,
    SensorType,
    Sim3d,
    TwoViewGeometry,
    TwoViewGeometryConfiguration,
    data_t,
    sensor_t,
)
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, geometric_verification  # noqa: PLC2701 — no public API  # pyright: ignore[reportUnknownVariableType] — upstream stub uses unparameterized os.PathLike

# from pycolmap._core import bundle_adjustment  # uncomment with the final-BA call below
from pycolmap._core import incremental_mapping  # noqa: PLC2701 — no public API  # pyright: ignore[reportUnknownVariableType] — upstream stub uses unparameterized os.PathLike
from scipy.spatial.transform import Rotation

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder, PairVioEssentialMatrixOptions
from .pairs import Pair, PairSource
from .progress_publisher import ReconstructionPublisher
from .rig import FramePose, Rig
from .shards import SHARD_PAIRS_FILE, TWO_VIEW_GEOMETRIES_FILE, VERIFICATION_SHARD_PREFIX
from .uploader import ArtifactUploader

COLMAP_DB_FILE = "database.db"
COLMAP_SFM_DIRECTORY = "sfm_model"
VERIFY_SHARD_MAX_PAIRS = 4096


def run_colmap_reconstruction(
    root_path: Path,
    output_path: Path,
    images_path: Path,
    options: OptionsBuilder,
    metrics: MetricsBuilder,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
    pairs: list[Pair],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    publisher: ReconstructionPublisher,
    uploader: ArtifactUploader,
    valid_verification_indexes: set[int],
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
    database = open_colmap_database(colmap_db_path)
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

                if camera[0].ref_sensor:
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

    database.close()

    # Run the kernel once per shard with only that shard's match rows present, because the
    # stock verifier never skips a pair that already has a two-view geometry
    verification_shards = partition_verification_shards(pairs)
    publisher.set_phase(ReconstructionStatus.VERIFYING_GEOMETRY, total=len(verification_shards))
    for shard_index, shard_pairs in enumerate(verification_shards):
        publisher.raise_if_lease_lost()
        if shard_index in valid_verification_indexes:
            database = open_colmap_database(colmap_db_path)
            replay_verification_shard(root_path, shard_index, database, colmap_image_ids)
            database.close()
            publisher.on_progress(shard_index + 1)
            continue

        database = open_colmap_database(colmap_db_path)
        write_match_rows(database, colmap_image_ids, shard_pairs, match_indices)
        database.close()
        geometric_verification(
            database_path=str(colmap_db_path),
            verifier_options=GeometricVerifierOptions(rig_verification=True),
            two_view_geometry_options=options.two_view_geometry_options(),
        )
        database = open_colmap_database(colmap_db_path)
        shard_files = harvest_verification_shard_files(database, colmap_image_ids, shard_pairs)
        uploader.put_shard(
            f"{VERIFICATION_SHARD_PREFIX}/{shard_index:05d}",
            shard_files,
            {"shard_index": shard_index, "shard_count": len(verification_shards)},
        )
        database.close()
        delete_match_rows(colmap_db_path)
        publisher.on_progress(shard_index + 1)

    # Restore every match row so the archived database.db keeps raw matches beside the two-view geometries
    database = open_colmap_database(colmap_db_path)
    write_match_rows(database, colmap_image_ids, pairs, match_indices)
    database.close()

    _apply_vio_em_check(colmap_db_path, colmap_image_ids, pairs, rigs, options.pair_vio_essential_matrix_options())

    # Compute and store verified matches metrics
    metrics.build_verified_matches_metrics(colmap_db_path, [(pair.image_a, pair.image_b) for pair in pairs])

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

    # Disabled: final standalone BA with rig refinement re-enabled. The incremental loop above ran
    # with rig refinement off (every global BA refining rig poses scales N times); this final pass
    # was meant to let sensor_from_rig settle against the converged geometry, but on large captures
    # it ran for >30 min with no progress callback and silently exceeded the lease timeout.
    # bundle_adjustment(best_reconstruction, options.final_bundle_adjustment_options())

    metrics.build_reconstruction_metrics(best_reconstruction)

    registered = sorted(_registered_frames(rigs, colmap_image_ids, best_reconstruction), key=lambda entry: entry[0])
    if not registered:
        raise RuntimeError("Could not find anchor frame in best reconstruction")

    gravity_samples_in_recon_world = [
        rig_from_world.rotation.matrix().T @ transform.gravity_in_rig_local
        for _frame_id, transform, rig_from_world in registered
    ]
    gravity_stack = stack(gravity_samples_in_recon_world)
    gravity_in_recon_world_estimate = median(gravity_stack, axis=0)
    gravity_in_recon_world_estimate /= norm(gravity_in_recon_world_estimate)
    alignment_rotation, _ = Rotation.align_vectors([[0.0, 1.0, 0.0]], [gravity_in_recon_world_estimate])
    rotation_align = alignment_rotation.as_matrix()
    metrics.metrics.gravity_aligned_in_map_frame = True
    metrics.metrics.gravity_sample_count = len(gravity_samples_in_recon_world)

    _first_frame_id, _first_transform, first_rig_from_world = registered[0]
    first_camera_position = -first_rig_from_world.rotation.matrix().T @ first_rig_from_world.translation
    translation_align = -rotation_align @ first_camera_position
    best_reconstruction.transform(Sim3d(concatenate([rotation_align, translation_align.reshape(3, 1)], axis=1)))

    # Rigid Umeyama best-fit of map centers to VIO position priors. Fit is not applied — the
    # residual is the prior-drift diagnostic surfaced for calibration-corpus filtering.
    if not options.is_multi_camera_capture:
        truth_centers_list: list[NDArray[float64]] = [
            transform.translation.astype(float64) for _frame_id, transform, _ in registered
        ]
        map_centers_list: list[NDArray[float64]] = [
            -rig_from_world.rotation.matrix().T @ rig_from_world.translation
            for _frame_id, _transform, rig_from_world in registered
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


def partition_verification_shards(pairs: list[Pair]) -> list[list[Pair]]:
    # Pack frame-pair groups into shards of at most VERIFY_SHARD_MAX_PAIRS pairs without ever
    # splitting a group, because the kernel's rig pass aggregates every camera pair of a frame pair
    groups: dict[tuple[tuple[str, str], tuple[str, str]], list[Pair]] = {}
    for pair in pairs:
        frame_a = _image_frame_key(pair.image_a)
        frame_b = _image_frame_key(pair.image_b)
        key = (frame_a, frame_b) if frame_a <= frame_b else (frame_b, frame_a)
        groups.setdefault(key, []).append(pair)

    shards: list[list[Pair]] = []
    shard: list[Pair] = []
    shard_pair_count = 0
    for group in groups.values():
        if shard and shard_pair_count + len(group) > VERIFY_SHARD_MAX_PAIRS:
            shards.append(shard)
            shard = []
            shard_pair_count = 0
        shard.extend(group)
        shard_pair_count += len(group)
    if shard:
        shards.append(shard)
    return shards


def _image_frame_key(image_name: str) -> tuple[str, str]:
    rig_id, _camera_id, frame_file = image_name.split("/", 2)
    return rig_id, frame_file.rsplit(".", 1)[0]


def replay_verification_shard(
    root_path: Path,
    shard_index: int,
    database: Database,
    colmap_image_ids: dict[str, int],
) -> None:
    # Insert each harvested geometry rather than update, because the database was rebuilt from
    # scratch and update is a no-op on a missing row
    shard_directory = root_path / VERIFICATION_SHARD_PREFIX / f"{shard_index:05d}"
    shard_pairs: list[list[str]] = loads((shard_directory / SHARD_PAIRS_FILE).read_text())
    with load(shard_directory / TWO_VIEW_GEOMETRIES_FILE) as data:
        configs = asarray(data["config"], dtype=int32)
        qvecs = asarray(data["qvec"], dtype=float64)
        tvecs = asarray(data["tvec"], dtype=float64)
        e_matrices = asarray(data["E"], dtype=float64)
        f_matrices = asarray(data["F"], dtype=float64)
        h_matrices = asarray(data["H"], dtype=float64)
        inlier_matches = asarray(data["inlier_matches"], dtype=uint32).reshape(-1, 2)
        inlier_offsets = asarray(data["inlier_offsets"], dtype=int64)
        for row_index, (image_a, image_b) in enumerate(shard_pairs):
            # Leave each NaN field unset, because the pose and each of E/F/H are independently optional
            qvec = qvecs[row_index]
            tvec = tvecs[row_index]
            e_matrix = e_matrices[row_index]
            f_matrix = f_matrices[row_index]
            h_matrix = h_matrices[row_index]
            tvg = TwoViewGeometry()
            tvg.config = TwoViewGeometryConfiguration(int(configs[row_index]))
            if not isnan(qvec).any():
                tvg.cam2_from_cam1 = Rigid3d(rotation=Rotation3d(qvec), translation=tvec)
            if not isnan(e_matrix).any():
                tvg.E = e_matrix
            if not isnan(f_matrix).any():
                tvg.F = f_matrix
            if not isnan(h_matrix).any():
                tvg.H = h_matrix
            tvg.inlier_matches = inlier_matches[int(inlier_offsets[row_index]) : int(inlier_offsets[row_index + 1])]
            database.write_two_view_geometry(colmap_image_ids[image_a], colmap_image_ids[image_b], tvg)


def write_match_rows(
    database: Database,
    colmap_image_ids: dict[str, int],
    pairs: list[Pair],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
) -> None:
    for pair in pairs:
        (image_a_indices, image_b_indices) = match_indices[(pair.image_a, pair.image_b)]
        database.write_matches(
            colmap_image_ids[pair.image_a],
            colmap_image_ids[pair.image_b],
            stack((image_a_indices, image_b_indices), axis=1).astype(uint32, copy=False),
        )


def harvest_verification_shard_files(
    database: Database,
    colmap_image_ids: dict[str, int],
    shard_pairs: list[Pair],
) -> dict[str, bytes]:
    pair_count = len(shard_pairs)
    configs = empty(pair_count, dtype=int32)
    qvecs = full((pair_count, 4), nan)
    tvecs = full((pair_count, 3), nan)
    e_matrices = full((pair_count, 3, 3), nan)
    f_matrices = full((pair_count, 3, 3), nan)
    h_matrices = full((pair_count, 3, 3), nan)
    inlier_parts: list[NDArray[uint32]] = []
    inlier_offsets = [0]
    for row_index, pair in enumerate(shard_pairs):
        tvg = database.read_two_view_geometry(colmap_image_ids[pair.image_a], colmap_image_ids[pair.image_b])
        configs[row_index] = int(tvg.config)
        if tvg.cam2_from_cam1 is not None:
            qvecs[row_index] = asarray(tvg.cam2_from_cam1.rotation.quat, dtype=float64).reshape(4)
            tvecs[row_index] = asarray(tvg.cam2_from_cam1.translation, dtype=float64).reshape(3)
        if tvg.E is not None:
            e_matrices[row_index] = asarray(tvg.E, dtype=float64).reshape(3, 3)
        if tvg.F is not None:
            f_matrices[row_index] = asarray(tvg.F, dtype=float64).reshape(3, 3)
        if tvg.H is not None:
            h_matrices[row_index] = asarray(tvg.H, dtype=float64).reshape(3, 3)
        inliers = asarray(tvg.inlier_matches, dtype=uint32).reshape(-1, 2)  # pyright: ignore[reportUnknownMemberType] — upstream stub leaves the inlier_matches row dimension unknown
        inlier_parts.append(inliers)
        inlier_offsets.append(inlier_offsets[-1] + len(inliers))

    buffer = BytesIO()
    savez_compressed(
        buffer,
        config=configs,
        qvec=qvecs,
        tvec=tvecs,
        E=e_matrices,
        F=f_matrices,
        H=h_matrices,
        inlier_matches=concatenate(inlier_parts),
        inlier_offsets=array(inlier_offsets, dtype=int64),
    )
    return {
        TWO_VIEW_GEOMETRIES_FILE: buffer.getvalue(),
        SHARD_PAIRS_FILE: dumps([[pair.image_a, pair.image_b] for pair in shard_pairs]).encode("utf-8"),
    }


def delete_match_rows(colmap_db_path: Path) -> None:
    # Clear the matches table between kernel calls, because the match shards are the record
    connection = sqlite3.connect(str(colmap_db_path))
    try:
        connection.execute("DELETE FROM matches")
        connection.commit()
    finally:
        connection.close()


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


def _apply_vio_em_check(
    colmap_db_path: Path,
    colmap_image_ids: dict[str, int],
    pairs: list[Pair],
    rigs: dict[str, Rig],
    vio_em_options: PairVioEssentialMatrixOptions,
) -> None:
    rotation_threshold_rad = vio_em_options.max_rotation_disagreement_deg * pi / 180.0
    translation_threshold_rad = vio_em_options.max_translation_direction_deg * pi / 180.0
    if vio_em_options.max_rotation_disagreement_deg <= 0 and vio_em_options.max_translation_direction_deg <= 0:
        return

    sequential_pairs = [pair for pair in pairs if pair.source == PairSource.SEQUENTIAL]

    cam_from_rig_by_image_prefix: dict[str, Rigid3d] = {
        camera.image_prefix: camera.cam_from_rig
        for rig in rigs.values()
        for camera in rig.colmap_rig_config.cameras
        if camera.cam_from_rig is not None
    }
    world_from_rig_by_rig_and_frame: dict[tuple[str, str], Rigid3d] = {
        (rig_id, frame_id): Rigid3d(rotation=pose.rotation, translation=pose.translation)
        for rig_id, rig in rigs.items()
        for frame_id, pose in rig.frame_poses.items()
    }

    database = open_colmap_database(colmap_db_path)
    checked = 0
    skipped_no_vio = 0
    rejected_rotation = 0
    rejected_translation = 0
    empty_tvg = TwoViewGeometry()
    for pair in sequential_pairs:
        a, b = pair.image_a, pair.image_b
        tvg: TwoViewGeometry = database.read_two_view_geometry(colmap_image_ids[a], colmap_image_ids[b])
        if tvg.config == TwoViewGeometryConfiguration.UNDEFINED:
            continue
        if tvg.cam2_from_cam1 is None:
            continue

        rig_a, _, frame_a_dot = a.split("/", 2)
        rig_b, _, frame_b_dot = b.split("/", 2)
        frame_a = frame_a_dot.rsplit(".", 1)[0]
        frame_b = frame_b_dot.rsplit(".", 1)[0]
        cam_a_from_rig = cam_from_rig_by_image_prefix.get(a.rsplit("/", 1)[0] + "/")
        cam_b_from_rig = cam_from_rig_by_image_prefix.get(b.rsplit("/", 1)[0] + "/")
        world_from_rig_a = world_from_rig_by_rig_and_frame.get((rig_a, frame_a))
        world_from_rig_b = world_from_rig_by_rig_and_frame.get((rig_b, frame_b))
        if cam_a_from_rig is None or cam_b_from_rig is None or world_from_rig_a is None or world_from_rig_b is None:
            skipped_no_vio += 1
            continue

        recon_translation = asarray(tvg.cam2_from_cam1.translation, dtype=float64).reshape(3)
        recon_baseline = float(norm(recon_translation))

        vio_cam2_from_cam1 = cam_b_from_rig * world_from_rig_b.inverse() * world_from_rig_a * cam_a_from_rig.inverse()
        checked += 1

        rotation_bad = (
            vio_em_options.max_rotation_disagreement_deg > 0
            and tvg.cam2_from_cam1.rotation.angle_to(vio_cam2_from_cam1.rotation) > rotation_threshold_rad
        )
        translation_bad = False
        if vio_em_options.max_translation_direction_deg > 0:
            vio_translation = asarray(vio_cam2_from_cam1.translation, dtype=float64).reshape(3)
            vio_baseline = float(norm(vio_translation))
            if vio_baseline >= vio_em_options.min_baseline_m:
                cosine = float((recon_translation @ vio_translation) / (recon_baseline * vio_baseline))
                cosine = max(-1.0, min(1.0, cosine))
                translation_angle = acos(cosine)
                translation_bad = translation_angle > translation_threshold_rad

        if rotation_bad:
            rejected_rotation += 1
        if translation_bad:
            rejected_translation += 1
        if rotation_bad or translation_bad:
            database.update_two_view_geometry(colmap_image_ids[a], colmap_image_ids[b], empty_tvg)

    database.close()
    print(
        f"[vio_em_check] checked={checked} rejected_rotation={rejected_rotation} "
        f"rejected_translation={rejected_translation} skipped_no_vio={skipped_no_vio}"
    )


def open_colmap_database(colmap_db_path: Path) -> Database:
    return Database.open(str(colmap_db_path))  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike


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
