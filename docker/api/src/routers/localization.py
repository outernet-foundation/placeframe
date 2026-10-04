import json
from typing import Annotated, Any, cast
from uuid import UUID

from common.multipart_requests import (
    MultipartRequestModel,
    MultipartRequestOperation,
    multipart_json,
    multipart_json_list,
)
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.localization_detail import LocalizationDetail
from core.localization_metrics import LocalizationMetrics
from core.transform import Float3, Float4, Transform
from datamodels.public_tables import Reconstruction
from litestar import Router, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_502_BAD_GATEWAY
from placeframe_localizer_client import ApiClient, ApiException, Configuration
from placeframe_localizer_client.api.default_api import DefaultApi
from placeframe_localizer_client.models.axis_convention import AxisConvention as LocalizerAxisConvention
from placeframe_localizer_client.models.pinhole_camera_config import PinholeCameraConfig as LocalizerPinholeCameraConfig
from placeframe_localizer_client.models.reconstruction_metrics import (
    ReconstructionMetrics as LocalizerReconstructionMetrics,
)
from pydantic import BaseModel, BeforeValidator, Json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .localization_maps import fetch_localization_maps

settings = get_settings()


class LocalizationRequest(MultipartRequestModel):
    map_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]
    camera_config: Annotated[Json[PinholeCameraConfig], BeforeValidator(multipart_json)]
    axis_convention: AxisConvention
    retrieval_top_k: int | None = None
    ransac_threshold: float | None = None
    use_chunking: bool = True
    detail: bool = False
    image: UploadFile


class MapLocalization(BaseModel):
    id: UUID
    camera_from_map_transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics
    # Present only when the request asked for it. Pure diagnostics -- nothing in the pose path
    # reads it, so a client that does not request it pays nothing.
    detail: LocalizationDetail | None = None


def _localizer_failure(exception: ApiException) -> tuple[str, list[Any] | None]:
    """The localizer's own 422 reason and its structured per-reconstruction failures.

    The localizer answers a total failure with `{detail: str, extra: [LocalizationFailure]}`.
    Both are forwarded: the string so a human sees why, the list so a diagnostic client can
    read the failing query's detail payload, which is the case most worth inspecting.
    """
    body = cast(str | bytes | None, exception.body)
    if body is None:
        return "Localization failed", None
    try:
        payload = cast(dict[str, Any], json.loads(body))
    except (ValueError, TypeError):
        return "Localization failed", None
    message = payload.get("detail")
    extra = cast("list[Any] | None", payload.get("extra") if isinstance(payload.get("extra"), list) else None)
    return (message if isinstance(message, str) and message else "Localization failed", extra)


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

    async with ApiClient(Configuration(host=str(settings.localizer_container_url))) as api_client:
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
                use_chunking=data.use_chunking,
                detail=data.detail,
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
                    detail=(
                        LocalizationDetail.model_validate(localization.detail.model_dump())
                        if localization.detail is not None
                        else None
                    ),
                )
                for localization in localizations
            ]

        except ApiException as e:
            status = cast(int | None, e.status)
            if status == 422:
                # Forward the localizer's own reason rather than an empty 422. "No matching
                # keypoints found", "Pose estimation failed" and "Confidence below gate" are
                # three different problems with three different fixes, and a caller that cannot
                # tell them apart cannot act on any of them.
                message, failures = _localizer_failure(e)
                raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=message, extra=failures) from e
            raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail="Localization session backend error") from e


@get("/version")
async def get_localizer_version() -> str:
    async with ApiClient(Configuration(host=str(settings.localizer_container_url))) as api_client:
        return await DefaultApi(api_client).get_localizer_version()


router = Router(
    "/localize",
    tags=["Localization"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[localize_image, get_localizer_version],
)
