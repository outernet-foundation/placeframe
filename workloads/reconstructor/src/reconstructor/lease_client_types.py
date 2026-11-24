# wrapper (noqa-wrapper): the generated lease-server client's ApiException leaves status and body unannotated, so reading them typed requires a suppression boundary

from __future__ import annotations

from placeframe_lease_server_client import ApiException


def api_exception_status(exception: ApiException) -> int | None:
    status = exception.status  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return status if isinstance(status, int) else None


def api_exception_body(exception: ApiException) -> str | None:
    body = exception.body  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return body if isinstance(body, str) else None
