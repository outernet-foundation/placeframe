from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from placeframe_api_client import ReconstructionStatus

from numpy import asarray, diag, eye, float64, intp, sign, stack, uint32
from numpy.linalg import det, norm, svd
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Camera as ColmapCamera
from pycolmap import (
    Database,
    Frame,
    IncrementalMapper,
    IncrementalMapperOptions,
    IncrementalPipeline,
    IncrementalPipelineOptions,
    PosePrior,
    PosePriorCoordinateSystem,
    Reconstruction,
    ReconstructionManager,
    Rigid3d,
    SensorType,
    TwoViewGeometry,
    align_reconstruction_to_orig_rig_scales,
    data_t,
    sensor_t,
)
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, estimate_two_view_geometry  # noqa: PLC2701 — no public API

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .pairs import PairSource, flatten_pairs
from .progress_publisher import ReconstructionPublisher
from .rig import Rig, image_name

# Mirror of the C++ IncrementalMapperImpl::kMinNumInitialRegTrials constant. After this
# many failures while the reconstruction is still below min_model_size the loop falls
# back to trying a different initial pair instead of grinding through every candidate.
INITIAL_REGISTRATION_TRIALS_LIMIT = 30

# Mapper options halved once per relaxation round when the primary attempt fails to
# register enough images. Upstream halves each option once per round, in order.
INIT_RELAXATION_TARGETS: tuple[Literal["init_min_num_inliers", "init_min_tri_angle"], ...] = (
    "init_min_num_inliers",
    "init_min_tri_angle",
)
INIT_RELAXATION_ROUNDS = 2

# Sim3 has 7 degrees of freedom and needs 3 non-collinear point correspondences for a
# unique fit. The check requires at least 3 more correspondences beyond that to give the
# residual statistic any signal — below this count the local-Umeyama prediction is
# mathematically vacuous and the registration is accepted by default.
VIO_CHECK_MIN_NEIGHBORS = 6

# Cap on the number of nearest-in-time already-registered VIO neighbors used to fit the
# local Umeyama. Larger windows leak secular VIO drift into the fit; the cap keeps the
# fit anchored to the local trajectory segment.
VIO_CHECK_WINDOW = 10

# Disagreement (metres) between the local-Umeyama-predicted recon position and the recon
# position COLMAP just assigned, above which the registration is rejected. `inf` accepts
# every registration while still running the check and logging its disagreement.
VIO_CHECK_MAX_DISAGREEMENT_M = float("inf")

# Lower bound on the squared VIO-neighbor spread. Below this the local Sim3 fit cannot
# determine rotation or scale (all neighbors at the same VIO position), so the check is
# structurally vacuous and the frame is accepted.
VIO_CHECK_MIN_VIO_SPREAD_M2 = 1.0e-6


@dataclass(frozen=True)
class VioFrameData:
    timestamp_ns: int
    position: NDArray[float64]


@dataclass(frozen=True)
class VioCheckResult:
    passed: bool
    disagreement_m: float | None
    neighbor_count: int


def run_colmap_pipeline_with_vio_check(
    database_path: Path,
    image_path: Path,
    sfm_output_path: Path,
    options: OptionsBuilder,
    metrics: MetricsBuilder,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
    pairs_by_source: dict[PairSource, list[tuple[str, str]]],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    publisher: ReconstructionPublisher,
) -> dict[int, Reconstruction]:
    if not image_path.exists():
        raise FileNotFoundError(f"Image path does not exist: {image_path}")
    sfm_output_path.mkdir(exist_ok=True, parents=True)

    with Database.open(str(database_path)) as database:  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike
        reconstruction_manager = _seed_and_reconstruct(
            database,
            image_path,
            options,
            metrics,
            rigs,
            keypoints,
            pairs_by_source,
            match_indices,
            publisher,
        )

    reconstruction_manager.write(str(sfm_output_path))  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike
    return {index: reconstruction_manager.get(index) for index in range(reconstruction_manager.size())}


