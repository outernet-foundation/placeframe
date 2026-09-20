from __future__ import annotations

from io import BytesIO

from PIL import Image as PILImage
from PIL.Image import Resampling, Transpose

from .camera_config import ImageOrientation, PinholeCameraConfig

# Standardizes per-pixel scale across cameras with different resolutions, so the feature extractor's
# fixed-pixel receptive field sees comparable structure regardless of source camera.
LOCAL_FEATURE_RESIZE_SHORTER_SIDE = 1024


def canonicalize_image(image_buffer: bytes, orientation: ImageOrientation) -> PILImage.Image:
    image = PILImage.open(BytesIO(image_buffer))
    image = _orient(image, orientation)
    new_width, new_height = _resized_dimensions(image.width, image.height)
    if (new_width, new_height) != (image.width, image.height):
        image = image.resize((new_width, new_height), Resampling.LANCZOS)
    return image.convert("RGB")


def canonicalize_intrinsics(camera: PinholeCameraConfig):
    width, height, fx, fy, cx, cy = _oriented_intrinsics(camera)
    new_width, new_height = _resized_dimensions(width, height)
    scale_x = new_width / width
    scale_y = new_height / height
    return new_width, new_height, fx * scale_x, fy * scale_y, cx * scale_x, cy * scale_y


def _resized_dimensions(width: int, height: int) -> tuple[int, int]:
    scale = LOCAL_FEATURE_RESIZE_SHORTER_SIDE / min(width, height)
    return round(width * scale), round(height * scale)


def _orient(image: PILImage.Image, orientation: ImageOrientation) -> PILImage.Image:
    match orientation:
        case "TOP_LEFT":
            return image
        case "TOP_RIGHT":
            return image.transpose(Transpose.FLIP_LEFT_RIGHT)
        case "BOTTOM_RIGHT":
            return image.transpose(Transpose.ROTATE_180)
        case "BOTTOM_LEFT":
            return image.transpose(Transpose.FLIP_TOP_BOTTOM)
        case "LEFT_TOP":
            return image.transpose(Transpose.TRANSPOSE)
        case "RIGHT_TOP":
            return image.transpose(Transpose.ROTATE_270)
        case "RIGHT_BOTTOM":
            return image.transpose(Transpose.TRANSVERSE)
        case "LEFT_BOTTOM":
            return image.transpose(Transpose.ROTATE_90)


def _oriented_intrinsics(camera: PinholeCameraConfig) -> tuple[int, int, float, float, float, float]:
    width = camera.width
    height = camera.height

    if camera.orientation == "TOP_LEFT":
        return camera.width, camera.height, camera.fx, camera.fy, camera.cx, camera.cy

    if camera.orientation == "TOP_RIGHT":
        return camera.width, camera.height, camera.fx, camera.fy, (width - camera.cx), camera.cy

    if camera.orientation == "BOTTOM_RIGHT":
        return camera.width, camera.height, camera.fx, camera.fy, (width - camera.cx), (height - camera.cy)

    if camera.orientation == "BOTTOM_LEFT":
        return camera.width, camera.height, camera.fx, camera.fy, camera.cx, (height - camera.cy)

    new_width = camera.height
    new_height = camera.width

    if camera.orientation == "LEFT_TOP":
        return new_width, new_height, camera.fy, camera.fx, camera.cy, camera.cx

    if camera.orientation == "RIGHT_TOP":
        return new_width, new_height, camera.fy, camera.fx, (height - camera.cy), camera.cx

    if camera.orientation == "RIGHT_BOTTOM":
        return new_width, new_height, camera.fy, camera.fx, (height - camera.cy), (width - camera.cx)

    if camera.orientation == "LEFT_BOTTOM":
        return new_width, new_height, camera.fy, camera.fx, camera.cy, (width - camera.cx)

    raise ValueError(f"Unknown orientation: {camera.orientation!r}")
