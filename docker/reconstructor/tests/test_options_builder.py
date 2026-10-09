from core.reconstruction_options import ReconstructionOptions
from reconstructor.options_builder import OptionsBuilder


def test_rendered_views_keep_their_exact_intrinsics() -> None:
    """A spherical frame's views are rendered with known intrinsics; BA must not touch them."""
    builder = OptionsBuilder(ReconstructionOptions(), is_multi_camera_capture=False, has_rendered_views=True)
    incremental = builder.incremental_pipeline_options(constant_rigs=set())
    assert not incremental.ba_refine_focal_length
    assert not incremental.ba_refine_extra_params
    final = builder.final_bundle_adjustment_options()
    assert not final.refine_focal_length
    assert not final.refine_extra_params


def test_real_cameras_are_still_refined() -> None:
    builder = OptionsBuilder(ReconstructionOptions(), is_multi_camera_capture=False)
    incremental = builder.incremental_pipeline_options(constant_rigs=set())
    assert incremental.ba_refine_focal_length
    assert incremental.ba_refine_extra_params
