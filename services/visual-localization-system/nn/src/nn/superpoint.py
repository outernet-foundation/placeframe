from typing import Any, Mapping

from SuperGluePretrainedNetwork.models import superpoint
from torch.nn import Module


class SuperPoint(Module):
    def __init__(self, weights: str, max_keypoints: int | None) -> None:
        super().__init__()  # type: ignore
        self.net = superpoint.SuperPoint({
            "weights": weights,
            "nms_radius": 4,
            "keypoint_threshold": 0.005,
            "max_keypoints": max_keypoints or -1,
            "remove_borders": 4,
        })

    def forward(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.net(data)


def load_superpoint(weights: str, max_keypoints: int | None, device: str):
    return SuperPoint(weights, max_keypoints).to(device).eval()
