"""
Core module - shared utilities and infrastructure.
"""

from core.logging import (
    get_logger,
    logger,
    setup_logging,
    get_trace_id,
    set_trace_id,
    reset_trace_id,
    CrawlLogger,
)

__all__ = [
    "get_logger",
    "logger",
    "setup_logging",
    "get_trace_id",
    "set_trace_id",
    "reset_trace_id",
    "CrawlLogger",
]
