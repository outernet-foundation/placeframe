# Vibe code: Gemini 3
#
# These classes add Litestar support for multipart/form-data requests containg both JSON and binary data

import json
from typing import Any, Dict, List, cast

from litestar.openapi.spec import Operation
from pydantic import BaseModel, model_validator


class MultipartRequestModel(BaseModel):
    # Allow Pydantic to accept 'UploadFile' (a Litestar type) without trying to generate a schema for it
    model_config = {"arbitrary_types_allowed": True}

    @staticmethod
    def _robust_json_load(v: Any) -> Any:
        # Litestar extracts multipart fields as a list of strings
        if isinstance(v, list):
            v_list = cast(List[Any], v)
            if len(v_list) == 1:
                first = v_list[0]
                if isinstance(first, str):
                    try:
                        return json.loads(first)
                    except (ValueError, TypeError):
                        pass
            return v_list

        # Handle standard JSON strings (objects/arrays)
        if isinstance(v, str):
            try:
                if v.strip().startswith(("{", "[")):
                    return json.loads(v)
            except (ValueError, TypeError):
                pass

        return v

    @model_validator(mode="before")
    @classmethod
    def parse_multipart_json(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_dict = dict(cast(Dict[str, Any], data))

            for key, value in data_dict.items():
                data_dict[key] = cls._robust_json_load(value)
            return data_dict

        return data


class MultipartRequestOperation(Operation):
    def to_schema(self) -> dict[str, Any]:
        schema_dict: dict[str, Any] = super().to_schema()

        if "requestBody" not in schema_dict:
            return schema_dict

        request_body = cast(Dict[str, Any], schema_dict["requestBody"])
        content = cast(Dict[str, Any], request_body.get("content", {}))

        if "multipart/form-data" not in content:
            return schema_dict

        media_type_obj = cast(Dict[str, Any], content["multipart/form-data"])
        schema = cast(Dict[str, Any], media_type_obj.get("schema", {}))
        properties = cast(Dict[str, Any], schema.get("properties", {}))

        encoding_map: dict[str, Any] = {}

        for prop_name, prop_val in properties.items():
            prop_schema = cast(Dict[str, Any], prop_val)

            # Heuristic: $ref implies complex object (Pydantic Model)
            is_ref: bool = "$ref" in prop_schema

            # Heuristic: Array of $refs
            items_schema = cast(Dict[str, Any], prop_schema.get("items", {}))
            is_array_ref: bool = prop_schema.get("type") == "array" and "$ref" in items_schema

            if is_ref or is_array_ref:
                encoding_map[prop_name] = {"contentType": "application/json"}

        if encoding_map:
            if "encoding" not in media_type_obj:
                media_type_obj["encoding"] = {}

            encoding_dict = cast(Dict[str, Any], media_type_obj["encoding"])
            encoding_dict.update(encoding_map)

        return schema_dict
