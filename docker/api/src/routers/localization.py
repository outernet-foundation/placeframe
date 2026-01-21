from typing import Annotated, cast
from uuid import UUID

from common.multipart_requests import MultipartRequestModel, MultipartRequestOperation
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.localization_metrics import LocalizationMetrics
from core.transform import Float3, Float4, Transform
from litestar import Router, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_502_BAD_GATEWAY
from plerion_localizer_client import ApiClient, ApiException, Configuration
from plerion_localizer_client.api.default_api import DefaultApi
from plerion_localizer_client.models.axis_convention import AxisConvention as LocalizerAxisConvention
from plerion_localizer_client.models.pinhole_camera_config import PinholeCameraConfig as LocalizerPinholeCameraConfig
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .localization_maps import fetch_localization_maps

settings = get_settings()


class LocalizationRequest(MultipartRequestModel):
    map_ids: list[UUID]
    camera_config: PinholeCameraConfig
    axis_convention: AxisConvention
    retrieval_top_k: int
    ransac_threshold: float
    image: UploadFile


class MapLocalization(BaseModel):
    id: UUID
    camera_from_map_transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics


@post("/", operation_class=MultipartRequestOperation)
async def localize_image(
    session: AsyncSession, data: Annotated[LocalizationRequest, Body(media_type=RequestEncodingType.MULTI_PART)]
) -> list[MapLocalization]:
    reconstruction_id_to_map_id = {
        map.reconstruction_id: map for map in await fetch_localization_maps(session, data.map_ids)
    }

    async with ApiClient(Configuration(host=str(settings.localizer_container_url))) as api_client:
        try:
            localizations = await DefaultApi(api_client).localize_image(
                list(reconstruction_id_to_map_id.keys()),
                LocalizerPinholeCameraConfig.model_validate(data.camera_config.model_dump()),
                LocalizerAxisConvention(data.axis_convention.value),
                data.retrieval_top_k,
                data.ransac_threshold,
                await data.image.read(),
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
            raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail="Localization session backend error") from e


router = Router(
    "/localize", tags=["Localization"], dependencies={"session": Provide(get_session)}, route_handlers=[localize_image]
)
