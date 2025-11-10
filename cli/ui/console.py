"""Rich Console singleton wrapper"""
from typing import Optional
from rich.console import Console

_console: Optional[Console] = None


def get_console() -> Console:
    """
    Get or create Rich Console singleton.

    Returns:
        Console: Rich Console instance
    """
    global _console
    if _console is None:
        _console = Console()
    return _console


def reset_console() -> None:
    """
    Reset the console singleton.
    Useful for testing or reinitialization.
    """
    global _console
    _console = None
