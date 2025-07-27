import asyncio
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.routing import APIRoute
from mangum import Mangum
from piccolo.engine import engine_finder  # type: ignore[import-untyped]

from .db.piccolo_shims import PostgresEngine
from .routers.captures import router as captures_router

try:
    DB = cast(PostgresEngine, engine_finder())
except Exception as e:
    print("Error finding database engine:", e)

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


# Make codegened client functions use the same name as their corresponding server functions
def use_handler_name(route: APIRoute) -> str:
    return route.name


@asynccontextmanager
async def lifespan(_: FastAPI):
    await DB.start_connection_pool()
    try:
        yield
    finally:
        await DB.close_connection_pool()


app = FastAPI(
    title="Plerion API",
    version="0.0.1",
    generate_unique_id_function=use_handler_name,
    lifespan=lifespan,
)

handler = Mangum(app)

app.include_router(captures_router)
