from __future__ import annotations

import asyncio
import os
import tarfile
import threading
from os import PathLike
from pathlib import Path
from typing import AsyncIterator


def stream_tar(base: str | PathLike[str]) -> AsyncIterator[bytes]:
    base_path = Path(base).resolve()
    if not base_path.is_dir():
        raise FileNotFoundError(f"{base_path} is not a directory")

    read_file_descriptor, write_file_descriptor = os.pipe()

    def producer() -> None:
        try:
            with (
                os.fdopen(write_file_descriptor, "wb", closefd=True) as writer,
                tarfile.open(mode="w|", fileobj=writer) as tar_file,
            ):
                for path in base_path.rglob("*"):
                    if not path.is_file():
                        continue
                    tar_info = tar_file.gettarinfo(
                        str(path), arcname=str(path.relative_to(base_path))
                    )
                    with path.open("rb") as file_object:
                        tar_file.addfile(tar_info, file_object)
        finally:
            try:
                os.close(write_file_descriptor)
            except OSError:
                pass

    threading.Thread(target=producer, daemon=True).start()

    async def stream() -> AsyncIterator[bytes]:
        event_loop = asyncio.get_running_loop()
        with os.fdopen(read_file_descriptor, "rb", closefd=True) as reader:
            while True:
                data = await event_loop.run_in_executor(None, reader.read, 64 * 1024)
                if not data:
                    break
                yield data

    return stream()
