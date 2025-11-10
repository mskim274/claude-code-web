"""Rich-integrated logging utilities"""
import logging
from typing import Optional
from rich.logging import RichHandler
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rich_tracebacks: bool = True,
) -> None:
    """
    Setup logging with Rich handler.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        rich_tracebacks: Enable rich tracebacks
    """
    handlers = []

    # Rich console handler
    rich_handler = RichHandler(
        rich_tracebacks=rich_tracebacks,
        markup=True,
        show_time=True,
        show_path=True,
    )
    handlers.append(rich_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
