import sys
from os import environ
from pathlib import Path
from typing import Any, Mapping, Protocol, cast

import torch
from lightglue import LightGlue, SuperPoint  # type: ignore
from numpy import float32
from numpy.typing import NDArray
from sklearn.decomposition import _pca  # type: ignore
from torch import Tensor, from_numpy  # type: ignore
from torch.hub import get_dir
from torch.nn import Module

environ["DB_ROOT"] = ""  # required by dirtorch
from dirtorch.extract_features import load_model  # type: ignore
from dirtorch.utils.common import whiten_features  # type: ignore

# From Hierarchical-Localization:
#
# The DIR model checkpoints (pickle files) include sklearn.decomposition.pca,
# which has been deprecated in sklearn v0.24
# and must be explicitly imported with `from sklearn.decomposition import PCA`.
# This is a hacky workaround to maintain forward compatibility.
sys.modules["sklearn.decomposition.pca"] = _pca

MODEL_NAME = "Resnet-101-AP-GeM"
MODEL_URL = "https://github.com/outernet-foundation/placeframe/releases/download/assets-v1/Resnet-101-AP-GeM.pt"
WHITEN_NAME = "Landmarks_clean"
WHITENP = 0.25
WHITENV = None
WHITENM = 1.0


class _DIRNet(Protocol):
    preprocess: Mapping[str, Any]
    pca: Mapping[str, Any]

    def __call__(self, image: Tensor) -> Tensor: ...


class DIR(Module):
    def __init__(self) -> None:
        super().__init__()  # type: ignore

        checkpoint = Path(get_dir(), "dirtorch", MODEL_NAME + ".pt")
        if not checkpoint.exists():
            checkpoint.parent.mkdir(exist_ok=True, parents=True)
            print(f"Downloading DIR model from {MODEL_URL}")
            torch.hub.download_url_to_file(MODEL_URL, str(checkpoint))

        self.net = cast(_DIRNet, load_model(checkpoint, False))  # first load on CPU
        assert WHITEN_NAME in self.net.pca

    def forward(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
        image = data["image"]
        assert image.shape[1] == 3
        image = image - image.new_tensor(self.net.preprocess["mean"])[:, None, None]
        image = image / image.new_tensor(self.net.preprocess["std"])[:, None, None]

        return {
            "global_descriptor": from_numpy(
                cast(
                    NDArray[float32],
                    whiten_features(
                        self.net(image).unsqueeze(0).detach().cpu().numpy(),
                        self.net.pca[WHITEN_NAME],
                        whitenp=WHITENP,
                        whitenv=WHITENV,
                        whitenm=WHITENM,
                    ),
                )
            ).to(image.device)
        }


def load_DIR(device: str = "cpu"):
    _orig_load = torch.load  # type: ignore

    # PyTorch 2.6 flips torch.load default to weights_only=True, so we temporarily force legacy loading to read DIR’s pickled checkpoint;
    # see: https://dev-discuss.pytorch.org/t/bc-breaking-change-torch-load-is-being-flipped-to-use-weights-only-true-by-default-in-the-nightlies-after-137602/2573
    def _load_legacy(*args, **kwargs):  # type: ignore
        kwargs.setdefault("weights_only", False)  # type: ignore
        return _orig_load(*args, **kwargs)  # type: ignore

    torch.load = _load_legacy
    dir: DIR = DIR().to(device).eval()
    torch.load = _orig_load

    return dir


def load_superpoint(
    nms_radius: float | None = None,
    keypoint_threshold: float | None = None,
    max_num_keypoints: int | None = None,
    remove_borders: int | None = None,
    device: str = "cpu",
):
    conf: dict[str, Any] = {}
    if nms_radius is not None:
        conf["nms_radius"] = nms_radius
    if keypoint_threshold is not None:
        conf["keypoint_threshold"] = keypoint_threshold
    if max_num_keypoints is not None:
        conf["max_num_keypoints"] = max_num_keypoints
    if remove_borders is not None:
        conf["remove_borders"] = remove_borders

    return SuperPoint(**conf).eval().to(device)


def load_lightglue(device: str = "cpu"):
    # TODO: add comment about why width_confidence and depth_confidence are set to -1
    return LightGlue(features="superpoint", width_confidence=-1, depth_confidence=-1).eval().to(device)
