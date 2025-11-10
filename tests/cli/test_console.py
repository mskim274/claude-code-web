"""Test CLI console singleton"""
import pytest
from rich.console import Console
from cli.ui.console import get_console, reset_console


class TestConsoleSingleton:
    """Test console singleton pattern"""

    def test_get_console_returns_console(self):
        """Test get_console returns a Console instance"""
        console = get_console()
        assert isinstance(console, Console)

    def test_get_console_returns_same_instance(self):
        """Test get_console returns the same instance"""
        console1 = get_console()
        console2 = get_console()
        assert console1 is console2

    def test_reset_console(self):
        """Test console can be reset"""
        console1 = get_console()
        reset_console()
        console2 = get_console()
        # After reset, should get a new instance
        assert console1 is not console2

    def test_console_has_print_method(self):
        """Test console has print method"""
        console = get_console()
        assert hasattr(console, "print")
        assert callable(console.print)

    def test_console_has_rule_method(self):
        """Test console has rule method"""
        console = get_console()
        assert hasattr(console, "rule")
        assert callable(console.rule)
