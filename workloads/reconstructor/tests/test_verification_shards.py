from __future__ import annotations

import sqlite3
from json import loads
from pathlib import Path

import pytest
from numpy import allclose, arange, array, array_equal, eye, float32, float64, intp, stack, uint32
from numpy.random import default_rng
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from pycolmap import (
    GeometricVerifierOptions,
    RigConfig,
    RigConfigCamera,
    Rigid3d,
    Rotation3d,
    TwoViewGeometry,
    TwoViewGeometryConfiguration,
    TwoViewGeometryOptions,
)
from pycolmap import Camera as ColmapCamera
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, geometric_verification  # noqa: PLC2701 — no public API

from reconstructor import colmap as colmap_module
from reconstructor.colmap import (
    delete_match_rows,
    harvest_verification_shard_files,
    open_colmap_database,
    partition_verification_shards,
    replay_verification_shard,
    write_match_rows,
)
from reconstructor.pairs import Pair, PairSource
from reconstructor.shards import SHARD_PAIRS_FILE, TWO_VIEW_GEOMETRIES_FILE, VERIFICATION_SHARD_PREFIX

FOCAL_LENGTH = 320.0
PRINCIPAL_POINT_X = 320.0
PRINCIPAL_POINT_Y = 240.0
CAMERA_BASELINE_M = 0.12
POINT_COUNT = 40


def _pair(image_a: str, image_b: str) -> Pair:
    return Pair(image_a=image_a, image_b=image_b, source=PairSource.INTRA_FRAME_STEREO)


def _rig_pose(translation_x: float) -> Rigid3d:
    return Rigid3d(
        rotation=Rotation3d([0.0, 0.0, 0.0, 1.0]),
        translation=array([translation_x, 0.0, 0.0], dtype=float64).reshape(3, 1),
    )


def _build_verification_database(database_path: Path, keypoints_by_name: dict[str, NDArray[float32]]) -> dict[str, int]:
    database = open_colmap_database(database_path)
    camera = ColmapCamera(
        width=640,
        height=480,
        model="PINHOLE",
        params=[FOCAL_LENGTH, FOCAL_LENGTH, PRINCIPAL_POINT_X, PRINCIPAL_POINT_Y],
    )
    camera_id = database.write_camera(camera)
    image_ids = {
        image_name: database.write_image(pycolmapImage(name=image_name, camera_id=camera_id))
        for image_name in keypoints_by_name
    }
    for image_name, image_keypoints in keypoints_by_name.items():
        database.write_keypoints(image_ids[image_name], image_keypoints)
    apply_rig_config(
        [
            RigConfig(
                cameras=[
                    RigConfigCamera(image_prefix="rig0/cam0/", ref_sensor=True, cam_from_rig=_rig_pose(0.0)),
                    RigConfigCamera(
                        image_prefix="rig0/cam1/", ref_sensor=False, cam_from_rig=_rig_pose(CAMERA_BASELINE_M)
                    ),
                ]
            )
        ],
        database,
    )
    database.close()
    return image_ids


def _write_shard_files(root_path: Path, shard_index: int, shard_files: dict[str, bytes]) -> None:
    shard_directory = root_path / VERIFICATION_SHARD_PREFIX / f"{shard_index:05d}"
    shard_directory.mkdir(parents=True)
    for file_name, file_body in shard_files.items():
        (shard_directory / file_name).write_bytes(file_body)


def test_partition_never_splits_a_frame_pair_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(colmap_module, "VERIFY_SHARD_MAX_PAIRS", 3)
    frame_1000_to_1500 = _pair("rig0/cam0/1000.jpg", "rig0/cam0/1500.jpg")
    frame_1000_to_2000_first = _pair("rig0/cam0/1000.jpg", "rig0/cam0/2000.jpg")
    frame_1000_to_2000_second = _pair("rig0/cam0/1000.jpg", "rig0/cam1/2000.jpg")
    frame_1500_to_2000 = _pair("rig0/cam0/1500.jpg", "rig0/cam0/2000.jpg")
    frame_1000_to_2000_third = _pair("rig0/cam1/1000.jpg", "rig0/cam0/2000.jpg")
    pairs = [
        frame_1000_to_1500,
        frame_1000_to_2000_first,
        frame_1000_to_2000_second,
        frame_1500_to_2000,
        frame_1000_to_2000_third,
    ]

    shards = partition_verification_shards(pairs)

    assert shards == [
        [frame_1000_to_1500],
        [frame_1000_to_2000_first, frame_1000_to_2000_second, frame_1000_to_2000_third],
        [frame_1500_to_2000],
    ]


