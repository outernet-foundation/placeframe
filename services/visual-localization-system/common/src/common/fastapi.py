import logging
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.applications import get_swagger_ui_oauth2_redirect_html
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.routing import APIRoute
from starlette.responses import Response
from starlette.types import StatefulLifespan, StatelessLifespan


# Make codegened client functions use the same name as their corresponding server functions
def use_handler_name(route: APIRoute) -> str:
    return route.name


def create_fastapi_app(
    title: str,
    lifespan: StatelessLifespan[FastAPI] | StatefulLifespan[FastAPI] | None = None,
    client_id: str | None = None,
) -> FastAPI:
    app = FastAPI(
        title=title,
        lifespan=lifespan,
        generate_unique_id_function=use_handler_name,
        docs_url=None,
        redoc_url=None,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    logger = logging.getLogger("uvicorn.error")

    async def log_http_exception(request: Request, exc: Exception) -> Response:
        http_exc = cast(HTTPException, exc)
        logger.warning(
            "HTTPException %s on %s %s: %r", http_exc.status_code, request.method, request.url.path, http_exc.detail
        )
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"detail": http_exc.detail},
            headers=getattr(http_exc, "headers", None),
        )

    async def log_unhandled_exception(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    async def root():
        return RedirectResponse(url="/docs")

    async def health():
        return PlainTextResponse("ok")

    async def docs():
        original_html_response = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} – Swagger UI",
            oauth2_redirect_url="/docs/oauth2-redirect",
            init_oauth={"clientId": client_id, "usePkceWithAuthorizationCodeGrant": True} if client_id else None,
        )

        # Custom Swagger UI to add add -L to curl commands so they follow redirects
        return HTMLResponse(
            content=bytes(original_html_response.body)
            .decode("utf-8")
            .replace(
                "SwaggerUIBundle({",
                """SwaggerUIBundle({
                requestInterceptor: (req) => {
                req.curlOptions = ['-L'];
                return req;
                },""",
            ),
            status_code=original_html_response.status_code,
            headers={k: v for k, v in original_html_response.headers.items() if k.lower() != "content-length"},
        )

    # Because we overrode the docs route, we need to add back the oauth2 redirect route
    async def oauth2_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    app.add_exception_handler(HTTPException, log_http_exception)
    app.add_exception_handler(Exception, log_unhandled_exception)
    app.add_api_route("/", root, include_in_schema=False, methods=["GET"])
    app.add_api_route("/health", health, include_in_schema=False, methods=["GET"])
    app.add_api_route("/docs", docs, include_in_schema=False, methods=["GET"])
    app.add_api_route("/docs/oauth2-redirect", oauth2_redirect, include_in_schema=False, methods=["GET"])

    return app
