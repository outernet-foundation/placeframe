from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from os import environ
from pathlib import Path
from threading import Lock
from typing import Annotated
from uuid import UUID

from common.boto_clients import create_s3_client
from common.litestar import create_litestar_app
from common.multipart_requests import MultipartRequestModel, MultipartRequestOperation
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from litestar import post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server
from litestar.params import Body
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY

from .map import Map, load_map
from .schemas import LoadState, Localization
from .settings import get_settings

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")


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

    load_models(settings.max_keypoints_per_image)


class LocalizationRequest(MultipartRequestModel):
    reconstruction_ids: list[UUID]
    camera_config: PinholeCameraConfig
    axis_convention: AxisConvention
    retrieval_top_k: int
    ransac_threshold: float
    image: UploadFile


@post("/localization", operation_class=MultipartRequestOperation)
async def localize_image(
    data: Annotated[LocalizationRequest, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> list[Localization]:
    if environ.get("CODEGEN"):
        raise

    # Import here to avoid importing torch during codegen
    from .localize import LocalizationError, localize_image_against_reconstruction

    image = await data.image.read()

    localizations: list[Localization] = []
    errors: list[str] = []

    for id in data.reconstruction_ids:
        if id not in _maps:
            _maps[id] = load_map(id, s3_client, settings.reconstructions_bucket, RECONSTRUCTIONS_DIR)

        try:
            result = localize_image_against_reconstruction(
                _maps[id], data.camera_config, data.axis_convention, image, data.retrieval_top_k, data.ransac_threshold
            )

            localizations.append(Localization(id=id, transform=result[0], metrics=result[1]))
        except LocalizationError as e:
            errors.append(f"Reconstruction {id}: {str(e)}")

    if not localizations:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="; ".join(errors))

    return localizations


openapi_config = OpenAPIConfig("Localizer", "0.1.0", servers=[Server(url="http://localhost:8000")])


app = create_litestar_app([localize_image], openapi_config)
