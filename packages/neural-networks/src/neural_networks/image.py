from io import BytesIO
from typing import Literal

from cv2 import COLOR_BGR2GRAY, COLOR_BGR2RGB, IMREAD_COLOR, cvtColor, imdecode
from numpy import frombuffer, uint8
from PIL import Image
from PIL.Image import Transpose
from torch import float32, from_numpy  # type: ignore


def create_image_tensors(rotation: Literal["None", "90_CW", "180", "90_CCW"], buffer: bytes, device: str):
    image = Image.open(BytesIO(buffer))
    if rotation == "90_CCW":
        image = image.transpose(Transpose.ROTATE_270)
    elif rotation == "90_CW":
        image = image.transpose(Transpose.ROTATE_90)
    elif rotation == "180":
        image = image.transpose(Transpose.ROTATE_180)

    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=95)
    buffer = buffered.getvalue()

    bgr_image = imdecode(frombuffer(buffer, uint8), IMREAD_COLOR)

    rgb_image = cvtColor(bgr_image, COLOR_BGR2RGB)
    rbg_image_tensor = from_numpy(rgb_image).permute(2, 0, 1).unsqueeze(0).div(255.0).to(device=device, dtype=float32)

    grayscale_image = cvtColor(bgr_image, COLOR_BGR2GRAY)
    grayscale_image_tensor = (
        from_numpy(grayscale_image).unsqueeze(0).unsqueeze(0).div(255.0).to(device=device, dtype=float32)
    )

    return rbg_image_tensor, grayscale_image_tensor, bgr_image.shape[:2]
