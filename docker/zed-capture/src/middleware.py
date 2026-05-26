import time
import uuid
from logging import getLogger
from typing import cast

from litestar.enums import ScopeType
from litestar.middleware import ASGIMiddleware
from litestar.types import ASGIApp, HTTPScope, Message, Receive, Scope, Send

logger = getLogger("zed-capture.access")


class RequestIdMiddleware(ASGIMiddleware):
    scopes = (ScopeType.HTTP,)

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        http_scope = cast("HTTPScope", scope)
        request_id = next(
            (value.decode("latin-1") for name, value in http_scope["headers"] if name == b"x-request-id"),
            uuid.uuid4().hex,
        )
        start = time.monotonic()
        response_status = 0

        # Entry log lets us tell a request that never reached uvicorn (e.g.
        # stuck somewhere between Caddy and the ASGI app) from one that
        # reached uvicorn but hung in the handler — without it, a stalled
        # request emits no log line at all until it completes or errors.
        logger.info(
            "req id=%s %s %s started",
            request_id,
            http_scope["method"],
            http_scope["path"],
        )

        async def send_with_header(message: Message) -> None:
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
                headers = list(message["headers"])
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await next_app(scope, receive, send_with_header)
        finally:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "req id=%s %s %s completed status=%d %dms",
                request_id,
                http_scope["method"],
                http_scope["path"],
                response_status,
                elapsed_ms,
            )
