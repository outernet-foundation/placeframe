from common.litestar import create_litestar_app
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server

from .routers.leases import router as leases_router

openapi_config = OpenAPIConfig("Placeframe Lease Server", "0.1.0", servers=[Server(url="http://lease-server:8000")])

app = create_litestar_app([leases_router], openapi_config)
