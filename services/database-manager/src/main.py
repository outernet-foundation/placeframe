from common.fastapi import create_fastapi_app

from .routers.databases import router as databases_router

app = create_fastapi_app(title="Database Manager")

app.include_router(databases_router)
