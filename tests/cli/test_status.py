"""Tests for status monitoring module"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from cli.ui.status import StatusMonitor, SystemInfo, APIRateLimitStatus


class TestSystemInfo:
    """Test SystemInfo class"""

    @patch('psutil.cpu_percent', return_value=45.5)
    def test_get_cpu_usage(self, mock_cpu):
        """Test CPU usage retrieval"""
        usage = SystemInfo.get_cpu_usage()
        assert usage == 45.5
        mock_cpu.assert_called_once()

    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_memory):
        """Test memory usage retrieval"""
        mock_memory.return_value = Mock(percent=72.3)
        usage = SystemInfo.get_memory_usage()
        assert usage == 72.3
        mock_memory.assert_called_once()


class TestAPIRateLimitStatus:
    """Test APIRateLimitStatus class"""

    def test_api_rate_limit_creation(self):
        """Test APIRateLimitStatus can be created"""
        reset_time = datetime.now() + timedelta(hours=1)
        status = APIRateLimitStatus(limit=1000, remaining=500, reset_time=reset_time)

        assert status.limit == 1000
        assert status.remaining == 500
        assert status.reset_time == reset_time

    def test_api_rate_limit_to_string(self):
        """Test converting rate limit status to string"""
        reset_time = datetime(2025, 11, 10, 15, 30, 0)
        status = APIRateLimitStatus(limit=1000, remaining=500, reset_time=reset_time)

        result = status.to_string()
        assert "500/1000" in result
        assert "15:30:00" in result

    def test_api_rate_limit_is_exhausted(self):
        """Test checking if API rate limit is exhausted"""
        reset_time = datetime.now() + timedelta(hours=1)
        exhausted = APIRateLimitStatus(limit=1000, remaining=0, reset_time=reset_time)
        available = APIRateLimitStatus(limit=1000, remaining=100, reset_time=reset_time)

        assert exhausted.is_exhausted() is True
        assert available.is_exhausted() is False


class TestStatusMonitor:
    """Test StatusMonitor class"""

    def test_status_monitor_initialization(self):
        """Test StatusMonitor can be initialized"""
        monitor = StatusMonitor()
        assert isinstance(monitor.system_info, SystemInfo)
        assert isinstance(monitor.api_status, dict)
        assert len(monitor.api_status) == 0

    def test_update_api_status(self):
        """Test updating API rate limit status"""
        monitor = StatusMonitor()
        reset_time = datetime.now() + timedelta(hours=1)
        status = APIRateLimitStatus(limit=1000, remaining=500, reset_time=reset_time)

        monitor.update_api_status("Kiwoom", status)
        assert "Kiwoom" in monitor.api_status
        assert monitor.api_status["Kiwoom"].remaining == 500

    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('psutil.virtual_memory')
    def test_create_panel(self, mock_memory, mock_cpu):
        """Test creating status panel"""
        mock_memory.return_value = Mock(percent=60.0)
        monitor = StatusMonitor()

        panel = monitor.create_panel()
        assert panel is not None
        assert panel.title == "시스템 상태"

    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('psutil.virtual_memory')
    def test_create_panel_with_api_status(self, mock_memory, mock_cpu):
        """Test creating panel with API status"""
        mock_memory.return_value = Mock(percent=60.0)
        monitor = StatusMonitor()

        reset_time = datetime.now() + timedelta(hours=1)
        status = APIRateLimitStatus(limit=1000, remaining=500, reset_time=reset_time)
        monitor.update_api_status("Kiwoom", status)

        panel = monitor.create_panel()
        assert panel is not None

    def test_get_status_summary(self):
        """Test getting status summary as dict"""
        monitor = StatusMonitor()
        reset_time = datetime.now() + timedelta(hours=1)
        status = APIRateLimitStatus(limit=1000, remaining=500, reset_time=reset_time)
        monitor.update_api_status("Kiwoom", status)

        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory', return_value=Mock(percent=60.0)):
            summary = monitor.get_status_summary()
            assert summary["cpu"] == 50.0
            assert summary["memory"] == 60.0
            assert "Kiwoom" in summary["api_status"]
