import logging
import logging.config
import os
import socket
import sys
from pathlib import Path
from tempfile import mkdtemp

from opentelemetry._logs import set_logger_provider  # noqa: PLC2701
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter  # noqa: PLC2701
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler  # noqa: PLC2701
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor  # noqa: PLC2701
from opentelemetry.sdk.resources import Resource

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

_SERVICE_NAMESPACE = "placeframe"


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


def _resolve_log_file_path(requested: Path) -> Path:
    # Fall back to a tmp dir if the requested path isn't writable. Lets the
    # OpenAPI dump (which imports modules on a dev machine without /var access)
    # succeed without forcing every callsite to set an override.
    try:
        requested.parent.mkdir(parents=True, exist_ok=True)
        return requested
    except PermissionError:
        return Path(mkdtemp(prefix=f"{requested.stem}-logs-")) / requested.name


def _build_resource(service_name: str, instance_id: str) -> Resource:
    return Resource.create({
        "service.name": service_name,
        "service.namespace": _SERVICE_NAMESPACE,
        "service.instance.id": instance_id,
        "service.version": os.environ.get("SERVICE_VERSION", "unknown"),
        "deployment.environment.name": os.environ.get("DEPLOYMENT_ENVIRONMENT", "development"),
        "container.name": os.environ.get("HOSTNAME", instance_id),
    })


def _build_otlp_handler(resource: Resource, endpoint: str) -> LoggingHandler:
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True)))
    set_logger_provider(provider)
    return LoggingHandler(level=logging.NOTSET, logger_provider=provider)


def configure_logging(
    service_name: str,
    instance_id: str | None = None,
    log_file_path: Path | None = None,
    uvicorn_logger_handlers: bool = False,
) -> Path | None:
    instance_id = instance_id or socket.gethostname()
    resource = _build_resource(service_name, instance_id)

    handlers: dict[str, dict[str, object]] = {
        "stream": {
            "class": "logging.StreamHandler",
            "formatter": "human",
            "stream": sys.stderr,
        },
    }
    handler_names = ["stream"]

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        handlers["otlp"] = {
            "()": lambda res=resource, ep=otlp_endpoint: _build_otlp_handler(res, ep),
        }
        handler_names.append("otlp")

    resolved_log_file_path: Path | None = None
    if log_file_path is not None:
        resolved_log_file_path = _resolve_log_file_path(log_file_path)
        handlers["file"] = {
            "()": "logging.handlers.RotatingFileHandler",
            "formatter": "human",
            "filename": str(resolved_log_file_path),
            "maxBytes": 50 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        }
        handler_names.append("file")

    loggers: dict[str, dict[str, object]] = {}
    if uvicorn_logger_handlers:
        for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
            loggers[name] = {"handlers": handler_names, "level": "INFO", "propagate": False}

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "human": {"()": HumanFormatter},
        },
        "handlers": handlers,
        "root": {"handlers": handler_names, "level": "INFO"},
        "loggers": loggers,
    })

    return resolved_log_file_path
