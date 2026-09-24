"""The projection has to be exactly what the camera parameters claim."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233

from panorama import projection


def equirectangular_with_dots(width: int, height: int, longitudes: range) -> np.ndarray:
    """Equator dots at known longitudes, to measure where a view puts them."""
    pano = np.zeros((height, width, 3), np.uint8)
    for lon in longitudes:
        x = int((lon / 360 + 0.5) * width)
        pano[height // 2 - 3 : height // 2 + 4, x - 3 : x + 4] = 255
    return pano


def test_view_is_equidistant() -> None:
    """A dot theta degrees off axis must land at radius f * theta, the claim made
    by the OPENCV_FISHEYE parameters with zero distortion."""
    width, height, size, fov = 3600, 1800, 800, 150.0
    pano = equirectangular_with_dots(width, height, range(-70, 71, 10))
    tables = projection.view_map(width, height, projection.View("t", 0.0, 0.0), size, fov)
    view = projection.render(pano, tables)

    focal, _, centre, *_ = tables.camera_params
    band = view[int(centre) - 2 : int(centre) + 3, :, 0].max(axis=0)
    columns = np.nonzero(band > 80)[0]
    clusters: list[list[int]] = []
    for x in columns:
        if clusters and x - clusters[-1][-1] <= 8:
            clusters[-1].append(int(x))
        else:
            clusters.append([int(x)])

    measured = sorted(np.degrees((np.mean(c) - centre) / focal) for c in clusters)
    expected = [d for d in range(-70, 71, 10)]
    assert len(measured) == len(expected)
    assert np.allclose(measured, expected, atol=0.2)


def test_tetrahedron_axes_are_109_degrees_apart() -> None:
    axes = np.array([projection.pano_from_cam(v) @ np.array([0.0, 0.0, 1.0]) for v in projection.TETRAHEDRON])
    angles = np.degrees(np.arccos(np.clip(axes @ axes.T, -1, 1)))
    pairs = angles[np.triu_indices(len(axes), 1)]
    assert np.allclose(pairs, 109.4712, atol=1e-3)


def test_tetrahedron_covers_the_sphere() -> None:
    """No direction is further from its nearest view axis than half the minimum
    field of view, so views at MIN_TETRA_FOV_DEG or wider leave no hole."""
    count = 200_000
    i = np.arange(count) + 0.5
    phi = np.arccos(1 - 2 * i / count)
    theta = np.pi * (1 + 5**0.5) * i
    directions = np.stack([np.sin(phi) * np.cos(theta), np.cos(phi), np.sin(phi) * np.sin(theta)], axis=1)

    axes = np.array([projection.pano_from_cam(v) @ np.array([0.0, 0.0, 1.0]) for v in projection.TETRAHEDRON])
    worst = np.degrees(np.arccos(np.clip(directions @ axes.T, -1, 1))).min(axis=1).max()
    assert worst <= projection.MIN_TETRA_FOV_DEG / 2
    assert worst == pytest.approx(projection.MIN_TETRA_FOV_DEG / 2, abs=0.1)

    # and the default field of view covers every sampled direction with margin
    covered = np.degrees(np.arccos(np.clip(directions @ axes.T, -1, 1))).min(axis=1) <= 150.0 / 2
    assert covered.all()


def test_view_axes_point_where_asked() -> None:
    for view in projection.TETRAHEDRON:
        axis = projection.pano_from_cam(view) @ np.array([0.0, 0.0, 1.0])
        assert np.degrees(np.arctan2(axis[0], axis[2])) % 360 == pytest.approx(view.yaw_deg % 360, abs=1e-6)
        assert np.degrees(np.arcsin(axis[1])) == pytest.approx(view.pitch_deg, abs=1e-6)


def test_rig_rotations_relate_the_view_axes() -> None:
    """cam_from_rig maps the rig frame (the reference view's camera frame) into
    each view, so the reference axis carried into a view sits 109.47 degrees off
    that view's own axis. The rotation's own magnitude also folds in roll, which
    is why the axes, not the angle of the rotation, are what is checked."""
    reference = projection.TETRAHEDRON[0]
    assert np.allclose(projection.cam_from_rig(reference, reference), np.eye(3))

    forward = np.array([0.0, 0.0, 1.0])
    for view in projection.TETRAHEDRON[1:]:
        reference_axis_in_view = projection.cam_from_rig(view, reference) @ forward
        angle = np.degrees(np.arccos(np.clip(reference_axis_in_view @ forward, -1, 1)))
        assert angle == pytest.approx(109.4712, abs=1e-3)


def sphere_directions(count: int = 200_000) -> NDArray[np.float64]:
    """Near-uniform directions on the sphere, in panorama axes (y up)."""
    i = np.arange(count) + 0.5
    phi = np.arccos(1 - 2 * i / count)
    theta = np.pi * (1 + 5**0.5) * i
    return np.stack([np.sin(phi) * np.cos(theta), np.cos(phi), np.sin(phi) * np.sin(theta)], axis=1)


def off_axis_degrees(views: tuple[projection.View, ...], directions: NDArray[np.float64]) -> NDArray[np.float64]:
    """For each direction, the angle to the nearest view axis."""
    axes = np.array([projection.pano_from_cam(v) @ np.array([0.0, 0.0, 1.0]) for v in views])
    return np.degrees(np.arccos(np.clip(directions @ axes.T, -1, 1))).min(axis=1)


def test_hexring_axes_are_lifted_out_of_one_plane() -> None:
    """The alternating tilt is the whole reason this layout can reach a pole.
    Six coplanar axes would each be 90 degrees from the zenith, which no fisheye
    model can represent -- so the tilt, not the view count, is load-bearing."""
    pitches = [v.pitch_deg for v in projection.HEXRING]
    assert pitches == [15.0, -15.0, 15.0, -15.0, 15.0, -15.0]

    directions = sphere_directions()
    zenith_gap = off_axis_degrees(projection.HEXRING, np.array([[0.0, 1.0, 0.0]]))[0]
    assert zenith_gap == pytest.approx(75.0, abs=0.1)  # 90 minus the tilt

    coplanar = tuple(projection.View(v.name, v.yaw_deg, 0.0) for v in projection.HEXRING)
    assert off_axis_degrees(coplanar, np.array([[0.0, 1.0, 0.0]]))[0] == pytest.approx(90.0, abs=1e-6)
    assert off_axis_degrees(projection.HEXRING, directions).max() == pytest.approx(75.0, abs=0.2)


def test_hexring_trades_coverage_for_views_that_look_level() -> None:
    """Outdoors the sky carries nothing to match on, so what matters is the band
    a level camera sees. The narrow fields this layout is for keep most of that
    band while staying far closer to rectilinear than a 150-degree view."""
    directions = sphere_directions()
    worst = off_axis_degrees(projection.HEXRING, directions)
    elevation = np.degrees(np.arcsin(directions[:, 1]))
    useful = (elevation <= 45) & (elevation >= -70)

    assert (worst <= 150.0 / 2).all()  # still covers the whole sphere when asked to
    assert (worst[useful] <= 120.0 / 2).mean() > 0.98
    assert (worst[useful] <= 100.0 / 2).mean() > 0.89
