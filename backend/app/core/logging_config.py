"""
Phase 11.6 — Structured logging configuration
core/logging.py
"""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the CricketIQ AI backend.

    Call this once at application startup via the lifespan handler.
    Sets consistent format across all loggers including uvicorn,
    SQLAlchemy, and application-level loggers.
    """

    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt   = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S"
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Remove existing handlers to avoid duplicate logs
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)

    # App loggers at INFO level
    for logger_name in [
        "app.agents",
        "app.rag",
        "app.nlp",
        "app.services",
        "app.llm",
    ]:
        logging.getLogger(logger_name).setLevel(level)

    logging.getLogger(__name__).info(
        "Logging configured — level: %s", log_level
    )