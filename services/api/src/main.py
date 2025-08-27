import os
from contextlib import asynccontextmanager

from common.fastapi import create_fastapi_app
from fastapi import FastAPI

from .routers.captures import router as captures_router
from .settings import get_api_settings

settings = get_api_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Importing the DB connects to the DB, which we don't want to during openapi generation.
    if os.environ.get("DONT_IMPORT_DB") == "1":
        yield
    else:
        # Must import here so connection occurs after event loop is running
        from .db.conf import DB

        print("Starting DB connection pool...")
        await DB.start_connection_pool()
        print("DB connection pool started.")
        try:
            yield
        finally:
            await DB.close_connection_pool()


app = create_fastapi_app(
    title="Plerion API",
    lifespan=lifespan,
)

app.include_router(captures_router)
