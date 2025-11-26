from __future__ import annotations

from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, List, Optional, Sequence, cast

from core.reconstruction_metrics import ReconstructionMetrics
from numpy import asarray, float64, percentile
from numpy.linalg import norm
from numpy.typing import NDArray
from pycolmap import Database, ImageMap, Point3D, Point3DMap, Reconstruction
from pycolmap import Image as ColmapImage

UINT64_MAX = 18446744073709551615  # sentinel used by Point2D.point3D_id default


class MetricsBuilder:
    def __init__(self):
        self.metrics = ReconstructionMetrics()

    def build_verified_matches_metrics(self, db_path: Path, pairs: list[tuple[str, ...]]) -> None:
        database = Database.open(str(db_path))
        # Map image name -> image_id (help Pyright with explicit types)
        all_images: list[ColmapImage] = database.read_all_images()
        name_to_id: dict[str, int] = {img.name: img.image_id for img in all_images}

        def _parse_name(name: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
            # Expected: "<rig_id>/<camera_id>/<frame_id>.jpg"
            try:
                rig_id, cam_id, rest = name.split("/", 2)
                frame_id = rest.rsplit(".", 1)[0]
                return rig_id, cam_id, frame_id
            except Exception:
                return None, None, None

        total: int = 0
        verified: int = 0
        inliers_all: List[int] = []

        st_total = st_verified = 0  # stereo: same frame, different sensors
        st_inliers: List[int] = []

        ss_total = ss_verified = 0  # same sensor across frames
        ss_inliers: List[int] = []

        cs_total = cs_verified = 0  # cross sensor across frames
        cs_inliers: List[int] = []

        for a, b in pairs:
            total += 1
            ida: int = name_to_id[a]
            idb: int = name_to_id[b]
            tvg: Any = database.read_two_view_geometry(ida, idb)

            ninl: int = len(getattr(tvg, "inlier_matches", []))
            ok: bool = ninl > 0 and int(getattr(tvg, "config", 0)) != 0

            if ok:
                verified += 1
                inliers_all.append(ninl)

            ra, ca, fa = _parse_name(a)
            rb, cb, fb = _parse_name(b)
            if None not in (ra, ca, fa, rb, cb, fb) and ra == rb:
                if fa == fb and ca != cb:
                    st_total += 1
                    if ok:
                        st_verified += 1
                        st_inliers.append(ninl)
                elif ca == cb and fa != fb:
                    ss_total += 1
                    if ok:
                        ss_verified += 1
                        ss_inliers.append(ninl)
                elif ca != cb and fa != fb:
                    cs_total += 1
                    if ok:
                        cs_verified += 1
                        cs_inliers.append(ninl)

        self.metrics.all_verified_matches = verified
        self.metrics.all_verified_match_rate = (100.0 * verified / total) if total else 0.0
        self.metrics.all_verified_match_inliers_mean = mean(inliers_all) if inliers_all else 0.0
        self.metrics.all_verified_match_inliers_median = median(inliers_all) if inliers_all else 0.0
        self.metrics.stereo_verified_matches = st_verified
        self.metrics.stereo_verified_match_rate = (100.0 * st_verified / st_total) if st_total else 0.0
        self.metrics.stereo_verified_match_inliers_mean = mean(st_inliers) if st_inliers else 0.0
        self.metrics.stereo_verified_match_inliers_median = median(st_inliers) if st_inliers else 0.0
        self.metrics.same_sensor_verified_matches = ss_verified
        self.metrics.same_sensor_verified_match_rate = (100.0 * ss_verified / ss_total) if ss_total else 0.0
        self.metrics.same_sensor_verified_match_inliers_mean = mean(ss_inliers) if ss_inliers else 0.0
        self.metrics.same_sensor_verified_match_inliers_median = median(ss_inliers) if ss_inliers else 0.0
        self.metrics.cross_sensor_verified_matches = cs_verified
        self.metrics.cross_sensor_verified_match_rate = (100.0 * cs_verified / cs_total) if cs_total else 0.0
        self.metrics.cross_sensor_verified_match_inliers_mean = mean(cs_inliers) if cs_inliers else 0.0
        self.metrics.cross_sensor_verified_match_inliers_median = median(cs_inliers) if cs_inliers else 0.0

        database.close()

    def build_reconstruction_metrics(self, best: Reconstruction) -> None:
        points3d: Point3DMap = best.points3D
        points3d_values: Iterable[Point3D] = cast(Iterable[Point3D], points3d.values())  # type: ignore
        reconstruction_images: ImageMap = best.images
        reconstruction_image_values: Iterable[ColmapImage] = cast(
            Iterable[ColmapImage],
            reconstruction_images.values(),  # type: ignore
        )
        track_lengths = [len(p.track.elements) for p in points3d_values]

        reproject_errors: List[float] = []
        for image in reconstruction_image_values:
            for point2d in image.points2D:
                if point2d.point3D_id == UINT64_MAX or point2d.point3D_id not in points3d:
                    continue
                projection: Optional[NDArray[float64]] = image.project_point(points3d[point2d.point3D_id].xyz)
                if projection is None:
                    continue
                reproject_errors.append(
                    float(
                        norm(
                            asarray(projection, dtype=float64).reshape(2)
                            - asarray(point2d.xy, dtype=float64).reshape(2)
                        )
                    )
                )

        self.metrics.total_images = len(reconstruction_images)
        self.metrics.registered_images = best.num_reg_images()
        self.metrics.registration_rate = float(best.num_reg_images() / len(reconstruction_images) * 100.0)
        self.metrics.num_3d_points = len(points3d)
        self.metrics.track_length_50th_percentile = _percentile([float(L) for L in track_lengths], 50.0)
        self.metrics.percent_tracks_with_length_greater_than_or_equal_to_3 = float(
            sum(1 for L in track_lengths if L >= 3) / float(len(track_lengths)) * 100.0
        )

        def q(x: float, eps: float = 1e-9) -> float:
            return float(round(x / eps) * eps)

        self.metrics.reprojection_pixel_error_50th_percentile = q(_percentile(reproject_errors, 50.0))
        self.metrics.reprojection_pixel_error_90th_percentile = q(_percentile(reproject_errors, 90.0))


def _percentile(xs: Sequence[float], q: float):
    arr = asarray(xs, dtype=float64)
    if arr.size == 0:
        raise ValueError("Cannot compute percentile of empty array")
    return float(percentile(arr, q))
