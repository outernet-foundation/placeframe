from asyncio import to_thread

from docker import from_env
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server
from placeframe_common.litestar import create_litestar_app
from placeframe_common.logging_config import configure_logging

from .docker_lifecycle import ModeSwitcher, compose_project_of
from .routers.mode import router as mode_router
from .settings import get_settings

configure_logging("mode-switcher")

openapi_config = OpenAPIConfig(
    "Placeframe Mode Switcher",
    "0.1.0",
    servers=[Server(url="http://mode-switcher:8000")],
)


async def bootstrap(app: Litestar) -> None:
    client = from_env()
    switcher = ModeSwitcher(client, get_settings().default_mode, compose_project_of(client))
    await to_thread(switcher.reconcile)
    app.state.mode_switcher = switcher


app = create_litestar_app([mode_router], openapi_config, logging_config=None)
app.on_startup.append(bootstrap)
