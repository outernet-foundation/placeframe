from typing import Annotated
from uuid import UUID, uuid4

import pytest
from common.multipart_requests import (
    MultipartRequestModel,
    MultipartRequestOperation,
    multipart_json,
    multipart_json_list,
)
from litestar import Litestar, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from pydantic import BaseModel, BeforeValidator, Json, ValidationError


class _CameraConfig(BaseModel):
    width: int


class _MultipartUuidListPayload(MultipartRequestModel):
    reconstruction_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]


class _MultipartObjectPayload(MultipartRequestModel):
    camera_config: Annotated[Json[_CameraConfig], BeforeValidator(multipart_json)]


class _MultipartRoutePayload(MultipartRequestModel):
    reconstruction_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]
    camera_config: Annotated[Json[_CameraConfig], BeforeValidator(multipart_json)]
    image: UploadFile


@post("/localization", operation_class=MultipartRequestOperation, sync_to_thread=False)
def _multipart_route(data: Annotated[_MultipartRoutePayload, Body(media_type=RequestEncodingType.MULTI_PART)]) -> None:
    del data


@pytest.fixture
def uuid_list_input(request: pytest.FixtureRequest) -> tuple[str | list[str], list[UUID]]:
    a, b = uuid4(), uuid4()
    formats: dict[str, tuple[str | list[str], list[UUID]]] = {
        "single-uuid-in-list": ([str(a)], [a]),
        "bare-uuid-string": (str(a), [a]),
        "json-array-single": ([f'["{a}"]'], [a]),
        "json-array-multiple": ([f'["{a}","{b}"]'], [a, b]),
        "csv-string": ([f"{a},{b}"], [a, b]),
        "multi-format-list": ([str(a), str(b)], [a, b]),
    }
    return formats[request.param]


@pytest.mark.parametrize(
    "uuid_list_input",
    [
        "single-uuid-in-list",
        "bare-uuid-string",
        "json-array-single",
        "json-array-multiple",
        "csv-string",
        "multi-format-list",
    ],
    indirect=True,
)
def test_multipart_request_model_parses_uuid_list(uuid_list_input: tuple[str | list[str], list[UUID]]) -> None:
    raw_input, expected = uuid_list_input
    payload = _MultipartUuidListPayload.model_validate({"reconstruction_ids": raw_input})

    assert payload.reconstruction_ids == expected


def test_multipart_request_model_parses_json_objects_from_single_part_lists() -> None:
    payload = _MultipartObjectPayload.model_validate({"camera_config": ['{"width": 1280}']})

    assert payload.camera_config == _CameraConfig(width=1280)


def test_multipart_request_model_rejects_multiple_json_object_parts() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _MultipartObjectPayload.model_validate({"camera_config": ['{"width": 1280}', '{"width": 720}']})

    assert exc_info.value.errors()[0]["type"] == "value_error"


def test_multipart_request_operation_marks_uuid_arrays_as_json() -> None:
    app = Litestar(route_handlers=[_multipart_route])

    schema = app.openapi_schema.to_schema()
    content = schema["paths"]["/localization"]["post"]["requestBody"]["content"]["multipart/form-data"]

    assert content["encoding"]["camera_config"]["contentType"] == "application/json"
    assert content["encoding"]["reconstruction_ids"]["contentType"] == "application/json"