def _seed_and_reconstruct(
    database: Database,
    image_path: Path,
    options: OptionsBuilder,
    metrics: MetricsBuilder,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
    pairs_by_source: dict[PairSource, list[tuple[str, str]]],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    publisher: ReconstructionPublisher,
) -> ReconstructionManager:
    pairs = flatten_pairs(pairs_by_source)
    position_covariance = (options.pose_prior_position_sigma_m() ** 2) * eye(3, dtype=float64)

    colmap_image_ids: dict[str, int] = {}
    image_cameras: dict[str, ColmapCamera] = {}
    vio_data_by_image_id: dict[int, VioFrameData] = {}
    reconstruction_manager = ReconstructionManager()

    for rig_id, rig in rigs.items():
        for camera_id, camera in rig.cameras.items():
            colmap_camera_id = database.write_camera(camera[1])

            for frame_id, transform in rig.frame_poses.items():
                name = image_name(rig_id, camera_id, frame_id)
                colmap_image_id = database.write_image(pycolmapImage(name=name, camera_id=colmap_camera_id))
                colmap_image_ids[name] = colmap_image_id
                image_cameras[name] = camera[1]
                database.write_keypoints(colmap_image_id, keypoints[name])

                # PosePrior is the BA-side consumer of per-frame VIO positions. Multi-camera captures
                # carry positions in frames.csv so pair-generation can use them as a spatial signal,
                # but BA must not see them: VIO drift baked into a quadratic loss tears global
                # geometry apart on revisits (the original priors-off motivation). Stereo baseline
                # anchors metric scale instead.
                if camera[0].ref_sensor and not options.is_multi_camera_capture and transform.translation is not None:
                    database.write_pose_prior(
                        PosePrior(
                            position=transform.translation.reshape(3, 1),
                            position_covariance=position_covariance,
                            coordinate_system=PosePriorCoordinateSystem.CARTESIAN,
                            corr_data_id=data_t(
                                sensor_t(SensorType.CAMERA, colmap_camera_id),
                                colmap_image_id,
                            ),
                        ),
                    )

                # Skipping frames without a translation leaves them outside the VIO check entirely:
                # gravity-only frames have no metric position for the local-Umeyama prediction.
                if transform.translation is not None:
                    vio_data_by_image_id[colmap_image_id] = VioFrameData(
                        timestamp_ns=int(frame_id),
                        position=transform.translation,
                    )

    apply_rig_config([rig.colmap_rig_config for rig in rigs.values()], database)

    # COLMAP assigns rig_t IDs at apply_rig_config time; harvest them so the incremental BA
    # loop can pin every rig's sensor_from_rig transform.
    pipeline_options = options.incremental_pipeline_options({rig.rig_id for rig in database.read_all_rigs()})
    pipeline_options.image_path = image_path

    for a, b in pairs:
        database.write_matches(
            colmap_image_ids[a],
            colmap_image_ids[b],
            stack(match_indices[(a, b)], axis=1).astype(uint32, copy=False),
        )

    # Per-pair so each completion ticks progress; sqlite writes stay on the main thread.
    publisher.set_phase(ReconstructionStatus.VERIFYING_GEOMETRY, len(pairs))
    with ThreadPoolExecutor() as pool:
        future_to_pair: dict[Future[TwoViewGeometry], tuple[str, str]] = {}
        for source, source_pairs in pairs_by_source.items():
            verification_options = (
                options.retrieval_two_view_geometry_options()
                if source == PairSource.RETRIEVAL
                else options.two_view_geometry_options()
            )
            for a, b in source_pairs:
                future_to_pair[
                    pool.submit(
                        estimate_two_view_geometry,
                        image_cameras[a],
                        keypoints[a],
                        image_cameras[b],
                        keypoints[b],
                        stack(match_indices[(a, b)], axis=1).astype(uint32, copy=False),
                        verification_options,
                    )
                ] = (a, b)
        for completed, future in enumerate(as_completed(future_to_pair), start=1):
            a, b = future_to_pair[future]
            database.write_two_view_geometry(colmap_image_ids[a], colmap_image_ids[b], future.result())
            publisher.on_progress(completed)

    metrics.build_verified_matches_metrics(database, pairs)

    # Phase total is the candidate image count — an upper bound, since COLMAP may drop images that
    # fail to register or get filtered after bundle adjustment.
    publisher.set_phase(ReconstructionStatus.RECONSTRUCTING, len(colmap_image_ids))

    controller = IncrementalPipeline(pipeline_options, database, reconstruction_manager)
    database_cache = controller.database_cache
    if database_cache.num_images() == 0:
        raise RuntimeError("No images survived two-view geometry verification")

    mapper = IncrementalMapper(database_cache)
    mapper_options = pipeline_options.get_mapper()
    skipped_image_ids: set[int] = set()

    # label=None is the primary attempt: no stop-check, no relaxation. Each later entry
    # halves one init threshold.
    for label in (None, *(INIT_RELAXATION_TARGETS * INIT_RELAXATION_ROUNDS)):
        if label is not None:
            if mapper.num_total_reg_images() == database_cache.num_images():
                break
            print(f"[colmap_pipeline] Relaxing {label}")
            if label == "init_min_num_inliers":
                mapper_options.init_min_num_inliers = int(mapper_options.init_min_num_inliers / 2)
            else:
                mapper_options.init_min_tri_angle /= 2
            mapper.reset_initialization_stats()

        for _ in range(pipeline_options.init_num_trials):
            reconstruction_index = reconstruction_manager.add()
            reconstruction = reconstruction_manager.get(reconstruction_index)
            mapper.begin_reconstruction(reconstruction)

            initial_pair_data = mapper.find_initial_image_pair(
                mapper_options, pipeline_options.init_image_id1, pipeline_options.init_image_id2
            )
            if initial_pair_data is None:
                mapper.end_reconstruction(True)
                reconstruction_manager.delete(reconstruction_index)
                break
            initial_pair = initial_pair_data[0]

            mapper.register_initial_image_pair(mapper_options, *initial_pair, initial_pair_data[1])

            triangulation_options = pipeline_options.get_triangulation()
            triangulation_options.min_angle = mapper_options.init_min_tri_angle
            for image_id in initial_pair:
                frame = reconstruction.images[image_id].frame
                assert frame is not None
                for data_id in frame.image_ids:
                    mapper.triangulate_image(triangulation_options, data_id.id)

            mapper.adjust_global_bundle(mapper_options, pipeline_options.get_global_bundle_adjustment())
            reconstruction.normalize()
            mapper.filter_points(mapper_options)
            mapper.filter_frames(mapper_options)

            if reconstruction.num_reg_frames() == 0 or reconstruction.num_points3D() == 0:
                mapper.end_reconstruction(True)
                reconstruction_manager.delete(reconstruction_index)
                continue

            publisher.on_initial_pair()

            previous_global_refinement_registered_frame_count = reconstruction.num_reg_frames()
            previous_global_refinement_point_count = reconstruction.num_points3D()
            register_next_succeeded = True
            previous_register_next_succeeded = True

            while True:
                if not (register_next_succeeded or previous_register_next_succeeded):
                    break

                previous_register_next_succeeded = register_next_succeeded
                register_next_succeeded = False
                next_image_id: int | None = None

                for structure_less in (False, True):
                    next_images = [
                        i
                        for i in mapper.find_next_images(mapper_options, structure_less=structure_less)
                        if i not in skipped_image_ids
                    ]
                    register = (
                        mapper.register_next_structure_less_image if structure_less else mapper.register_next_image
                    )

                    for registration_trial, candidate_image_id in enumerate(next_images):
                        register_next_succeeded = register(mapper_options, candidate_image_id)

                        if register_next_succeeded:
                            check_result = vio_check(vio_data_by_image_id, reconstruction, candidate_image_id)
                            print(
                                f"[vio_check] image_id={candidate_image_id} structure_less={structure_less} "
                                f"neighbors={check_result.neighbor_count} disagreement_m="
                                f"{'vacuous' if check_result.disagreement_m is None else f'{check_result.disagreement_m:.6f}'} "
                                f"passed={check_result.passed}"
                            )
                            if check_result.passed:
                                next_image_id = candidate_image_id
                                break
                            # Skip-list every image attached to this frame — multi-camera rigs share one
                            # frame across all cameras, and deregister_frame removes them all together.
                            # Adding only candidate_image_id would let find_next_images re-suggest the
                            # other stereo image at the same (rejected) pose on the next iteration.
                            rejected_frame = reconstruction.images[candidate_image_id].frame
                            assert rejected_frame is not None
                            skipped_image_ids.update(data_id.id for data_id in rejected_frame.image_ids)
                            reconstruction.deregister_frame(rejected_frame.frame_id)
                            register_next_succeeded = False
                            continue

                        # If the initial pair fails to grow the model for a while, abort and try
                        # a different initial pair instead of grinding through every candidate.
                        if (
                            registration_trial >= INITIAL_REGISTRATION_TRIALS_LIMIT
                            and reconstruction.num_reg_images() < pipeline_options.min_model_size
                        ):
                            break

                    if register_next_succeeded:
                        break

                if register_next_succeeded and next_image_id is not None:
                    frame = reconstruction.images[next_image_id].frame
                    assert frame is not None
                    for data_id in frame.image_ids:
                        mapper.triangulate_image(pipeline_options.get_triangulation(), data_id.id)
                    mapper.iterative_local_refinement(
                        pipeline_options.ba_local_max_refinements,
                        pipeline_options.ba_local_max_refinement_change,
                        mapper_options,
                        pipeline_options.get_local_bundle_adjustment(),
                        pipeline_options.get_triangulation(),
                        next_image_id,
                    )
                    if controller.check_run_global_refinement(
                        reconstruction,
                        previous_global_refinement_registered_frame_count,
                        previous_global_refinement_point_count,
                    ):
                        _iterative_global_refinement(pipeline_options, mapper_options, mapper)
                        previous_global_refinement_point_count = reconstruction.num_points3D()
                        previous_global_refinement_registered_frame_count = reconstruction.num_reg_frames()
                    publisher.on_next_image()

                if mapper.num_shared_reg_images() >= int(pipeline_options.max_model_overlap):
                    break

                if (not register_next_succeeded) and previous_register_next_succeeded:
                    _iterative_global_refinement(pipeline_options, mapper_options, mapper)

            # Final global BA when the last incremental refinement was local-only.
            if reconstruction.num_reg_frames() > 0 and not (
                reconstruction.num_reg_frames() == previous_global_refinement_registered_frame_count
                and reconstruction.num_points3D() == previous_global_refinement_point_count
            ):
                _iterative_global_refinement(pipeline_options, mapper_options, mapper)

            registered_image_count = reconstruction.num_reg_images()
            if (
                pipeline_options.multiple_models
                and reconstruction_manager.size() > 1
                and registered_image_count < pipeline_options.min_model_size
            ) or registered_image_count == 0:
                mapper.end_reconstruction(True)
                reconstruction_manager.delete(reconstruction_index)
            else:
                reconstruction.update_point_3d_errors()
                mapper.end_reconstruction(False)
                align_reconstruction_to_orig_rig_scales(database_cache.rigs, reconstruction)
            if (
                not pipeline_options.multiple_models
                or reconstruction_manager.size() >= pipeline_options.max_num_models
                or mapper.num_total_reg_images() >= database_cache.num_images() - 1
            ):
                return reconstruction_manager

    return reconstruction_manager


