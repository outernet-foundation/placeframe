# Wrappers for some Piccolo functionality to provide type signatures that pass strict Pyright checks

from __future__ import annotations

from typing import Any, Dict, Tuple, Type, TypeVar

from piccolo.columns import Column
from piccolo.engine.postgres import PostgresEngine as PiccoloPostgresEngine
from piccolo.query import Exists, Objects
from piccolo.table import Table as PiccoloTable
from piccolo.utils.pydantic import (
    create_pydantic_model as _create_pydantic_model,  # type: ignore[reportUnknownVariableType]
)
from pydantic import BaseModel, ConfigDict

_TTable = TypeVar("_TTable", bound="Table")


class Table(PiccoloTable):
    @classmethod
    def objects(cls: Type[_TTable], *prefetch: Any) -> Objects[_TTable]:
        return super().objects(*prefetch)  # type: ignore[override]

    @classmethod
    def exists(cls: Type[_TTable]) -> Exists[_TTable]:
        return super().exists()  # type: ignore[override]


def create_pydantic_model(
    table: Type[_TTable],
    *,
    nested: bool | Any = False,
    exclude_columns: Tuple[Column, ...] = (),
    include_columns: Tuple[Column, ...] = (),
    include_default_columns: bool = False,
    include_readable: bool = False,
    all_optional: bool = False,
    model_name: str | None = None,
    deserialize_json: bool = False,
    recursion_depth: int = 0,
    max_recursion_depth: int = 5,
    pydantic_config: ConfigDict | None = None,
    json_schema_extra: Dict[str, Any] | None = None,
) -> Type[BaseModel]:
    return _create_pydantic_model(
        table=table,
        nested=nested,
        exclude_columns=exclude_columns,
        include_columns=include_columns,
        include_default_columns=include_default_columns,
        include_readable=include_readable,
        all_optional=all_optional,
        model_name=model_name,
        deserialize_json=deserialize_json,
        recursion_depth=recursion_depth,
        max_recursion_depth=max_recursion_depth,
        pydantic_config=pydantic_config,
        json_schema_extra=json_schema_extra,
    )


class PostgresEngine(PiccoloPostgresEngine):
    async def start_connection_pool(self) -> None:  # type: ignore[override]
        return await super().start_connection_pool()  # type: ignore[override]
