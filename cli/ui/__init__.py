"""CLI UI components package"""
from cli.ui.console import get_console, reset_console
from cli.ui.progress import create_progress, ProgressTracker
from cli.ui.formatter import (
    format_number,
    format_percent,
    format_date,
    format_datetime,
    colorize_status,
    format_currency,
)
from cli.ui.menu import InteractiveMenu, MenuOption, MenuResult
from cli.ui.status import StatusMonitor, SystemInfo, APIRateLimitStatus
from cli.ui.table import TableRenderer
from cli.ui.validators import StockCodeValidator, DateValidator, NumberValidator

__all__ = [
    # Console & Progress
    "get_console",
    "reset_console",
    "create_progress",
    "ProgressTracker",
    # Formatters
    "format_number",
    "format_percent",
    "format_date",
    "format_datetime",
    "colorize_status",
    "format_currency",
    # Interactive Menu
    "InteractiveMenu",
    "MenuOption",
    "MenuResult",
    # Status Monitoring
    "StatusMonitor",
    "SystemInfo",
    "APIRateLimitStatus",
    # Table Rendering
    "TableRenderer",
    # Input Validators
    "StockCodeValidator",
    "DateValidator",
    "NumberValidator",
]