def vio_check(
    vio_by_image_id: dict[int, VioFrameData],
    reconstruction: Reconstruction,
    image_id: int,
) -> VioCheckResult:
    query_data = vio_by_image_id.get(image_id)
    if query_data is None:
        return VioCheckResult(passed=True, disagreement_m=None, neighbor_count=0)
    if image_id not in reconstruction.images:
        return VioCheckResult(passed=True, disagreement_m=None, neighbor_count=0)
    query_frame = reconstruction.images[image_id].frame
    if query_frame is None:
        return VioCheckResult(passed=True, disagreement_m=None, neighbor_count=0)
    query_reconstruction_position = _frame_position(query_frame)
    if query_reconstruction_position is None:
        return VioCheckResult(passed=True, disagreement_m=None, neighbor_count=0)

    # Dedup multi-camera neighbors by frame_id — both stereo images of one frame share
    # the same rig_from_world and the same VIO position, so each frame contributes a
    # single correspondence regardless of camera count.
    seen_frame_ids: set[int] = set()
    candidates: list[tuple[int, VioFrameData, NDArray[float64]]] = []
    for candidate_image_id in reconstruction.reg_image_ids():
        if candidate_image_id == image_id:
            continue
        candidate_data = vio_by_image_id.get(candidate_image_id)
        if candidate_data is None:
            continue
        candidate_frame = reconstruction.images[candidate_image_id].frame
        if candidate_frame is None:
            continue
        if candidate_frame.frame_id in seen_frame_ids:
            continue
        reconstruction_position = _frame_position(candidate_frame)
        if reconstruction_position is None:
            continue
        seen_frame_ids.add(candidate_frame.frame_id)
        candidates.append((
            abs(candidate_data.timestamp_ns - query_data.timestamp_ns),
            candidate_data,
            reconstruction_position,
        ))

    candidates.sort(key=lambda candidate: candidate[0])
    neighbors = candidates[:VIO_CHECK_WINDOW]
    if len(neighbors) < VIO_CHECK_MIN_NEIGHBORS:
        return VioCheckResult(passed=True, disagreement_m=None, neighbor_count=len(neighbors))

    reconstruction_points = asarray(
        [reconstruction_position for _, _, reconstruction_position in neighbors], dtype=float64
    )
    vio_points = asarray([neighbor_data.position for _, neighbor_data, _ in neighbors], dtype=float64)

    vio_mean = vio_points.mean(axis=0)
    reconstruction_mean = reconstruction_points.mean(axis=0)
    vio_centered = vio_points - vio_mean

    vio_spread_squared = float((vio_centered**2).sum())
    if vio_spread_squared < VIO_CHECK_MIN_VIO_SPREAD_M2:
        return VioCheckResult(passed=True, disagreement_m=None, neighbor_count=len(neighbors))

    # Umeyama Sim3 (vio -> recon). Covariance built as X̃^T Ỹ.
    u, singular_values, vt = svd(vio_centered.T @ (reconstruction_points - reconstruction_mean))
    sign_diagonal = asarray([1.0, 1.0, float(sign(det(vt.T @ u.T)))], dtype=float64)
    rotation = vt.T @ diag(sign_diagonal) @ u.T
    scale = float((singular_values * sign_diagonal).sum() / vio_spread_squared)

    disagreement_m = float(
        norm(
            scale * (rotation @ query_data.position)
            + reconstruction_mean
            - scale * (rotation @ vio_mean)
            - query_reconstruction_position
        )
    )

    return VioCheckResult(
        passed=disagreement_m <= VIO_CHECK_MAX_DISAGREEMENT_M,
        disagreement_m=disagreement_m,
        neighbor_count=len(neighbors),
    )


def _iterative_global_refinement(
    options: IncrementalPipelineOptions,
    mapper_options: IncrementalMapperOptions,
    mapper: IncrementalMapper,
) -> None:
    mapper.iterative_global_refinement(
        options.ba_global_max_refinements,
        options.ba_global_max_refinement_change,
        mapper_options,
        options.get_global_bundle_adjustment(),
        options.get_triangulation(),
    )
    mapper.filter_frames(mapper_options)


def _frame_position(frame: Frame) -> NDArray[float64] | None:
    rig_from_world: Rigid3d | None = frame.rig_from_world
    if rig_from_world is None:
        return None
    return -rig_from_world.rotation.matrix().T @ rig_from_world.translation
