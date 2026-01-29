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

from common.fastapi import create_fastapi_app

from .routers.captures import router as captures_router

app = create_fastapi_app("Zed API")

app.include_router(captures_router)
