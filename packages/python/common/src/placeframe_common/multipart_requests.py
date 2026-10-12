import json
from typing import ClassVar

from litestar.enums import RequestEncodingType
from litestar.openapi.spec import Encoding, OpenAPIMediaType, Operation, Reference, RequestBody, Schema
from pydantic import BaseModel, ConfigDict
from pydantic.types import Json as JsonMetadata


def multipart_json(value: str | list[str]) -> str:
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError("expected exactly one multipart value")
        return value[0]

    return value


def multipart_json_list(value: str | list[str]) -> str:
    if isinstance(value, list):
        if len(value) == 1:
            value = value[0]
        else:
            return json.dumps(value)

    if "," in value and not value.lstrip().startswith("["):
        return json.dumps([part.strip() for part in value.split(",")])

    if not value.lstrip().startswith("["):
        return json.dumps([value])

    return value


class MultipartRequestModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    multipart_json_fields: ClassVar[dict[str, set[str]]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: object) -> None:  # noqa: PLW3201
        super().__pydantic_init_subclass__(**kwargs)
        cls.multipart_json_fields[cls.__name__] = {
            field_name
            for field_name, field_info in cls.model_fields.items()
            if any(type(item) is JsonMetadata for item in field_info.metadata)
        }


class MultipartRequestOperation(Operation):
    def to_schema(self) -> dict[str, object]:
        request_body = self.request_body
        if not isinstance(request_body, RequestBody):
            return super().to_schema()

        media_type = request_body.content.get(RequestEncodingType.MULTI_PART)
        if not isinstance(media_type, OpenAPIMediaType):
            return super().to_schema()

        schema = media_type.schema
        model_name: str | None = None

        if isinstance(schema, Reference):
            model_name = schema.ref.rsplit("/", maxsplit=1)[-1]
        elif isinstance(schema, Schema) and isinstance(schema.title, str):
            model_name = schema.title

        json_fields = MultipartRequestModel.multipart_json_fields.get(model_name or "", set())
        if json_fields:
            encoding = media_type.encoding or {}
            encoding.update({
                field_name: Encoding(content_type="application/json") for field_name in sorted(json_fields)
            })
            media_type.encoding = encoding

        return super().to_schema()
