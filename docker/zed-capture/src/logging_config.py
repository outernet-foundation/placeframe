import logging.config
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from tempfile import mkdtemp

from pythonjsonlogger.json import JsonFormatter

# Single source of truth for both the file the handler writes to and the file
# the GET /logs router reads back. Both must agree.
_default_log_dir = Path("/var/log/zed-capture")
_requested_log_dir = Path(environ.get("ZED_LOG_DIR", str(_default_log_dir)))


def _resolve_log_dir(requested: Path) -> Path:
    # Fall back to a tmp dir if the requested path isn't writable. Lets the
    # OpenAPI dump (which imports this module on a dev machine without /var
    # access) succeed without forcing every callsite to set ZED_LOG_DIR.
    try:
        requested.mkdir(parents=True, exist_ok=True)
        return requested
    except PermissionError:
        return Path(mkdtemp(prefix="zed-capture-logs-"))


def _resolve_box_id() -> str:
    # Box identity travels with every log record so the api relay can route
    # lines to the right Loki stream. The deploy layer sets ZED_BOX_ID from
    # the underlying hardware identity (e.g., /proc/device-tree/serial-number
    # on Jetson). Fail loudly when unset — a box that doesn't know who it is
    # shouldn't be writing to a shared log stream. CODEGEN imports the module
    # without a real deployment, so allow a placeholder there.
    box_id = environ.get("ZED_BOX_ID")
    if box_id:
        return box_id
    if environ.get("CODEGEN"):
        return "codegen-placeholder"
    raise RuntimeError(
        "ZED_BOX_ID is required but unset; the deploy layer must export it from the box's hardware serial"
    )


# Module-level dictConfig call. Imported by src/__init__.py so logging is set
# up before any other application module (including litestar) is imported and
# acquires loggers. Don't pass --log-config to uvicorn — Litestar's default
# LoggingConfig runs second and would clobber our handlers (replaces root with
# its own QueueHandler). create_litestar_app() is called with logging_config=None
# so Litestar leaves what we set up here alone.
LOG_DIR = _resolve_log_dir(_requested_log_dir)
LOG_FILE_NAME = "app.jsonl"
BOX_ID = _resolve_box_id()

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,
            "format": "%(levelname)s %(name)s %(message)s",
            "rename_fields": {"levelname": "level"},
            "timestamp": True,
            "static_fields": {"box_id": BOX_ID},
        },
    },
    "handlers": {
        "file": {
            "()": RotatingFileHandler,
            "formatter": "json",
            "filename": str(LOG_DIR / LOG_FILE_NAME),
            "maxBytes": 50 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "stream": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["file", "stream"],
        "level": "INFO",
    },
    "loggers": {
        "uvicorn": {"handlers": ["file", "stream"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["file", "stream"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["file", "stream"], "level": "INFO", "propagate": False},
    },
})
