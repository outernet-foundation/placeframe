from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.routing import APIRoute
from starlette.types import StatefulLifespan, StatelessLifespan


# Make codegened client functions use the same name as their corresponding server functions
def use_handler_name(route: APIRoute) -> str:
    return route.name


def create_fastapi_app(
    title: str, lifespan: StatelessLifespan[FastAPI] | StatefulLifespan[FastAPI] | None
) -> FastAPI:
    app = FastAPI(
        title=title,
        lifespan=lifespan,
        generate_unique_id_function=use_handler_name,
        docs_url=None,
        redoc_url=None,
    )

    async def root():
        return RedirectResponse(url="/docs")

    async def health():
        return PlainTextResponse("ok")

    # Custom Swagger UI to add add -L to curl commands so they follow redirects
    async def docs():
        orig_resp = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} – Swagger UI",
        )

        return HTMLResponse(
            content=bytes(orig_resp.body)
            .decode("utf-8")
            .replace(
                "SwaggerUIBundle({",
                """SwaggerUIBundle({
                requestInterceptor: (req) => {
                req.curlOptions = ['-L'];
                return req;
                },""",
            ),
            status_code=orig_resp.status_code,
            headers={
                k: v
                for k, v in orig_resp.headers.items()
                if k.lower() != "content-length"
            },
        )

    app.add_api_route("/", root, include_in_schema=False, methods=["GET"])

    app.add_api_route(
        "/health",
        health,
        include_in_schema=False,
        methods=["GET"],
    )

    app.add_api_route("/docs", docs, include_in_schema=False, methods=["GET"])

    return app
