"""Test CLI progress bar and spinner"""
import pytest
from io import StringIO
from rich.console import Console
from cli.ui.progress import create_progress, ProgressTracker


class TestProgressBar:
    """Test progress bar functionality"""

    def test_create_progress_context_manager(self):
        """Test progress bar can be created as context manager"""
        with create_progress("Testing", total=100) as (progress, task_id):
            assert progress is not None
            assert task_id is not None

    def test_progress_advance(self):
        """Test progress bar can be advanced"""
        with create_progress("Testing", total=100) as (progress, task_id):
            progress.advance(task_id, advance=10)
            # Progress bar should not raise exception
            assert True

    def test_progress_update(self):
        """Test progress bar can be updated"""
        with create_progress("Testing", total=100) as (progress, task_id):
            progress.update(task_id, completed=50)
            # Progress bar should not raise exception
            assert True


class TestProgressTracker:
    """Test progress tracker utility"""

    def test_progress_tracker_initialization(self):
        """Test progress tracker can be initialized"""
        tracker = ProgressTracker(total=100, description="Test Task")
        assert tracker.total == 100
        assert tracker.completed == 0
        assert tracker.description == "Test Task"

    def test_progress_tracker_update(self):
        """Test progress tracker can be updated"""
        tracker = ProgressTracker(total=100, description="Test Task")
        tracker.update(10)
        assert tracker.completed == 10
        tracker.update(20)
        assert tracker.completed == 30

    def test_progress_tracker_percentage(self):
        """Test progress tracker calculates percentage"""
        tracker = ProgressTracker(total=100, description="Test Task")
        tracker.update(25)
        assert tracker.percentage == 25.0
        tracker.update(25)
        assert tracker.percentage == 50.0

    def test_progress_tracker_eta_calculation(self):
        """Test progress tracker calculates ETA"""
        tracker = ProgressTracker(total=100, description="Test Task")
        tracker.update(10)
        # ETA should be available after first update
        eta = tracker.get_eta()
        assert eta is not None or eta == "N/A"
