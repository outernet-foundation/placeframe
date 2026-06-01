from __future__ import annotations

from math import ceil
from typing import NewType

from PIL import Image as PILImage
from torch import Tensor, arange, einsum

from .image_preprocess import LOCAL_FEATURE_RESIZE_SHORTER_SIDE

NumImages = NewType("NumImages", int)
MaxTiles = NewType("MaxTiles", int)
NumQueryTiles = NewType("NumQueryTiles", int)

# Tiling produces multiple framings per image so cross-aspect query/database pairs can still find a
# comparable match. CNN-backbone retrieval models also expect square inputs near their training shape.
RETRIEVAL_TILE_OVERLAP_FRACTION = 0.5


def tile_image(image: PILImage.Image) -> list[PILImage.Image]:
    side = LOCAL_FEATURE_RESIZE_SHORTER_SIDE
    width, height = image.width, image.height
    long_axis = max(width, height)
    if long_axis <= side:
        return [image]

    stride_target = max(1, round(side * (1.0 - RETRIEVAL_TILE_OVERLAP_FRACTION)))
    num_tiles = max(2, ceil((long_axis - side) / stride_target) + 1)
    step = (long_axis - side) / (num_tiles - 1)

    tiles: list[PILImage.Image] = []
    for tile_index in range(num_tiles):
        offset = round(tile_index * step)
        box = (offset, 0, offset + side, side) if width >= height else (0, offset, side, offset + side)
        tiles.append(image.crop(box))
    return tiles


def image_similarity_matrix(
    query_tiles: Tensor,
    query_tile_counts: Tensor,
    database_tiles: Tensor,
) -> Tensor:
    # Asymmetric all-pairs image similarity between two sets of tile-descriptor stacks.
    #
    # query_tiles: (Q, max_query_tiles, D) — L2-normalized per-tile DIR descriptors, zero-padded
    #   along the tile dimension so a single tensor can hold images with different tile counts.
    # query_tile_counts: (Q,) int — actual tile count per query image; the mean over query tiles
    #   averages only the real tiles.
    # database_tiles: (N, max_database_tiles, D) — same shape contract as query_tiles. Database
    #   padding is benign without an explicit mask: zero-padded tiles produce zero cosine with any
    #   query tile, and zero never beats a real positive cosine in the per-query-tile max for any
    #   plausible database image of the scene the query depicts.
    #
    # Returns (Q, N). Element [q, n] is the mean over q's real tiles of the max-over-n's-tiles of
    # pairwise tile cosine. "For each tile of q, how well does it appear somewhere in n, averaged
    # across q's tiles."
    #
    # Properties:
    #   - Every pairwise comparison is a true cosine between two L2-normalized DIR descriptors —
    #     the metric the model was trained for. No pooled-then-renormalized Frankenstein vectors.
    #   - Tolerates different tile counts on both sides without one-tile coincidences dominating:
    #     a single coincidental tile match lifts the mean by at most 1 / (query tile count).
    #   - Asymmetric: scores "how much of the query is represented in the database image," which
    #     is the right semantics for localization. For symmetric map-build pair ranking, callers
    #     average the two directions: 0.5 * (M + M.T) where M = image_similarity_matrix(D, c, D).
    pairwise_cosines = einsum("qid,njd->qnij", query_tiles, database_tiles)
    per_query_tile_best = pairwise_cosines.amax(dim=-1)

    max_query_tiles = query_tiles.size(1)
    query_tile_indices = arange(max_query_tiles, device=query_tiles.device)
    real_query_tile_mask = (query_tile_indices.unsqueeze(0) < query_tile_counts.unsqueeze(1)).to(
        per_query_tile_best.dtype
    )
    masked_best = per_query_tile_best * real_query_tile_mask.unsqueeze(1)
    return masked_best.sum(dim=-1) / query_tile_counts.unsqueeze(1).to(per_query_tile_best.dtype)
