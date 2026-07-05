"""
Structured logging configuration.

Uses Python's standard logging module with JSON-friendly formatting.
Log level is driven by the APP environment variable.
"""
from __future__ import annotations

import logging
import sys
from typing import Any


class _PrefixFormatter(logging.Formatter):
    """Formatter that prefixes log records with a structured tag."""

    LEVEL_EMOJIS: dict[str, str] = {
        "DEBUG": "🔍",
        "INFO": "ℹ️ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "CRITICAL": "🔥",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        emoji = self.LEVEL_EMOJIS.get(record.levelname, "")
        record.msg = f"{emoji} [{record.name}] {record.msg}"
        return super().format(record)


def configure_logging(level: str = "INFO") -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = _PrefixFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove duplicate handlers on reconfiguration
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # Silence noisy third-party loggers in production
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
