from logging import getLogger
from typing import Any, Sequence, cast

from litestar import Litestar, Request, Response, get
from litestar.exceptions import HTTPException, ValidationException
from litestar.handlers import HTTPRouteHandler
from litestar.logging import BaseLoggingConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Schema
from litestar.openapi.spec.enums import OpenAPIFormat, OpenAPIType
from litestar.plugins import OpenAPISchemaPlugin
from litestar.response import Redirect
from litestar.types import ControllerRouterHandler, Method, Middleware, Empty, EmptyType
from litestar.types.internal_types import PathParameterDefinition
from litestar.typing import FieldDefinition

logger = getLogger("uvicorn.error")


class FloatFormatPlugin(OpenAPISchemaPlugin):
    # OpenAPIFormat enum has no DOUBLE member but Schema.format serializes any
    # string subclass; cast satisfies the static type and emits "format": "double".
    _DOUBLE_FORMAT = cast(OpenAPIFormat, "double")

    @staticmethod
    def is_plugin_supported_type(value: Any) -> bool:
        return value is float

    def is_plugin_supported_field(self, field_definition: FieldDefinition) -> bool:
        return field_definition.annotation is float

    def to_openapi_schema(self, field_definition: FieldDefinition, schema_creator: Any) -> Schema:
        return Schema(type=OpenAPIType.NUMBER, format=self._DOUBLE_FORMAT)


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
    # Default Empty preserves Litestar's auto-LoggingConfig behavior for callers
    # that haven't configured logging themselves (api, localizer). Pass None to
    # opt out — required when the caller has already called dictConfig() and
    # would have its handlers clobbered by Litestar's default queue-based setup.
    logging_config: BaseLoggingConfig | EmptyType | None = Empty,
) -> Litestar:
    openapi_config.operation_id_creator = use_handler_name

    return Litestar(
        [root, health_check, *route_handlers],
        openapi_config=openapi_config,
        middleware=middleware,
        request_max_body_size=1024 * 1024 * 1024,
        exception_handlers={HTTPException: log_http_exception, Exception: log_unhandled_exception},
        logging_config=logging_config,
        plugins=[FloatFormatPlugin()],
    )
