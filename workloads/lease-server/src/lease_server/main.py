from placeframe_common.litestar import create_litestar_app
from placeframe_common.logging_config import configure_logging
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server

from .routers.leases import router as leases_router
from .routers.queue_state import router as queue_state_router

configure_logging("lease-server")

openapi_config = OpenAPIConfig("Placeframe Lease Server", "0.1.0", servers=[Server(url="http://lease-server:8000")])

app = create_litestar_app([leases_router, queue_state_router], openapi_config, logging_config=None)