def test_partition_packs_groups_up_to_the_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(colmap_module, "VERIFY_SHARD_MAX_PAIRS", 4)
    first_group = [
        _pair("rig0/cam0/1000.jpg", "rig0/cam0/2000.jpg"),
        _pair("rig0/cam0/1000.jpg", "rig0/cam1/2000.jpg"),
    ]
    second_group = [
        _pair("rig0/cam0/3000.jpg", "rig0/cam0/4000.jpg"),
        _pair("rig0/cam0/3000.jpg", "rig0/cam1/4000.jpg"),
    ]
    third_group = [
        _pair("rig0/cam0/5000.jpg", "rig0/cam0/6000.jpg"),
        _pair("rig0/cam0/5000.jpg", "rig0/cam1/6000.jpg"),
    ]
    pairs = first_group + second_group + third_group

    shards = partition_verification_shards(pairs)

    assert shards == [first_group + second_group, third_group]


def test_partition_keeps_an_oversized_group_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(colmap_module, "VERIFY_SHARD_MAX_PAIRS", 5)
    pairs = [
        _pair("rig0/cam0/1000.jpg", "rig0/cam1/1000.jpg"),
        _pair("rig0/cam0/1000.jpg", "rig0/cam2/1000.jpg"),
        _pair("rig0/cam0/1000.jpg", "rig0/cam3/1000.jpg"),
        _pair("rig0/cam1/1000.jpg", "rig0/cam2/1000.jpg"),
        _pair("rig0/cam1/1000.jpg", "rig0/cam3/1000.jpg"),
        _pair("rig0/cam2/1000.jpg", "rig0/cam3/1000.jpg"),
    ]

    shards = partition_verification_shards(pairs)

    assert shards == [pairs]


def test_partition_is_deterministic_and_preserves_input_order() -> None:
    pairs = [
        _pair("rig0/cam0/1000.jpg", "rig0/cam1/1000.jpg"),
        _pair("rig0/cam0/1000.jpg", "rig0/cam0/2000.jpg"),
        _pair("rig0/cam0/1000.jpg", "rig0/cam1/2000.jpg"),
        _pair("rig0/cam0/3000.jpg", "rig0/cam1/3000.jpg"),
    ]

    first_partition = partition_verification_shards(pairs)
    second_partition = partition_verification_shards(pairs)

    assert first_partition == second_partition
    flattened = [pair for shard in first_partition for pair in shard]
    assert flattened == pairs


def test_choreography_write_kernel_harvest_delete_round_trips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(colmap_module, "VERIFY_SHARD_MAX_PAIRS", 1)
    generator = default_rng(7)
    frame_points = {
        "1000": generator.uniform([-0.5, -0.4, 1.5], [0.5, 0.4, 2.5], size=(POINT_COUNT, 3)),
        "1001": generator.uniform([-0.5, -0.4, 1.5], [0.5, 0.4, 2.5], size=(POINT_COUNT, 3)),
    }
    keypoints_by_name = {
        f"rig0/cam{camera_index}/{frame_id}.jpg": stack(
            (
                FOCAL_LENGTH * (points[:, 0] - camera_index * CAMERA_BASELINE_M) / points[:, 2] + PRINCIPAL_POINT_X,
                FOCAL_LENGTH * points[:, 1] / points[:, 2] + PRINCIPAL_POINT_Y,
            ),
            axis=1,
        ).astype(float32)
        for frame_id, points in frame_points.items()
        for camera_index in (0, 1)
    }
    database_path = tmp_path / "database.db"
    image_ids = _build_verification_database(database_path, keypoints_by_name)

    pairs = [
        _pair("rig0/cam0/1000.jpg", "rig0/cam1/1000.jpg"),
        _pair("rig0/cam0/1001.jpg", "rig0/cam1/1001.jpg"),
    ]
    full_match_indices = arange(POINT_COUNT, dtype=intp)
    match_indices = {(pair.image_a, pair.image_b): (full_match_indices, full_match_indices) for pair in pairs}
    shards = partition_verification_shards(pairs)
    assert len(shards) == 2

    for shard_index, shard_pairs in enumerate(shards):
        database = open_colmap_database(database_path)
        write_match_rows(database, image_ids, shard_pairs, match_indices)
        database.close()
        geometric_verification(
            database_path=str(database_path),
            verifier_options=GeometricVerifierOptions(rig_verification=True),
            two_view_geometry_options=TwoViewGeometryOptions(),
        )
        database = open_colmap_database(database_path)
        shard_files = harvest_verification_shard_files(database, image_ids, shard_pairs)
        database.close()
        delete_match_rows(database_path)
        _write_shard_files(tmp_path, shard_index, shard_files)

        connection = sqlite3.connect(str(database_path))
        try:
            row = connection.execute("SELECT COUNT(*) FROM matches").fetchone()
        finally:
            connection.close()

        assert int(row[0]) == 0
        assert set(shard_files) == {TWO_VIEW_GEOMETRIES_FILE, SHARD_PAIRS_FILE}
        assert loads(shard_files[SHARD_PAIRS_FILE].decode("utf-8")) == [
            [shard_pairs[0].image_a, shard_pairs[0].image_b]
        ]

    # Check the first shard's geometry survives the second shard's kernel call and match deletes
    database = open_colmap_database(database_path)
    original = database.read_two_view_geometry(image_ids[pairs[0].image_a], image_ids[pairs[0].image_b])
    database.close()

    # Assert only that the geometry is verified, because the kernel's config choice is scene-dependent
    assert original.config != TwoViewGeometryConfiguration.UNDEFINED
    assert len(original.inlier_matches) == POINT_COUNT

    replay_database_path = tmp_path / "replay.db"
    replay_image_ids = _build_verification_database(replay_database_path, keypoints_by_name)
    database = open_colmap_database(replay_database_path)
    replay_verification_shard(tmp_path, 0, database, replay_image_ids)
    replayed = database.read_two_view_geometry(replay_image_ids[pairs[0].image_a], replay_image_ids[pairs[0].image_b])
    database.close()

    assert replayed.config == original.config
    assert array_equal(replayed.inlier_matches, original.inlier_matches)
    assert (replayed.cam2_from_cam1 is None) == (original.cam2_from_cam1 is None)
    assert (replayed.E is None) == (original.E is None)
    if original.F is not None and replayed.F is not None:
        assert allclose(replayed.F, original.F)
    if original.H is not None and replayed.H is not None:
        assert allclose(replayed.H, original.H)


