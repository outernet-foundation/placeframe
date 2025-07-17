from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute
from piccolo_admin.endpoints import create_admin

from .db.app import APP_CONFIG
from .db.conf.local import DB
from .routers.captures import router as captures_router


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

app.mount("/admin", create_admin(tables=APP_CONFIG.table_classes), name="admin")

app.include_router(captures_router)
