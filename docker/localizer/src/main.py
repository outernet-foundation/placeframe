from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from os import environ
from pathlib import Path
from threading import Lock
from typing import Annotated, Any
from uuid import UUID

from common.boto_clients import create_s3_client
from common.litestar import create_litestar_app
from common.multipart_requests import MultipartRequestModel, MultipartRequestOperation
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from litestar import post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server
from litestar.params import Body

from .map import Map, load_map
from .schemas import LoadState, Localization
from .settings import get_settings

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")
MAX_KEYPOINTS = 2500
RETRIEVAL_TOP_K = 12  # how many similar database images to keep
RANSAC_THRESHOLD = 12.0  # reprojection error in pixels


_executor = ThreadPoolExecutor(max_workers=2)
_load_lock = Lock()
_load_state: dict[UUID, LoadState] = {}
_load_error: dict[UUID, str] = {}
_maps: dict[UUID, Map] = {}

settings = get_settings()
s3_client = create_s3_client(
    minio_endpoint_url=settings.minio_endpoint_url,
    minio_access_key=settings.minio_access_key,
    minio_secret_key=settings.minio_secret_key,
)


if not environ.get("CODEGEN"):
    from .localize import load_models

    load_models(2500)


def deserialize_json(v: Any) -> Any:
    try:
        return json.loads(v)
    except (ValueError, TypeError):
        # If parsing fails, return original to let Pydantic raise the validation error
        return v


class LocalizationRequest(MultipartRequestModel):
    reconstruction_ids: list[UUID]
    camera_config: PinholeCameraConfig
    axis_convention: AxisConvention
    image: UploadFile


@post("/localization", operation_class=MultipartRequestOperation)
async def localize_image(
    data: Annotated[LocalizationRequest, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> list[Localization]:
    if environ.get("CODEGEN"):
        raise

    # Import here to avoid importing torch during codegen
    from .localize import localize_image_against_reconstruction

    reconstruction_ids = data.reconstruction_ids
    camera = data.camera_config
    axis_convention = data.axis_convention
    image = await data.image.read()

    localizations: list[Localization] = []
    for id in reconstruction_ids:
        if id not in _maps:
            _maps[id] = load_map(id, s3_client, settings.reconstructions_bucket, RECONSTRUCTIONS_DIR)

        result = localize_image_against_reconstruction(
            map=_maps[id],
            camera=camera,
            axis_convention=axis_convention,
            image_buffer=image,
            retrieval_top_k=RETRIEVAL_TOP_K,
            ransac_threshold=RANSAC_THRESHOLD,
        )

        localizations.append(Localization(id=id, transform=result[0], metrics=result[1]))

    return localizations


openapi_config = OpenAPIConfig("Localizer", "0.1.0", servers=[Server(url="http://localhost:8000")])


app = create_litestar_app([localize_image], openapi_config)
