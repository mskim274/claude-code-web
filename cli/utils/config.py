"""CLI configuration management"""
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CLIConfig:
    """
    CLI configuration settings.
    """

    # Display settings
    color_enabled: bool = True
    verbose: bool = False
    quiet: bool = False

    # Output settings
    output_format: str = "table"  # table, json, csv
    max_width: Optional[int] = None

    # Progress settings
    show_progress: bool = True
    show_eta: bool = True

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # Data directories
    data_dir: Path = field(default_factory=lambda: Path("data"))
    cache_dir: Path = field(default_factory=lambda: Path(".cache"))


_config: Optional[CLIConfig] = None


def get_config() -> CLIConfig:
    """
    Get or create CLI config singleton.

    Returns:
        CLIConfig instance
    """
    global _config
    if _config is None:
        _config = CLIConfig()
    return _config


def reset_config() -> None:
    """
    Reset config singleton.
    Useful for testing.
    """
    global _config
    _config = None
