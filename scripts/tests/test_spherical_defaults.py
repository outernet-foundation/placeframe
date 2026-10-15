"""Spherical captures get their own reconstruction defaults; an explicit choice always wins."""

from __future__ import annotations

from core.reconstruction_options import ReconstructionOptions

from scripts.howard_test import SPHERICAL_RECONSTRUCTION_DEFAULTS, with_spherical_defaults


def test_defaults_fill_an_empty_request_and_validate() -> None:
    merged = with_spherical_defaults({})
    options = ReconstructionOptions.model_validate(merged)
    assert options.spherical_layout == "dodecahedron"
    assert options.spherical_view_fov_deg == 80.0
    assert options.spherical_sequential_views == "neighbouring"
    assert options.max_keypoints_per_image == 5000
    assert options.pair_vio_em_max_rotation_disagreement_deg == 180.0
    assert options.pair_vio_em_max_translation_direction_deg == 180.0


def test_field_of_view_follows_a_chosen_layout() -> None:
    assert with_spherical_defaults({"spherical_layout": "cube"})["spherical_view_fov_deg"] == 120.0
    assert with_spherical_defaults({"spherical_layout": "tetrahedron"})["spherical_view_fov_deg"] == 150.0


def test_explicit_values_win() -> None:
    chosen = {"spherical_layout": "cube", "spherical_view_fov_deg": 110.0, "max_keypoints_per_image": 2500}
    merged = with_spherical_defaults(chosen)
    assert {k: merged[k] for k in chosen} == chosen
    assert merged["spherical_sequential_views"] == SPHERICAL_RECONSTRUCTION_DEFAULTS["spherical_sequential_views"]
