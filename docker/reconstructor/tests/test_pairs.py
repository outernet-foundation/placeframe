from __future__ import annotations

from reconstructor.pairs import PairSource, generate_image_pairs
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
