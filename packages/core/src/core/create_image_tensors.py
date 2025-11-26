from io import BytesIO
from typing import Literal

from numpy import asarray, float32
from PIL import Image as PILImage
from PIL.Image import Transpose
from torch import from_numpy  # type: ignore


def create_image_tensors(image_buffer: bytes, camera_rotation: Literal["None", "90_CW", "180", "90_CCW"]):
    image = PILImage.open(BytesIO(image_buffer))

    if camera_rotation == "90_CCW":
        image = image.transpose(Transpose.ROTATE_270)
    elif camera_rotation == "90_CW":
        image = image.transpose(Transpose.ROTATE_90)
    elif camera_rotation == "180":
        image = image.transpose(Transpose.ROTATE_180)

    image = image.convert("RGB")

    return (
        image,
        # RGB (permuted because DIR expects channel-first)
        from_numpy(asarray(image, dtype=float32)).permute(2, 0, 1).div(255.0),
        # Grayscale
        from_numpy(asarray(image.convert("L"), dtype=float32)).unsqueeze(0).div(255.0),
    )
