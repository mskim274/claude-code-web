"""Status monitoring module for CLI"""
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
import psutil
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class SystemInfo:
    """System information collector"""

    @staticmethod
    def get_cpu_usage() -> float:
        """
        Get current CPU usage percentage.

        Returns:
            CPU usage percentage (0-100)
        """
        return psutil.cpu_percent(interval=0.1)

    @staticmethod
    def get_memory_usage() -> float:
        """
        Get current memory usage percentage.

        Returns:
            Memory usage percentage (0-100)
        """
        return psutil.virtual_memory().percent


class APIRateLimitStatus:
    """API rate limit status tracker"""

    def __init__(self, limit: int, remaining: int, reset_time: datetime):
        """
        Initialize API rate limit status.

        Args:
            limit: Total API call limit
            remaining: Remaining API calls
            reset_time: Time when limit resets
        """
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time

    def to_string(self) -> str:
        """
        Convert status to string representation.

        Returns:
            Formatted status string
        """
        return f"{self.remaining}/{self.limit} (리셋: {self.reset_time.strftime('%H:%M:%S')})"

    def is_exhausted(self) -> bool:
        """
        Check if API rate limit is exhausted.

        Returns:
            True if no remaining calls
        """
        return self.remaining <= 0


class StatusMonitor:
    """Real-time status monitoring panel"""

    def __init__(self):
        """Initialize status monitor"""
        self.system_info = SystemInfo()
        self.api_status: Dict[str, APIRateLimitStatus] = {}

    def update_api_status(self, api_name: str, status: APIRateLimitStatus) -> None:
        """
        Update API rate limit status.

        Args:
            api_name: Name of the API
            status: APIRateLimitStatus instance
        """
        self.api_status[api_name] = status

    def create_panel(self) -> Panel:
        """
        Create status panel with current information.

        Returns:
            Rich Panel with status information
        """
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        # System info
        table.add_row("CPU", f"{self.system_info.get_cpu_usage():.1f}%")
        table.add_row("메모리", f"{self.system_info.get_memory_usage():.1f}%")

        # API status
        for api_name, status in self.api_status.items():
            table.add_row(f"{api_name} API", status.to_string())

        return Panel(table, title="시스템 상태", border_style="green")

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get status summary as dictionary.

        Returns:
            Dictionary with cpu, memory, and api_status
        """
        return {
            "cpu": self.system_info.get_cpu_usage(),
            "memory": self.system_info.get_memory_usage(),
            "api_status": {
                api_name: {
                    "limit": status.limit,
                    "remaining": status.remaining,
                    "reset_time": status.reset_time.isoformat()
                }
                for api_name, status in self.api_status.items()
            }
        }

    def start_live_monitoring(self, refresh_rate: float = 1.0) -> Live:
        """
        Start live monitoring panel.

        Args:
            refresh_rate: Refresh rate in seconds

        Returns:
            Rich Live instance
        """
        live = Live(
            self.create_panel(),
            refresh_per_second=1.0 / refresh_rate,
            auto_refresh=True
        )
        return live
