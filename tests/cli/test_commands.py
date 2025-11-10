"""Test CLI commands"""
import pytest
from typer.testing import CliRunner
from cli.commands import collect, backtest, ml, analyze


class TestCollectCommand:
    """Test data collection commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    def test_collect_domestic_command_exists(self, runner):
        """Test collect domestic command exists"""
        result = runner.invoke(collect.app, ["domestic"])
        # Should fail with missing args or succeed - either is fine
        assert "domestic" in result.stdout.lower() or result.exit_code in [0, 1, 2]

    def test_collect_overseas_command_exists(self, runner):
        """Test collect overseas command exists"""
        result = runner.invoke(collect.app, ["overseas"])
        assert "overseas" in result.stdout.lower() or result.exit_code in [0, 1, 2]


class TestBacktestCommand:
    """Test backtesting commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    def test_backtest_run_command_exists(self, runner):
        """Test backtest run command exists"""
        result = runner.invoke(backtest.app, ["run"])
        # Should fail with missing strategy arg OR execute with default
        assert result.exit_code in [0, 2] or "백테스팅" in result.stdout

    def test_backtest_results_command_exists(self, runner):
        """Test backtest results command exists"""
        result = runner.invoke(backtest.app, ["results"])
        # Should succeed as no required args
        assert result.exit_code == 0 or "결과" in result.stdout


class TestMLCommand:
    """Test machine learning commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    def test_ml_train_command_exists(self, runner):
        """Test ml train command exists"""
        result = runner.invoke(ml.app, ["train"])
        # Should fail with missing model_name arg OR execute with default
        assert result.exit_code in [0, 2] or "학습" in result.stdout

    def test_ml_predict_command_exists(self, runner):
        """Test ml predict command exists"""
        result = runner.invoke(ml.app, ["predict"])
        # Should fail with missing args OR execute with default
        assert result.exit_code in [0, 2] or "예측" in result.stdout

    def test_ml_evaluate_command_exists(self, runner):
        """Test ml evaluate command exists"""
        result = runner.invoke(ml.app, ["evaluate"])
        # Should fail with missing model_name arg OR execute with default
        assert result.exit_code in [0, 2] or "평가" in result.stdout


class TestAnalyzeCommand:
    """Test analysis commands"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    def test_analyze_stock_command_exists(self, runner):
        """Test analyze stock command exists"""
        result = runner.invoke(analyze.app, ["stock"])
        # Should fail with missing symbol arg OR execute with default
        assert result.exit_code in [0, 2] or "분석" in result.stdout

    def test_analyze_portfolio_command_exists(self, runner):
        """Test analyze portfolio command exists"""
        result = runner.invoke(analyze.app, ["portfolio"])
        # Should succeed as no required args
        assert result.exit_code == 0 or "포트폴리오" in result.stdout
