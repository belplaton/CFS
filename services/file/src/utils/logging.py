"""
Structured logging for the file service.

Phase 2: ``structlog`` is configured once at startup.  Every log line is
emitted as JSON in production (``settings.env == "production"``) or as a
human-friendly key/value stream in development.  A ``request_id`` is
propagated through the request via a ``ContextVar`` (see the middleware
in :mod:`src.middleware.request_id`).
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
    format_exc_info,
)
from structlog.stdlib import BoundLogger, ProcessorFormatter
from structlog.types import EventDict, Processor

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def _drop_request_id(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Allow log calls to override ``request_id`` via ``request_id=...`` kwarg."""
    if "request_id" in event_dict and event_dict["request_id"] is None:
        event_dict.pop("request_id", None)
    return event_dict


def configure_logging(*, env: str, level: str = "INFO") -> None:
    """
    Wire up structlog + stdlib ``logging`` to use the same JSON/console
    output and ensure ``uvicorn`` / ``sqlalchemy`` loggers flow through
    the same pipeline.

    Call once at application startup (from ``main.py``).
    """
    is_production = env.lower() == "production"

    shared_processors: list[Processor] = [
        merge_contextvars,
        _drop_request_id,
        add_log_level,
        TimeStamper(fmt="iso", utc=True),
        StackInfoRenderer(),
        format_exc_info,
    ]

    if is_production:
        renderer: Processor = JSONRenderer(sort_keys=True)
    else:
        renderer = ConsoleRenderer(colors=sys.stderr.isatty())

    # structlog: bypass the stdlib formatter so we can render the final line.
    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # stdlib: route logs through the same processors so uvicorn/sqlalchemy
    # messages look the same.  We do this by attaching a
    # ProcessorFormatter to the root handler.
    formatter = ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processor=renderer,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level))

    # Quiet down chatty third parties a touch in development.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING if is_production else logging.INFO
        )


def get_logger(name: str | None = None) -> BoundLogger:
    """Return a bound structlog logger (use this instead of stdlib ``getLogger``)."""
    return structlog.get_logger(name) if name else structlog.get_logger()


__all__ = [
    "bind_contextvars",
    "clear_contextvars",
    "configure_logging",
    "get_logger",
    "request_id_var",
]
