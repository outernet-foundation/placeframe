import numpy as np
import pytest
from localize.build_metrics import _compute_inlier_coverage  # noqa: PLC2701 — testing private helper


class TestComputeInlierCoverage:
    def test_fewer_than_3_inliers_returns_zero(self):
        points = np.array([[10.0, 20.0], [30.0, 40.0]])
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_single_point_returns_zero(self):
        points = np.array([[50.0, 50.0]])
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_empty_returns_zero(self):
        points = np.empty((0, 2))
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_collinear_points_returns_zero(self):
        points = np.array([[0.0, 0.0], [50.0, 0.0], [100.0, 0.0]])
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_quarter_coverage(self):
        points = np.array([[0.0, 0.0], [50.0, 0.0], [50.0, 50.0], [0.0, 50.0]])
        assert _compute_inlier_coverage(points, 100, 100) == pytest.approx(0.25, abs=1e-6)

    def test_full_coverage(self):
        points = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
        assert _compute_inlier_coverage(points, 100, 100) == pytest.approx(1.0, abs=1e-6)

    def test_triangle_area(self):
        # Right triangle: area = 0.5 * 100 * 100 = 5000, image = 200*200 = 40000
        points = np.array([[0.0, 0.0], [100.0, 0.0], [0.0, 100.0]])
        assert _compute_inlier_coverage(points, 200, 200) == pytest.approx(5000.0 / 40000.0, abs=1e-6)

    def test_nonsquare_image(self):
        # Full-width half-height rectangle in a 200x100 image
        points = np.array([[0.0, 0.0], [200.0, 0.0], [200.0, 50.0], [0.0, 50.0]])
        # Hull area = 200*50 = 10000, image area = 200*100 = 20000
        assert _compute_inlier_coverage(points, 200, 100) == pytest.approx(0.5, abs=1e-6)
