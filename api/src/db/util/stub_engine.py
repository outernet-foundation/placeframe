# Stub engine for piccolo to avoid connection hangs when no connection is available while running
# commands that don't require a database connection

from __future__ import annotations

import typing

from api.src.db.util.shims import PostgresEngine


class StubEngine(PostgresEngine):
    def __init__(self) -> None:
        self.config = {}
        self.extensions = ()
        self.version_number = None

    async def start_connection_pool(self, **_: dict[str, "typing.Any"]) -> None:
        pass

    async def close_connection_pool(self) -> None:
        pass
