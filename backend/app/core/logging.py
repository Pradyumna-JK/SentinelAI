"""Structured logging configuration built on structlog.

One pipeline formats everything — structlog loggers *and* stdlib loggers
(uvicorn, sqlalchemy, alembic) — so every line the process emits has the
same shape. Output is JSON in deployed environments (machine-parseable for
Loki/CloudWatch/Datadog) and a human-readable console renderer during local
development. Selection is driven by Settings, never hardcoded.
"""

import logging
import sys

import structlog

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # Applied to structlog-native log calls AND to stdlib records passing
    # through the ProcessorFormatter, so both end up with identical fields.
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if settings.log_json_resolved:
        final_processors = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # ConsoleRenderer pretty-prints exceptions itself; format_exc_info
        # must not run first or tracebacks render twice.
        final_processors = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ]

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=final_processors,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())

    # Our RequestLoggingMiddleware replaces uvicorn's access log with a
    # structured equivalent (request id, latency, client), so silence the
    # built-in one instead of double-logging every request.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
