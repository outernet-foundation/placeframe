import logging.config
from logging.handlers import RotatingFileHandler
from os import environ
from pathlib import Path
from tempfile import mkdtemp

from pythonjsonlogger.json import JsonFormatter

# Single source of truth for the file the handler writes to.
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


# Module-level dictConfig call. Imported by src/__init__.py so logging is set
# up before any other application module (including litestar) is imported and
# acquires loggers. Don't pass --log-config to uvicorn — Litestar's default
# LoggingConfig runs second and would clobber our handlers (replaces root with
# its own QueueHandler). create_litestar_app() is called with logging_config=None
# so Litestar leaves what we set up here alone.
LOG_DIR = _resolve_log_dir(_requested_log_dir)
LOG_FILE_NAME = "app.jsonl"

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,
            "format": "%(levelname)s %(name)s %(message)s",
            "rename_fields": {"levelname": "level"},
            "timestamp": True,
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
