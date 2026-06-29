"""Structured logging configuration with channel-based rotation.

Channels:
  - app        : application lifecycle events, startup/shutdown
  - gateway    : REST API gateway activity
  - provider   : AI provider calls
  - request    : per-request access logs
  - health     : health check outcomes
"""
from __future__ import annotations
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.constants import (
    LOG_CHANNEL_APP,
    LOG_CHANNEL_GATEWAY,
    LOG_CHANNEL_HEALTH,
    LOG_CHANNEL_PROVIDER,
    LOG_CHANNEL_REQUEST,
)


def _ensure_dir(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _build_file_handler(channel: str, log_dir: Path, rotation: str, retention: int) -> logging.Handler:
    log_file = log_dir / f"{channel}.log"
    handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=_parse_size(rotation),
        backupCount=retention,
        encoding="utf-8",
        delay=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def _parse_size(size_str: str) -> int:
    """Parse '20 MB' / '1 GB' / '500 KB' into bytes; falls back to raw int."""
    s = size_str.strip().upper().replace(" ", "")
    units = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}
    for unit, mult in units.items():
        if s.endswith(unit):
            try:
                return int(float(s[: -len(unit)]) * mult)
            except ValueError:
                return 0
    try:
        return int(s)
    except ValueError:
        return 20 * 1024 * 1024


def _build_console_handler(fmt: str) -> logging.Handler:
    handler = logging.StreamHandler(sys.stderr)
    if fmt == "json":
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
    return handler


_configured = False


def configure_logging() -> None:
    """Initialise structured logging once at process start.

    Uses structlog on top of the stdlib logging module so we can route
    different "channels" to different rotating files.
    """
    global _configured
    if _configured:
        return
    settings = get_settings()
    log_dir = _ensure_dir(settings.logging.log_dir)

    level = getattr(logging, settings.general.log_level.upper(), logging.INFO)
    fmt = settings.logging.log_format
    rot = settings.logging.log_rotation
    ret = settings.logging.log_retention

    root = logging.getLogger()
    root.setLevel(level)
    # Clear pre-existing handlers (e.g. from pytest plugin or reload scenarios).
    for h in list(root.handlers):
        root.removeHandler(h)

    root.addHandler(_build_console_handler(fmt))

    # Channel loggers (each gets a rotating file).
    channel_names = [
        LOG_CHANNEL_APP,
        LOG_CHANNEL_GATEWAY,
        LOG_CHANNEL_PROVIDER,
        LOG_CHANNEL_REQUEST,
        LOG_CHANNEL_HEALTH,
    ]
    file_handler_by_channel: dict[str, logging.Handler] = {}
    for ch in channel_names:
        logger = logging.getLogger(f"aigateway.{ch}")
        logger.setLevel(level)
        logger.propagate = False
        for h in list(logger.handlers):
            logger.removeHandler(h)
        fh = _build_file_handler(ch, log_dir, rot, ret)
        logger.addHandler(fh)
        file_handler_by_channel[ch] = fh

    # Configure structlog with a simple processor chain.
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if fmt == "json":
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=[
            *shared_processors[:-1],
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(channel: str = LOG_CHANNEL_APP, name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger bound to the given channel."""
    if not _configured:
        configure_logging()
    full_name = name or channel
    return structlog.get_logger(f"aigateway.{channel}", full_name)


def get_channel_logger(channel: str) -> logging.Logger:
    """Return the underlying stdlib logger used for the given channel file."""
    if not _configured:
        configure_logging()
    return logging.getLogger(f"aigateway.{channel}")