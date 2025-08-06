import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from mangum import Mangum

from .routers.captures import router as captures_router
from .settings import get_settings

print("Starting API...")
settings = get_settings()
print("Settings loaded.")


# Make codegened client functions use the same name as their corresponding server functions
def use_handler_name(route: APIRoute) -> str:
    return route.name


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


app = FastAPI(
    title="Plerion API",
    version="0.0.1",
    generate_unique_id_function=use_handler_name,
    lifespan=lifespan,
    docs_url=None,  # ← disable the built-in Swagger UI at /docs
    redoc_url=None,  # ← disable the built-in Redoc at /redoc
)


# Custom Swagger UI to add add -L to curl commands so they follow redirects
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    orig_resp: HTMLResponse = get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} – Swagger UI",
    )
    body_bytes = bytes(orig_resp.body)
    raw_html = body_bytes.decode("utf-8")

    modified_html = raw_html.replace(
        "SwaggerUIBundle({",
        """SwaggerUIBundle({
             requestInterceptor: (req) => {
               req.curlOptions = ['-L'];
               return req;
             },""",
    )

    # copy all headers *except* the old Content-Length
    filtered_headers = {
        k: v for k, v in orig_resp.headers.items() if k.lower() != "content-length"
    }

    return HTMLResponse(
        content=modified_html,
        status_code=orig_resp.status_code,
        headers=filtered_headers,
    )


handler = Mangum(app)

app.include_router(captures_router)
