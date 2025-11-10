"""Output formatting utilities"""
from datetime import date, datetime
from typing import Union
from rich.text import Text


def format_number(value: Union[int, float], decimals: int = 0) -> str:
    """
    Format number with thousands separator.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted number string

    Example:
        >>> format_number(1000)
        '1,000'
        >>> format_number(1234.5678, decimals=2)
        '1,234.57'
    """
    return f"{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 2) -> str:
    """
    Format decimal as percentage.

    Args:
        value: Decimal value (e.g., 0.125 for 12.5%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string

    Example:
        >>> format_percent(0.125)
        '12.50%'
        >>> format_percent(0.5, decimals=1)
        '50.0%'
    """
    return f"{value * 100:.{decimals}f}%"


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """
    Format date.

    Args:
        d: Date object
        fmt: Format string

    Returns:
        Formatted date string

    Example:
        >>> format_date(date(2024, 1, 15))
        '2024-01-15'
    """
    return d.strftime(fmt)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime.

    Args:
        dt: Datetime object
        fmt: Format string

    Returns:
        Formatted datetime string

    Example:
        >>> format_datetime(datetime(2024, 1, 15, 10, 30, 45))
        '2024-01-15 10:30:45'
    """
    return dt.strftime(fmt)


def colorize_status(status: str, message: str) -> Text:
    """
    Colorize status message.

    Args:
        status: Status type (success, error, warning, info)
        message: Message text

    Returns:
        Rich Text object with color

    Example:
        >>> colorize_status("success", "Operation completed")
        <Text with green color>
    """
    colors = {
        "success": "green",
        "error": "red",
        "warning": "yellow",
        "info": "blue",
    }
    color = colors.get(status.lower(), "white")
    return Text(f"[{status.upper()}] {message}", style=color)


def format_currency(value: Union[int, float], currency: str = "KRW") -> str:
    """
    Format currency value.

    Args:
        value: Amount
        currency: Currency code (KRW, USD, etc.)

    Returns:
        Formatted currency string

    Example:
        >>> format_currency(1000000, currency="KRW")
        '₩1,000,000'
        >>> format_currency(1234.56, currency="USD")
        '$1,234.56'
    """
    symbols = {
        "KRW": "₩",
        "USD": "$",
        "EUR": "€",
        "JPY": "¥",
    }
    symbol = symbols.get(currency.upper(), currency)

    if currency.upper() == "KRW":
        # Korean Won has no decimal places
        return f"{symbol}{value:,.0f}"
    else:
        # Other currencies typically use 2 decimal places
        return f"{symbol}{value:,.2f}"
