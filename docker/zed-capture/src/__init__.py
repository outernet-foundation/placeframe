# ruff: noqa: RUF067 — this init imports logging_config for its module-level configure_logging side effect, which must run before any application module (Litestar) acquires loggers; the package init is the only Python hook that fires before submodule imports
from . import logging_config as logging_config
