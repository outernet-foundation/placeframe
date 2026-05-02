from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, NewType, cast

from torch import Tensor

from .lightglue import (
    Descriptors,
    DescriptorsArrays,
    Keypoints,
    KeypointsArrays,
    MatchIndices,
    lightglue_match,
    lightglue_match_tensors,
)
from .tensor_types import TT

RetrievalDim = NewType("RetrievalDim", int)
NumKeypoints = NewType("NumKeypoints", int)
LocalDescDim = NewType("LocalDescDim", int)

LocalFeatureOutput = tuple[TT[NumKeypoints, Literal[2]], TT[NumKeypoints, LocalDescDim]]


def make_global_descriptor_extractor(model: Any) -> Callable[[Tensor], TT[RetrievalDim]]:
    def extract(image: Tensor) -> TT[RetrievalDim]:
        return cast(TT[RetrievalDim], model({"image": image})["global_descriptor"][0])

    return extract


def make_local_feature_extractor(model: Any) -> Callable[[Tensor], LocalFeatureOutput]:
    def extract(image: Tensor) -> LocalFeatureOutput:
        output = model({"image": image})
        return (
            cast(TT[NumKeypoints, Literal[2]], output["keypoints"][0]),
            cast(TT[NumKeypoints, LocalDescDim], output["descriptors"][0]),
        )

    return extract


def make_local_feature_matcher_for_tensors(
    model: Any, device: str
) -> Callable[
    [list[tuple[str, str]], Keypoints, Descriptors, dict[str, tuple[int, int]], int],
    MatchIndices,
]:
    def match(
        pairs: list[tuple[str, str]],
        keypoints: Keypoints,
        descriptors: Descriptors,
        sizes: dict[str, tuple[int, int]],
        batch_size: int,
    ) -> MatchIndices:
        return lightglue_match_tensors(model, pairs, keypoints, descriptors, sizes, batch_size, device)

    return match


def make_local_feature_matcher_for_arrays(
    model: Any, device: str
) -> Callable[
    [list[tuple[str, str]], KeypointsArrays, DescriptorsArrays, dict[str, tuple[int, int]], int],
    MatchIndices,
]:
    def match(
        pairs: list[tuple[str, str]],
        keypoints: KeypointsArrays,
        descriptors: DescriptorsArrays,
        sizes: dict[str, tuple[int, int]],
        batch_size: int,
    ) -> MatchIndices:
        return lightglue_match(model, pairs, keypoints, descriptors, sizes, batch_size, device)

    return match
