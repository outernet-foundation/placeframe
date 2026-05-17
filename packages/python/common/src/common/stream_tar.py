from __future__ import annotations

import asyncio
import io
import os
import tarfile
import threading
from contextlib import nullcontext
from os import PathLike
from pathlib import Path
from typing import IO, TYPE_CHECKING, AsyncIterator, Callable, ContextManager, Protocol, cast

if TYPE_CHECKING:
    from _typeshed import ReadableBuffer


class _ChunkReader(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


class _ByteCounter(io.RawIOBase):
    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def writable(self) -> bool:
        return True

    def write(self, data: ReadableBuffer, /) -> int:
        length = memoryview(data).nbytes
        self.count += length
        return length

    def tell(self) -> int:
        return self.count


class _ZeroReader:
    def __init__(self, size: int) -> None:
        self._remaining = size

    def read(self, size: int = -1, /) -> bytes:
        if size < 0 or size > self._remaining:
            size = self._remaining
        self._remaining -= size
        return b"\x00" * size


def compute_tar_size(
    base: str | PathLike[str],
    exclude_suffixes: tuple[str, ...] = (),
) -> int:
    base_path = _resolve_capture_directory(base)
    counter = _ByteCounter()
    with tarfile.open(mode="w|", fileobj=counter) as tar_file:
        _emit_tar(
            tar_file,
            base_path,
            exclude_suffixes,
            lambda _path, info: nullcontext(_ZeroReader(info.size)),
        )
    return counter.count


def stream_tar(
    base: str | PathLike[str],
    exclude_suffixes: tuple[str, ...] = (),
) -> AsyncIterator[bytes]:
    base_path = _resolve_capture_directory(base)
    read_file_descriptor, write_file_descriptor = os.pipe()

    threading.Thread(
        target=_tar_producer, args=(write_file_descriptor, base_path, exclude_suffixes), daemon=True
    ).start()

    async def stream() -> AsyncIterator[bytes]:
        event_loop = asyncio.get_running_loop()
        with os.fdopen(read_file_descriptor, "rb", closefd=True) as reader:
            while True:
                data = await event_loop.run_in_executor(None, reader.read, 64 * 1024)
                if not data:
                    break
                yield data

    return stream()


def _tar_producer(write_file_descriptor: int, base_path: Path, exclude_suffixes: tuple[str, ...]) -> None:
    with (
        os.fdopen(write_file_descriptor, "wb", closefd=True) as writer,
        tarfile.open(mode="w|", fileobj=writer) as tar_file,
    ):
        _emit_tar(tar_file, base_path, exclude_suffixes, lambda path, _info: path.open("rb"))


def _emit_tar(
    tar_file: tarfile.TarFile,
    base_path: Path,
    exclude_suffixes: tuple[str, ...],
    open_data: Callable[[Path, tarfile.TarInfo], ContextManager[_ChunkReader]],
) -> None:
    for path in base_path.rglob("*"):
        if not path.is_file():
            continue
        if exclude_suffixes and path.suffix in exclude_suffixes:
            continue
        arcname = str(path.relative_to(base_path))
        tar_info = tar_file.gettarinfo(str(path), arcname=arcname)
        with open_data(path, tar_info) as data:
            tar_file.addfile(tar_info, cast("IO[bytes]", data))


def _resolve_capture_directory(base: str | PathLike[str]) -> Path:
    base_path = Path(base).resolve()
    if not base_path.is_dir():
        raise FileNotFoundError(f"{base_path} is not a directory")
    return base_path
