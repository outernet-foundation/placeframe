from typing import Callable, TypeVar

from fastapi import Form, HTTPException
from pydantic import TypeAdapter, ValidationError

T = TypeVar("T")


def make_multipart_json_dep(name: str, adapter: TypeAdapter[T]) -> Callable[[str], T]:
    def dep(value: str = Form(..., alias=name)) -> T:
        try:
            return adapter.validate_json(value)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())

    return dep
