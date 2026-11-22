from typing import Annotated, cast
from uuid import UUID

from placeframe_common.multipart_requests import (
    MultipartRequestModel,
    MultipartRequestOperation,
    multipart_json,
    multipart_json_list,
)
from placeframe_core.axis_convention import AxisConvention
from placeframe_core.camera_config import PinholeCameraConfig
from placeframe_core.localization_metrics import LocalizationMetrics
from placeframe_core.transform import Float3, Float4, Transform
from datamodels.public_tables import Reconstruction
from litestar import Router, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_503_SERVICE_UNAVAILABLE
from placeframe_localizer_client import ApiClient, ApiException, Configuration
from placeframe_localizer_client.api.default_api import DefaultApi
from placeframe_localizer_client.models.axis_convention import AxisConvention as LocalizerAxisConvention
from placeframe_localizer_client.models.pinhole_camera_config import PinholeCameraConfig as LocalizerPinholeCameraConfig
from placeframe_localizer_client.models.reconstruction_metrics import (
    ReconstructionMetrics as LocalizerReconstructionMetrics,
)
from httpx import AsyncClient, HTTPError
from pydantic import BaseModel, BeforeValidator, Json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .localization_maps import fetch_localization_maps

UNAVAILABLE_DETAIL = "Localization unavailable"


class LocalizationRequest(MultipartRequestModel):
    map_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]
    camera_config: Annotated[Json[PinholeCameraConfig], BeforeValidator(multipart_json)]
    axis_convention: AxisConvention
    retrieval_top_k: int | None = None
    ransac_threshold: float | None = None
    image: UploadFile


class MapLocalization(BaseModel):
    id: UUID
    camera_from_map_transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics


class LocalizerAddress(BaseModel):
    address: str | None
    retry_after_seconds: int


@post("/", operation_class=MultipartRequestOperation)
async def localize_image(
    session: AsyncSession, data: Annotated[LocalizationRequest, Body(media_type=RequestEncodingType.MULTI_PART)]
) -> list[MapLocalization]:
    reconstruction_id_to_map_id = {
        map.reconstruction_id: map for map in await fetch_localization_maps(session, data.map_ids)
    }
    manifest_rows = (
        await session.execute(
            select(Reconstruction.id, Reconstruction.manifest).where(
                Reconstruction.id.in_(reconstruction_id_to_map_id.keys())
            )
        )
    ).all()
    image = await data.image.read()
    localizer_address = await resolve_localizer_address()

    async with ApiClient(Configuration(host=localizer_address)) as api_client:
        try:
            localizations = await DefaultApi(api_client).localize_image(
                reconstruction_ids=list(reconstruction_id_to_map_id.keys()),
                metrics={
                    str(row_id): LocalizerReconstructionMetrics.model_validate(manifest["metrics"])
                    for row_id, manifest in manifest_rows
                },
                camera_config=LocalizerPinholeCameraConfig.model_validate(data.camera_config.model_dump()),
                axis_convention=LocalizerAxisConvention(data.axis_convention.value),
                image=image,
                retrieval_top_k=data.retrieval_top_k,
                ransac_threshold=data.ransac_threshold,
            )

            return [
                MapLocalization(
                    id=reconstruction_id_to_map_id[localization.id].id,
                    camera_from_map_transform=Transform.model_validate(localization.transform.model_dump()),
                    map_transform=Transform(
                        translation=Float3(
                            x=reconstruction_id_to_map_id[localization.id].position_x,
                            y=reconstruction_id_to_map_id[localization.id].position_y,
                            z=reconstruction_id_to_map_id[localization.id].position_z,
                        ),
                        rotation=Float4(
                            x=reconstruction_id_to_map_id[localization.id].rotation_x,
                            y=reconstruction_id_to_map_id[localization.id].rotation_y,
                            z=reconstruction_id_to_map_id[localization.id].rotation_z,
                            w=reconstruction_id_to_map_id[localization.id].rotation_w,
                        ),
                    ),
                    metrics=LocalizationMetrics.model_validate(localization.metrics.model_dump()),
                )
                for localization in localizations
            ]

        except ApiException as e:
            status = cast(int | None, e.status)
            if status == 422:
                raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY) from e
            raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_DETAIL) from e


@get("/version")
async def get_localizer_version() -> str:
    async with ApiClient(Configuration(host=await resolve_localizer_address())) as api_client:
        return await DefaultApi(api_client).get_localizer_version()


async def resolve_localizer_address() -> str:
    # Query the router for the localizer address only when the router manages the GPU slot
    settings = get_settings()
    if not settings.localizer_router_managed:
        # Return the router address unchanged because unmanaged modes keep the localizer always on
        return str(settings.localizer_router_address)

    try:
        async with AsyncClient() as http:
            response = await http.get(f"{settings.localizer_router_address}/localizer-address")
            response.raise_for_status()
    except HTTPError as e:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_DETAIL) from e

    result = LocalizerAddress.model_validate(response.json())

    # If no localizer is running
    if result.address is None:
        # Echo the orchestrator's warm-up hint in the Retry-After header
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=UNAVAILABLE_DETAIL,
            headers={"Retry-After": str(result.retry_after_seconds)},
        )
    return result.address


router = Router(
    "/localize",
    tags=["Localization"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[localize_image, get_localizer_version],
)
