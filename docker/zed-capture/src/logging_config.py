from os import environ
from pathlib import Path

from common.logging_config import configure_logging

# Module-level invocation. Imported by src/__init__.py so logging is set up
# before any other application module (including litestar) is imported and
# acquires loggers. Don't pass --log-config to uvicorn — Litestar's default
# LoggingConfig runs second and would clobber our handlers (replaces root with
# its own QueueHandler). create_litestar_app() is called with logging_config=None
# so Litestar leaves what we set up here alone.
_log_directory = Path(environ.get("ZED_LOG_DIR", "/var/log/zed-capture"))
LOG_FILE_NAME = "app.jsonl"
LOG_FILE_PATH = configure_logging(
    "zed-capture",
    instance_id=environ.get("ZED_BOX_ID"),
    log_file_path=_log_directory / LOG_FILE_NAME,
    uvicorn_logger_handlers=True,
)
