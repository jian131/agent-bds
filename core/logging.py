"""
Structured logging configuration with trace_id support.
Provides JSON logging for production and human-readable for development.
"""

import sys
import uuid
import logging
from typing import Any
from contextvars import ContextVar
from datetime import datetime

import structlog
from structlog.types import Processor

from config import settings

# Context variable for request trace_id
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    """Get current trace_id or generate new one."""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]
        trace_id_var.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set trace_id for current context."""
    trace_id_var.set(trace_id)


def reset_trace_id() -> str:
    """Reset and return new trace_id."""
    trace_id = str(uuid.uuid4())[:8]
    trace_id_var.set(trace_id)
    return trace_id


def add_trace_id(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Processor to add trace_id to log events."""
    event_dict["trace_id"] = get_trace_id()
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Processor to add ISO timestamp."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Processor to add service metadata."""
    event_dict["service"] = "bds-agent"
    event_dict["env"] = settings.app_env
    return event_dict


def setup_logging() -> None:
    """Configure structured logging based on environment."""

    # Shared processors
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_timestamp,
        add_trace_id,
        add_service_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.app_env == "production":
        # JSON logging for production
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Human-readable for development
        shared_processors.append(structlog.dev.set_exc_info)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Reduce noise from third-party libraries
    for logger_name in ["httpx", "httpcore", "asyncio", "urllib3", "chromadb"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Convenience logger instance
logger = get_logger("bds-agent")


class CrawlLogger:
    """Specialized logger for crawling operations."""

    def __init__(self, platform: str):
        self.platform = platform
        self._logger = get_logger(f"crawler.{platform}")

    def info(self, event: str, **kwargs):
        self._logger.info(event, platform=self.platform, **kwargs)

    def error(self, event: str, **kwargs):
        self._logger.error(event, platform=self.platform, **kwargs)

    def warning(self, event: str, **kwargs):
        self._logger.warning(event, platform=self.platform, **kwargs)

    def crawl_start(self, url: str):
        self._logger.info(
            "crawl_start",
            platform=self.platform,
            url=url,
            action="crawl_start"
        )

    def crawl_success(self, url: str, items_count: int, latency_ms: float):
        self._logger.info(
            "crawl_success",
            platform=self.platform,
            url=url,
            action="crawl_success",
            items_count=items_count,
            latency_ms=round(latency_ms, 2)
        )

    def crawl_error(self, url: str, error_type: str, error_msg: str, status_code: int = None):
        self._logger.error(
            "crawl_error",
            platform=self.platform,
            url=url,
            action="crawl_error",
            error_type=error_type,
            error_msg=error_msg,
            status_code=status_code
        )

    def crawl_blocked(self, url: str, status_code: int = 403):
        self._logger.warning(
            "crawl_blocked",
            platform=self.platform,
            url=url,
            action="crawl_blocked",
            status_code=status_code,
            error_type="blocked"
        )

    def rate_limited(self, url: str, retry_after: int = None):
        self._logger.warning(
            "rate_limited",
            platform=self.platform,
            url=url,
            action="rate_limited",
            retry_after=retry_after
        )
