import os
import sys

if sys.platform == "win32":
    # Adjust these paths to your install:
    zed_bin = r"C:\\Program Files (x86)\\ZED SDK\\bin"
    cuda_bin = r"C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.0\\bin"  # or your CUDA version
    msvc_dir = r"C:\\Windows\\System32"  # MSVC runtime normally here

    for p in (zed_bin, cuda_bin, msvc_dir):
        if os.path.isdir(p):
            os.add_dll_directory(p)

from common.litestar import create_litestar_app
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from .middleware import RequestIdMiddleware
from .routers.captures import router as captures_router
from .routers.logs import router as logs_router
from .routers.status import router as status_router

openapi_config = OpenAPIConfig("Zed API", "0.1.0", render_plugins=[ScalarRenderPlugin()])

# logging_config=None opts out of Litestar's default LoggingConfig, which would
# call dictConfig with its own QueueHandler-based setup and clobber the handlers
# installed by src/__init__.py importing src.logging_config.
app = create_litestar_app(
    [captures_router, status_router, logs_router],
    openapi_config,
    logging_config=None,
    middleware=[RequestIdMiddleware()],
)
