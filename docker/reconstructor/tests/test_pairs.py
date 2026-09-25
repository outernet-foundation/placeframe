from __future__ import annotations

from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.capture_session_manifest import RigCameraConfig, RigConfig
from core.transform import Float3, Float4
from reconstructor.pairs import Pair, PairSource, generate_image_pairs
from reconstructor.rig import Rig
from .test_spherical import build, spherical_rig


def test_every_pair_names_an_image_the_pipeline_extracted() -> None:
    """A spherical rig's cameras are views derived from one manifest camera, so
    they all carry that camera's id; only the rig's own key names the folder the
    rendered images are in. Naming pairs from the config id instead put the
    un-rendered sphere in the match list, and matching died on the first lookup.
    """
    rig = build(spherical_rig())
    extracted = {f"rig0/{camera_id}/{frame_id}.jpg" for camera_id in rig.cameras for frame_id in rig.frame_poses}

    pairs = generate_image_pairs(
        {"rig0": rig}, {}, sequential_window_m=3.0, retrieval_neighbors=0, retrieval_min_score=0.0
    )

    assert pairs
    for pair in pairs:
        assert pair.image_a in extracted, pair.image_a
        assert pair.image_b in extracted, pair.image_b


def test_views_of_one_sphere_are_not_paired_with_each_other() -> None:
    """They share an optical centre, so a pair of them has no baseline."""
    rig = build(spherical_rig())

    pairs = generate_image_pairs(
        {"rig0": rig}, {}, sequential_window_m=3.0, retrieval_neighbors=0, retrieval_min_score=0.0
    )

    assert not [pair for pair in pairs if pair.source == PairSource.INTRA_FRAME_STEREO]
    for pair in pairs:
        assert pair.image_a.split("/")[2] != pair.image_b.split("/")[2], pair


def two_rigs_apart(separation_m: float) -> dict[str, Rig]:
    """Two single-camera rigs whose frames sit `separation_m` apart, frame for frame."""
    rigs: dict[str, Rig] = {}
    for index, (rig_id, offset) in enumerate((("rig0", 0.0), ("rig1", separation_m))):
        frames = "timestamp_ms,tx,ty,tz,qx,qy,qz,qw\n" + "\n".join(
            f"{1000 + step},{offset},0,{float(step)},0,0,0,1" for step in range(4)
        )
        rigs[rig_id] = Rig(
            RigConfig(
                id=rig_id,
                cameras=[
                    RigCameraConfig(
                        id="camera0",
                        ref_sensor=True,
                        rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
                        translation=Float3(x=0.0, y=0.0, z=0.0),
                        camera_config=PinholeCameraConfig(
                            width=640, height=480, orientation="TOP_LEFT", fx=500.0, fy=500.0, cx=320.0, cy=240.0
                        ),
                    )
                ],
            ),
            AxisConvention.OPENCV,
            frames,
        )
        _ = index
    return rigs


def cross_rig(pairs: list[Pair]) -> list[Pair]:
    return [p for p in pairs if p.image_a.split("/")[0] != p.image_b.split("/")[0]]


def test_nothing_crosses_rigs_until_asked() -> None:
    """Sequential pairing is per-rig and retrieval needs descriptors, so two captures sitting on
    top of each other still produce no cross-rig pair on their own."""
    pairs = generate_image_pairs(
        two_rigs_apart(0.0), {}, sequential_window_m=3.0, retrieval_neighbors=0, retrieval_min_score=0.0
    )
    assert cross_rig(pairs) == []


def test_frames_of_different_rigs_pair_when_the_priors_put_them_together() -> None:
    rigs = two_rigs_apart(1.0)
    pairs = generate_image_pairs(
        rigs,
        {},
        sequential_window_m=3.0,
        retrieval_neighbors=0,
        retrieval_min_score=0.0,
        cross_rig_pair_distance_m=2.0,
    )
    crossing = cross_rig(pairs)
    assert crossing, "rigs 1 m apart should pair within a 2 m window"
    assert all(p.source == PairSource.CROSS_RIG_SPATIAL for p in crossing)


def test_rigs_beyond_the_window_are_left_alone() -> None:
    """The window is the whole gate: it is what keeps a placement that puts two captures nowhere
    near each other from inventing pairs between them."""
    pairs = generate_image_pairs(
        two_rigs_apart(50.0),
        {},
        sequential_window_m=3.0,
        retrieval_neighbors=0,
        retrieval_min_score=0.0,
        cross_rig_pair_distance_m=2.0,
    )
    assert cross_rig(pairs) == []
