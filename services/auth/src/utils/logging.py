"""
Structured logging for the auth service.

Mirrors the file service's configuration so operators can correlate
logs across the two.  ``request_id`` is propagated through the
:mod:`src.middleware.request_id` middleware.
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
    if "request_id" in event_dict and event_dict["request_id"] is None:
        event_dict.pop("request_id", None)
    return event_dict


def configure_logging(*, env: str, level: str = "INFO") -> None:
    """Wire up structlog + stdlib ``logging`` to share one output pipeline."""
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

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processor=renderer,
    ))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level))

    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING if is_production else logging.INFO)


def get_logger(name: str | None = None) -> BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()


__all__ = [
    "bind_contextvars",
    "clear_contextvars",
    "configure_logging",
    "get_logger",
    "request_id_var",
]
