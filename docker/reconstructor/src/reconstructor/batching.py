"""How many pairs LightGlue matches per forward pass.

Peak GPU memory for one pass is set by the assignment matrices LightGlue builds
at the end: about six float32 tensors of (batch, keypoints, keypoints), since
every image in a batch is padded to the longest. That is batch x keypoints^2
floats, so the memory does not depend on how many pairs there are in total,
only on how many are matched at once and how many keypoints each may carry.

At the historical setting -- 4 pairs of 2500 keypoints -- the stage needs well
under 1 GiB. Raising the per-image cap to 8000 at the same batch size asked for
about 6.5 GiB and died on an 8 GiB card alongside the loaded models. The batch
size therefore follows the cap: the product batch x cap^2 is held at or below
the budget the historical setting established, so any cap matches within the
memory the default always used. A larger cap simply matches fewer pairs at once.

The batch size is not a ReconstructionOptions field. Batching changes how the
matching is computed, never what it produces, and every option is part of the
blob that decides whether an existing reconstruction can be reused
(scripts/fit_calibration.py). It can instead be fixed through the
LIGHTGLUE_BATCH_SIZE environment variable, for a card with more or less memory
than the budget assumes.
"""

from __future__ import annotations

# Pairs per pass that the matching stage was tuned at, and the per-image keypoint
# cap it was tuned for (ReconstructionOptions.max_keypoints_per_image's default).
REFERENCE_BATCH_SIZE = 4
REFERENCE_MAX_KEYPOINTS = 2500

# Upper bound on batch x max_keypoints^2 for one pass, in keypoint pairs.
LIGHTGLUE_BATCH_KEYPOINT_BUDGET = REFERENCE_BATCH_SIZE * REFERENCE_MAX_KEYPOINTS**2

# Environment variable that fixes the batch size regardless of the keypoint cap.
# Unset or empty means the automatic rule above.
LIGHTGLUE_BATCH_SIZE_ENV = "LIGHTGLUE_BATCH_SIZE"


def lightglue_batch_size(max_keypoints: int, override: str | None = None) -> int:
    """Pairs per LightGlue pass for images carrying up to `max_keypoints` each.

    `override` is the raw LIGHTGLUE_BATCH_SIZE environment value; a positive
    integer wins over the automatic rule, anything empty defers to it.
    """
    if override is not None and override.strip():
        fixed = int(override)
        if fixed < 1:
            raise ValueError(f"{LIGHTGLUE_BATCH_SIZE_ENV} must be a positive integer, got {override!r}")
        return fixed
    if max_keypoints < 1:
        raise ValueError(f"max_keypoints must be positive, got {max_keypoints}")
    return max(1, LIGHTGLUE_BATCH_KEYPOINT_BUDGET // (max_keypoints * max_keypoints))


__all__ = [
    "LIGHTGLUE_BATCH_KEYPOINT_BUDGET",
    "LIGHTGLUE_BATCH_SIZE_ENV",
    "REFERENCE_BATCH_SIZE",
    "REFERENCE_MAX_KEYPOINTS",
    "lightglue_batch_size",
]
