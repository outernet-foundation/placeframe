from __future__ import annotations

from pathlib import Path

from logconf import configure_logging as _configure_logging


def configure_logging(
    service_name: str,
    *,
    instance_id: str | None = None,
    log_file_path: Path | None = None,
    uvicorn_logger_handlers: bool = False,
) -> Path | None:
    return _configure_logging(
        service_name,
        service_namespace="placeframe",
        instance_id=instance_id,
        log_file_path=log_file_path,
        uvicorn_logger_handlers=uvicorn_logger_handlers,
    )
