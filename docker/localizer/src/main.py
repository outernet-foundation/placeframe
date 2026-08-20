from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from os import environ
from pathlib import Path
from threading import Lock
from typing import Annotated
from uuid import UUID

from common.boto_clients import create_s3_client
from common.litestar import create_litestar_app
from common.logging_config import configure_logging
from common.multipart_requests import (
    MultipartRequestModel,
    MultipartRequestOperation,
    multipart_json,
    multipart_json_list,
)
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.reconstruction_metrics import ReconstructionMetrics
from litestar import get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server
from litestar.params import Body
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import BeforeValidator, Json

from core.calibration import CalibrationArtifact
from .map import Map, load_map
from .schemas import LoadState, Localization
from .settings import get_settings

configure_logging("localizer")

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")
CALIBRATION_GLOBAL_PATH = Path("/etc/placeframe/calibration/global.json")


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

pipeline_version: str = ""
calibration: CalibrationArtifact | None = None

if not environ.get("CODEGEN"):
    from core.calibration import load_global_calibration
    from .localize import load_models

    load_models()
    pipeline_version = environ["LOCALIZER_SHA"]
    calibration = load_global_calibration(CALIBRATION_GLOBAL_PATH, pipeline_version)
    print(f"Loaded global calibration (pipeline_version={pipeline_version[:12]}…)")


class LocalizationRequest(MultipartRequestModel):
    reconstruction_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]
    metrics: Annotated[Json[dict[UUID, ReconstructionMetrics]], BeforeValidator(multipart_json)]
    camera_config: Annotated[Json[PinholeCameraConfig], BeforeValidator(multipart_json)]
    axis_convention: AxisConvention
    retrieval_top_k: int | None = None
    ransac_threshold: float | None = None
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
            _maps[id] = load_map(id, s3_client, settings.reconstructions_bucket, RECONSTRUCTIONS_DIR, data.metrics[id])

        try:
            assert calibration is not None  # CODEGEN-guarded; runtime always has it
            result = localize_image_against_reconstruction(
                _maps[id],
                data.camera_config,
                data.axis_convention,
                image,
                data.retrieval_top_k,
                data.ransac_threshold,
                pipeline_version,
                calibration,
            )

            localizations.append(Localization(id=id, transform=result[0], metrics=result[1]))
        except LocalizationError as e:
            errors.append(f"Reconstruction {id}: {str(e)}")

    if not localizations:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="; ".join(errors))

    return localizations


@get("/version")
async def get_localizer_version() -> str:
    return pipeline_version


openapi_config = OpenAPIConfig("Localizer", "0.1.0", servers=[Server(url="http://localhost:8000")])


app = create_litestar_app([localize_image, get_localizer_version], openapi_config, logging_config=None)
