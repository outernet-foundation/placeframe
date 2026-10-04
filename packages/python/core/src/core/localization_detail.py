"""Per-query diagnostic detail for a single localization attempt.

The localizer's normal answer is a pose plus aggregate metrics, which says whether a
query localized but not why. This module carries the intermediate state the pipeline
already computes and would otherwise discard: which database images retrieval chose,
how each one matched, and where every correspondence landed in both images.

It is opt-in (`detail=True` on the request) because the correspondence arrays are far
larger than the pose they explain -- a twelve-candidate query carries a few thousand
point pairs -- and because it is only ever read by a human diagnosing one frame.

Correspondences are parallel arrays rather than a list of objects: the same numbers in
roughly a third of the JSON, and already in the shape a renderer wants to iterate.
"""

from __future__ import annotations

from pydantic import BaseModel

from .camera_config import PinholeCameraConfig
from .localization_metrics import LocalizationMetrics

# `status` values for a raw LightGlue match. A match only becomes a 2D-3D correspondence
# if the database keypoint carries a triangulated point, so NO_POINT3D records matches the
# matcher liked but PnP never saw -- the difference between "did not match" and "matched
# something the map does not know in 3D", which aggregate metrics cannot distinguish.
MATCH_NO_POINT3D = 0
MATCH_OUTLIER = 1
MATCH_INLIER = 2


class PairDetail(BaseModel):
    """One retrieved database image and how the query matched against it."""

    rank: int
    image_id: int
    name: str
    width: int
    height: int

    retrieval_score: float
    num_keypoints: int
    num_matches: int
    num_correspondences: int
    num_inliers: int
    inlier_ratio: float
    reprojection_error_median: float | None

    # Where this database image's camera sits relative to the estimated query pose.
    # Both are None when the query produced no pose to measure against.
    distance_m: float | None
    view_angle_deg: float | None

    # Parallel arrays over this pair's raw matches, in the matcher's own order. Typed as
    # list[list[float]] rather than list[tuple[float, float]] deliberately: a fixed-length
    # tuple serializes to JSON-Schema `prefixItems`, which openapi-generator rejects outright
    # ("attribute components.schemas.PairDetail.prefixItems is unexpected") -- and it exits 0
    # while doing so, so the client generator treats the empty result as success.
    query_xy: list[list[float]]
    database_xy: list[list[float]]
    status: list[int]
    reprojection_error_px: list[float]


class GateDetail(BaseModel):
    """The calibrated confidence gate, and whether this query cleared it."""

    loose_min: float
    tight_min: float
    passed: bool


class LocalizationDetail(BaseModel):
    reconstruction_id: str

    # The intrinsics the pipeline actually used, not the ones the caller believes it sent.
    # A query localizing badly because its focal length is wrong looks identical to one
    # failing for any other reason until you can read this back.
    camera: PinholeCameraConfig
    retrieval_top_k: int
    ransac_threshold: float
    num_query_keypoints: int

    timings_ms: dict[str, float]
    pairs: list[PairDetail]

    # Absent when the attempt failed before metrics could be built.
    metrics: LocalizationMetrics | None = None
    gate: GateDetail | None = None
    failure_reason: str | None = None
