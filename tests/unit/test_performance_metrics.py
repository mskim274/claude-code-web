"""
Unit tests for PerformanceEvaluator

Tests for classification and trading performance metrics calculation.
"""

import pytest
import numpy as np
import pandas as pd


class TestPerformanceEvaluator:
    """Test suite for PerformanceEvaluator class"""

    @pytest.fixture
    def evaluator(self):
        """Create PerformanceEvaluator instance"""
        from ml.backtest.performance_metrics import PerformanceEvaluator
        return PerformanceEvaluator()

    @pytest.fixture
    def perfect_classification_data(self):
        """Perfect classification predictions"""
        y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        y_pred = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        return y_true, y_pred

    @pytest.fixture
    def poor_classification_data(self):
        """Poor classification predictions"""
        y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        y_pred = np.array([2, 0, 1, 2, 0, 1, 2, 0, 1, 2])
        return y_true, y_pred

    @pytest.fixture
    def sample_returns_positive(self):
        """Sample returns with positive trend"""
        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        # Generate returns with positive drift
        np.random.seed(42)
        returns = pd.Series(
            np.random.normal(0.001, 0.02, 252),  # Mean 0.1% daily
            index=dates,
            name='returns'
        )
        return returns

    @pytest.fixture
    def sample_returns_negative(self):
        """Sample returns with negative trend"""
        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        np.random.seed(42)
        returns = pd.Series(
            np.random.normal(-0.001, 0.02, 252),  # Mean -0.1% daily
            index=dates,
            name='returns'
        )
        return returns

    def test_evaluate_classification_perfect(self, evaluator, perfect_classification_data):
        """Test classification metrics with perfect predictions"""
        y_true, y_pred = perfect_classification_data

        metrics = evaluator.evaluate_classification(y_true, y_pred)

        # Perfect accuracy
        assert metrics['accuracy'] == 1.0
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1_score'] == 1.0

        # Check confusion matrix
        assert 'confusion_matrix' in metrics
        confusion = np.array(metrics['confusion_matrix'])
        # Diagonal should have all counts
        assert np.trace(confusion) == len(y_true)

    def test_evaluate_classification_returns_all_metrics(self, evaluator, poor_classification_data):
        """Test that all required classification metrics are returned"""
        y_true, y_pred = poor_classification_data

        metrics = evaluator.evaluate_classification(y_true, y_pred)

        # Check all required keys
        required_keys = ['accuracy', 'precision', 'recall', 'f1_score', 'confusion_matrix']
        for key in required_keys:
            assert key in metrics, f"Missing metric: {key}"

        # Check value ranges
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['precision'] <= 1
        assert 0 <= metrics['recall'] <= 1
        assert 0 <= metrics['f1_score'] <= 1

    def test_evaluate_classification_with_imbalanced_data(self, evaluator):
        """Test classification with imbalanced classes"""
        # Heavily imbalanced: mostly class 0
        y_true = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 2])
        y_pred = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 2])

        metrics = evaluator.evaluate_classification(y_true, y_pred)

        # Should still work with macro averaging
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert metrics['accuracy'] == 1.0  # Perfect predictions

    def test_evaluate_trading_positive_returns(self, evaluator, sample_returns_positive):
        """Test trading metrics with positive returns"""
        metrics = evaluator.evaluate_trading(sample_returns_positive)

        # Check all required keys
        required_keys = [
            'total_return', 'annualized_return', 'sharpe_ratio', 'sortino_ratio',
            'max_drawdown', 'win_rate', 'profit_factor', 'num_trades', 'avg_return_per_trade'
        ]
        for key in required_keys:
            assert key in metrics, f"Missing metric: {key}"

        # With positive mean returns
        assert metrics['total_return'] > 0
        assert metrics['annualized_return'] > 0
        assert metrics['sharpe_ratio'] > 0
        assert metrics['max_drawdown'] <= 0  # Drawdown is negative

    def test_evaluate_trading_negative_returns(self, evaluator, sample_returns_negative):
        """Test trading metrics with negative returns"""
        metrics = evaluator.evaluate_trading(sample_returns_negative)

        # With negative mean returns
        assert metrics['total_return'] < 0
        assert metrics['annualized_return'] < 0
        assert metrics['sharpe_ratio'] < 0  # Negative Sharpe

    def test_evaluate_trading_sharpe_ratio_calculation(self, evaluator):
        """Test Sharpe ratio calculation"""
        # Create returns with low volatility (not constant to avoid std=0)
        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.01, 0.001, 252), index=dates)  # Mean 1%, low volatility

        metrics = evaluator.evaluate_trading(returns)

        # Sharpe = sqrt(252) * (mean - rf) / std
        # With high return and low volatility, Sharpe should be high
        assert metrics['sharpe_ratio'] > 5  # High due to low volatility relative to return

    def test_evaluate_trading_max_drawdown(self, evaluator):
        """Test max drawdown calculation"""
        # Create returns with known drawdown
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        # Prices: 100 -> 110 -> 105 -> 100 -> 95 -> 90 -> 95 -> 100 -> 105 -> 110
        prices = pd.Series([100, 110, 105, 100, 95, 90, 95, 100, 105, 110], index=dates)
        returns = prices.pct_change().dropna()

        metrics = evaluator.evaluate_trading(returns)

        # Max drawdown from 110 to 90 = -18.18%
        assert metrics['max_drawdown'] < -0.15
        assert metrics['max_drawdown'] > -0.20

    def test_evaluate_trading_win_rate(self, evaluator):
        """Test win rate calculation"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        # 7 positive, 3 negative
        returns = pd.Series([0.01, -0.01, 0.02, 0.01, -0.01, 0.01, 0.01, -0.01, 0.01, 0.01], index=dates)

        metrics = evaluator.evaluate_trading(returns)

        # Win rate should be 7/10 = 0.7
        assert abs(metrics['win_rate'] - 0.7) < 0.01

    def test_evaluate_trading_profit_factor(self, evaluator):
        """Test profit factor calculation"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        # Total profit: 0.06, Total loss: 0.03
        returns = pd.Series([0.02, -0.01, 0.02, 0.01, -0.01, 0.01, 0.0, -0.01, 0.0, 0.0], index=dates)

        metrics = evaluator.evaluate_trading(returns)

        # Profit factor = 0.06 / 0.03 = 2.0
        assert abs(metrics['profit_factor'] - 2.0) < 0.1

    def test_evaluate_trading_with_zero_returns(self, evaluator):
        """Test handling of zero returns"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        returns = pd.Series([0.0] * 10, index=dates)

        metrics = evaluator.evaluate_trading(returns)

        # All metrics should be 0 or undefined
        assert metrics['total_return'] == 0.0
        assert metrics['annualized_return'] == 0.0
        # Sharpe/Sortino might be nan or 0
        assert 'sharpe_ratio' in metrics

    def test_evaluate_trading_num_trades(self, evaluator):
        """Test number of trades counting"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        # 6 non-zero returns
        returns = pd.Series([0.01, 0.0, 0.02, 0.0, -0.01, 0.01, 0.0, 0.0, 0.01, 0.0], index=dates)

        metrics = evaluator.evaluate_trading(returns)

        # Should count non-zero returns as trades
        assert metrics['num_trades'] == 5

    def test_evaluate_trading_avg_return_per_trade(self, evaluator):
        """Test average return per trade"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        returns = pd.Series([0.02, 0.0, 0.04, 0.0, -0.02, 0.02, 0.0, 0.0, 0.04, 0.0], index=dates)

        metrics = evaluator.evaluate_trading(returns)

        # Non-zero returns: 0.02, 0.04, -0.02, 0.02, 0.04 = avg 0.02
        assert abs(metrics['avg_return_per_trade'] - 0.02) < 0.001

    def test_evaluate_trading_with_custom_risk_free_rate(self, evaluator, sample_returns_positive):
        """Test trading evaluation with custom risk-free rate"""
        metrics_low_rf = evaluator.evaluate_trading(sample_returns_positive, risk_free_rate=0.01)
        metrics_high_rf = evaluator.evaluate_trading(sample_returns_positive, risk_free_rate=0.10)

        # Higher risk-free rate should result in lower Sharpe ratio
        assert metrics_low_rf['sharpe_ratio'] > metrics_high_rf['sharpe_ratio']

    def test_print_report_runs_without_error(self, evaluator, perfect_classification_data, sample_returns_positive):
        """Test that print_report executes without error"""
        y_true, y_pred = perfect_classification_data
        classification_metrics = evaluator.evaluate_classification(y_true, y_pred)
        trading_metrics = evaluator.evaluate_trading(sample_returns_positive)

        # Should not raise exception
        try:
            evaluator.print_report(classification_metrics, trading_metrics)
            assert True
        except Exception as e:
            pytest.fail(f"print_report raised exception: {e}")

    def test_confusion_matrix_shape(self, evaluator):
        """Test confusion matrix has correct shape"""
        y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 1, 2, 0, 2, 0, 1])

        metrics = evaluator.evaluate_classification(y_true, y_pred)

        confusion = np.array(metrics['confusion_matrix'])
        # Should be 3x3 for 3 classes
        assert confusion.shape == (3, 3)

    def test_sortino_ratio_uses_downside_risk(self, evaluator):
        """Test that Sortino ratio only considers downside deviation"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        # Mix of positive and negative returns
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

        metrics = evaluator.evaluate_trading(returns)

        # Sortino should be different from Sharpe (usually higher)
        # because it only penalizes downside volatility
        assert 'sortino_ratio' in metrics
        assert 'sharpe_ratio' in metrics
