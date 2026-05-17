import logging
import logging.config
import sys
from pathlib import Path

_STANDARD_LOG_RECORD_ATTRS = frozenset({
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
})


# Stream handler for the human at the terminal. Renders one line per record:
# `HH:MM:SS [level] event key=value key=value`. Extras passed via `extra={...}`
# in the log call get rendered as trailing key=value pairs.
class HumanFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%H:%M:%S")
        base = f"{timestamp} [{record.levelname.lower()}] {record.getMessage()}"
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_RECORD_ATTRS and not key.startswith("_")
        }
        if not extras:
            return base
        rendered_extras = " ".join(f"{key}={value}" for key, value in extras.items())
        return f"{base} {rendered_extras}"


def configure_logging(service_name: str, log_directory: Path | None = None) -> None:
    log_directory = log_directory or Path.cwd() / ".placeframe" / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / f"{service_name}.jsonl"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(levelname)s %(name)s %(message)s",
                "rename_fields": {"levelname": "level"},
                "timestamp": True,
                "static_fields": {"service": service_name},
            },
            "human": {
                "()": HumanFormatter,
            },
        },
        "handlers": {
            "file": {
                "()": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": str(log_file),
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
            "stream": {
                "class": "logging.StreamHandler",
                "formatter": "human",
                "stream": sys.stderr,
            },
        },
        "root": {
            "handlers": ["file", "stream"],
            "level": "INFO",
        },
    })
