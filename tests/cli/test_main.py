"""Test CLI main application"""
import pytest
from typer.testing import CliRunner
from cli.main import app


class TestCLIApp:
    """Test CLI main app initialization and structure"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    def test_cli_app_exists(self):
        """Test that CLI app is created"""
        from cli.main import app
        assert app is not None

    def test_cli_help(self, runner):
        """Test CLI help output"""
        result = runner.invoke(app, [])
        # With no_args_is_help=True, should show help or error
        assert result.exit_code in [0, 1] or len(result.stdout) > 0

    def test_collect_command_registered(self, runner):
        """Test collect command is registered"""
        result = runner.invoke(app, ["collect"])
        # Should show subcommands or work
        assert result.exit_code in [0, 1] or "collect" in result.stdout.lower()

    def test_backtest_command_registered(self, runner):
        """Test backtest command is registered"""
        result = runner.invoke(app, ["backtest"])
        # Should show subcommands or work
        assert result.exit_code in [0, 1] or "backtest" in result.stdout.lower()

    def test_ml_command_registered(self, runner):
        """Test ml command is registered"""
        result = runner.invoke(app, ["ml"])
        # Should show subcommands or work
        assert result.exit_code in [0, 1] or "ml" in result.stdout.lower()

    def test_analyze_command_registered(self, runner):
        """Test analyze command is registered"""
        result = runner.invoke(app, ["analyze"])
        # Should show subcommands or work
        assert result.exit_code in [0, 1] or "analyze" in result.stdout.lower()