def test_harvest_and_replay_round_trips_a_fully_populated_geometry(tmp_path: Path) -> None:
    keypoints_by_name = {
        "rig0/cam0/1000.jpg": arange(10, dtype=float32).reshape(5, 2),
        "rig0/cam1/1000.jpg": arange(10, 20, dtype=float32).reshape(5, 2),
    }
    source_database_path = tmp_path / "source.db"
    image_ids = _build_verification_database(source_database_path, keypoints_by_name)

    stored = TwoViewGeometry()
    stored.config = TwoViewGeometryConfiguration.CALIBRATED
    stored.cam2_from_cam1 = Rigid3d(
        rotation=Rotation3d([0.1, 0.2, 0.3, 0.9]),
        translation=array([1.0, 2.0, 3.0], dtype=float64).reshape(3, 1),
    )
    stored.E = eye(3) * 2.0
    stored.F = eye(3) * 3.0
    stored.H = eye(3) * 4.0
    stored.inlier_matches = stack((arange(5, dtype=uint32), arange(5, 10, dtype=uint32)), axis=1)
    database = open_colmap_database(source_database_path)
    database.write_two_view_geometry(image_ids["rig0/cam0/1000.jpg"], image_ids["rig0/cam1/1000.jpg"], stored)
    database.close()

    shard_pair = _pair("rig0/cam0/1000.jpg", "rig0/cam1/1000.jpg")
    database = open_colmap_database(source_database_path)
    shard_files = harvest_verification_shard_files(database, image_ids, [shard_pair])
    database.close()
    _write_shard_files(tmp_path, 0, shard_files)

    replay_database_path = tmp_path / "replay.db"
    replay_image_ids = _build_verification_database(replay_database_path, keypoints_by_name)
    database = open_colmap_database(replay_database_path)
    replay_verification_shard(tmp_path, 0, database, replay_image_ids)
    replayed = database.read_two_view_geometry(
        replay_image_ids["rig0/cam0/1000.jpg"], replay_image_ids["rig0/cam1/1000.jpg"]
    )
    database.close()

    assert replayed.config == TwoViewGeometryConfiguration.CALIBRATED
    assert array_equal(replayed.inlier_matches, stored.inlier_matches)
    assert replayed.cam2_from_cam1 is not None
    assert allclose(replayed.cam2_from_cam1.translation, stored.cam2_from_cam1.translation)
    assert allclose(replayed.cam2_from_cam1.rotation.quat, stored.cam2_from_cam1.rotation.quat)
    assert replayed.E is not None and allclose(replayed.E, stored.E)
    assert replayed.F is not None and allclose(replayed.F, stored.F)
    assert replayed.H is not None and allclose(replayed.H, stored.H)
