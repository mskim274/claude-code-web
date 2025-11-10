"""Progress bar and spinner utilities"""
from contextlib import contextmanager
from typing import Generator, Tuple, Optional
import time
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TaskID,
)


@contextmanager
def create_progress(
    description: str, total: int
) -> Generator[Tuple[Progress, TaskID], None, None]:
    """
    Create a Rich progress bar context manager.

    Args:
        description: Task description
        total: Total number of items

    Yields:
        Tuple of (Progress instance, TaskID)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task_id = progress.add_task(description, total=total)
        yield progress, task_id


class ProgressTracker:
    """
    Simple progress tracker with percentage and ETA calculation.
    """

    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items
            description: Task description
        """
        self.total = total
        self.completed = 0
        self.description = description
        self._start_time: Optional[float] = None

    def update(self, increment: int = 1) -> None:
        """
        Update progress by incrementing completed count.

        Args:
            increment: Number of items completed
        """
        if self._start_time is None:
            self._start_time = time.time()
        self.completed += increment

    @property
    def percentage(self) -> float:
        """
        Calculate completion percentage.

        Returns:
            Percentage completed (0-100)
        """
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100.0

    def get_eta(self) -> str:
        """
        Calculate estimated time remaining.

        Returns:
            ETA string or "N/A" if unavailable
        """
        if self._start_time is None or self.completed == 0:
            return "N/A"

        elapsed = time.time() - self._start_time
        if elapsed == 0:
            return "N/A"

        items_per_second = self.completed / elapsed
        remaining_items = self.total - self.completed

        if items_per_second > 0:
            eta_seconds = remaining_items / items_per_second
            minutes, seconds = divmod(int(eta_seconds), 60)
            return f"{minutes}m {seconds}s"
        return "N/A"
