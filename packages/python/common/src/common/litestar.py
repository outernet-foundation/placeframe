from logging import getLogger
from typing import Any, Sequence

from litestar import Litestar, Request, Response, get
from litestar.exceptions import HTTPException, ValidationException
from litestar.handlers import HTTPRouteHandler
from litestar.openapi.config import OpenAPIConfig
from litestar.response import Redirect
from litestar.types import ControllerRouterHandler, Method, Middleware
from litestar.types.internal_types import PathParameterDefinition

logger = getLogger("uvicorn.error")


# Make codegened client functions use the same name as their corresponding server functions
def use_handler_name(
    route_handler: HTTPRouteHandler, http_method: Method, path_components: list[str | PathParameterDefinition]
) -> str:
    return route_handler.handler_name


def log_http_exception(request: Request[Any, Any, Any], exception: HTTPException) -> Response[dict[str, Any]]:
    # Server Errors
    if exception.status_code >= 500:
        logger.exception(
            "HTTPException %s on %s %s: %r",
            exception.status_code,
            request.method,
            request.url.path,
            exception.detail,
            exc_info=exception,
        )

        return Response(content={"detail": "Internal Server Error"}, status_code=exception.status_code)

    # Client Errors
    logger.info(
        "HTTPException %s on %s %s: %r", exception.status_code, request.method, request.url.path, exception.detail
    )

    content: dict[str, Any] = {"detail": exception.detail}

    if isinstance(exception, ValidationException) and exception.extra:
        content["validation_errors"] = exception.extra

    return Response(content=content, status_code=exception.status_code)


def log_unhandled_exception(request: Request[Any, Any, Any], exception: Exception) -> Response[dict[str, Any]]:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exception)

    return Response(content={"detail": "Internal Server Error"}, status_code=500)


@get("/", include_in_schema=False)
async def root() -> Redirect:
    return Redirect(path="/schema")


@get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


def create_litestar_app(
    route_handlers: Sequence[ControllerRouterHandler],
    openapi_config: OpenAPIConfig,
    middleware: Sequence[Middleware] | None = None,
) -> Litestar:
    openapi_config.operation_id_creator = use_handler_name

    return Litestar(
        [root, health_check, *route_handlers],
        openapi_config=openapi_config,
        middleware=middleware,
        request_max_body_size=1024 * 1024 * 1024,
        exception_handlers={HTTPException: log_http_exception, Exception: log_unhandled_exception},
    )
