"""
Integration tests for WalkForwardBacktest

Tests for walk-forward validation backtesting with no future data leakage.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch


class TestWalkForwardBacktest:
    """Test suite for WalkForwardBacktest class"""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Create sample OHLCV data for backtesting"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=500, freq='D')

        # Generate realistic price movement
        returns = np.random.normal(0.0005, 0.02, 500)
        prices = 100 * (1 + returns).cumprod()

        return pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, 500)),
            'high': prices * (1 + np.random.uniform(0, 0.02, 500)),
            'low': prices * (1 + np.random.uniform(-0.02, 0, 500)),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 500)
        }, index=dates)

    @pytest.fixture
    def mock_model_class(self):
        """Create mock model class"""
        class MockModel:
            def __init__(self, params=None):
                self.params = params
                self.model = MagicMock()

            def fit(self, X, y):
                return self

            def predict(self, X):
                # Predict based on simple rule for testing
                np.random.seed(42)
                return np.random.randint(0, 3, len(X))

            def predict_proba(self, X):
                # Generate random probabilities
                np.random.seed(42)
                proba = np.random.dirichlet([1, 1, 1], len(X))
                return proba

        return MockModel

    @pytest.fixture
    def mock_strategy_class(self):
        """Create mock strategy class"""
        from ml.backtest.ml_strategy import MLTradingStrategy
        return MLTradingStrategy

    @pytest.fixture
    def mock_feature_engine(self):
        """Create mock feature engine"""
        class MockFeatureEngine:
            def create_features(self, df):
                """Create simple features from OHLCV data"""
                features = pd.DataFrame(index=df.index)
                features['returns'] = df['close'].pct_change()
                features['volume'] = df['volume']
                features['high_low'] = (df['high'] - df['low']) / df['close']
                return features.dropna()

            def create_labels(self, features):
                """Create labels from returns"""
                forward_returns = features['returns'].shift(-1)
                labels = pd.Series(1, index=features.index)  # Default: flat

                # Label based on forward returns
                labels[forward_returns > 0.01] = 2  # Up
                labels[forward_returns < -0.01] = 0  # Down

                return labels.dropna()

        return MockFeatureEngine()

    def test_walk_forward_backtest_initialization(self, mock_model_class, mock_strategy_class, mock_feature_engine):
        """Test WalkForwardBacktest initialization"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        assert backtest.model_class == mock_model_class
        assert backtest.strategy_class == mock_strategy_class
        assert backtest.feature_engine == mock_feature_engine

    def test_walk_forward_backtest_runs_successfully(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test that walk-forward backtesting runs successfully"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Check that result has all required attributes
        assert hasattr(result, 'returns')
        assert hasattr(result, 'market_returns')
        assert hasattr(result, 'signals')
        assert hasattr(result, 'predictions')
        assert hasattr(result, 'probabilities')
        assert hasattr(result, 'trades')
        assert hasattr(result, 'metrics')

    def test_no_future_data_leakage(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test that there is no future data leakage in walk-forward"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Check that signals are generated before they are used
        # Signals should have earlier or equal dates compared to returns
        assert result.signals.index[0] <= result.returns.index[0]

        # Check that all trades have valid dates (within data range)
        for trade in result.trades:
            assert trade['date'] in sample_ohlcv_data.index

    def test_expanding_window(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test walk-forward with expanding window"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Check that we have multiple test periods
        # With 500 days, train=100, test=20, step=20
        # We should have (500 - 100 - 20) // 20 + 1 = 19 iterations
        assert len(result.signals) > 0
        assert len(result.predictions) > 0

    def test_walk_forward_with_custom_model_params(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test walk-forward with custom model parameters"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        model_params = {'learning_rate': 0.05, 'n_estimators': 100}
        strategy_params = {'threshold': 0.7, 'hold_days': 2}

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20,
            model_params=model_params,
            strategy_params=strategy_params
        )

        assert result is not None
        assert len(result.signals) > 0

    def test_walk_forward_returns_have_correct_index(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test that returns have correct datetime index"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Check that returns are pandas Series with datetime index
        assert isinstance(result.returns, pd.Series)
        assert isinstance(result.returns.index, pd.DatetimeIndex)

        # Check that market returns match
        assert isinstance(result.market_returns, pd.Series)
        assert len(result.returns) == len(result.market_returns)

    def test_walk_forward_trades_recorded(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test that trades are properly recorded"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Check that trades list is not empty
        assert len(result.trades) > 0

        # Check trade structure
        first_trade = result.trades[0]
        assert 'date' in first_trade
        assert 'signal' in first_trade
        assert 'prediction' in first_trade
        assert 'probability' in first_trade

        # Check that signal is valid
        assert first_trade['signal'] in [-1, 0, 1]

    def test_walk_forward_metrics_calculated(
        self, sample_ohlcv_data, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test that performance metrics are calculated"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        result = backtest.run(
            data=sample_ohlcv_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Check classification metrics
        assert 'accuracy' in result.metrics
        assert 'precision' in result.metrics
        assert 'recall' in result.metrics
        assert 'f1_score' in result.metrics

        # Check trading metrics
        assert 'total_return' in result.metrics
        assert 'sharpe_ratio' in result.metrics
        assert 'max_drawdown' in result.metrics
        assert 'win_rate' in result.metrics

    def test_walk_forward_with_short_data(
        self, mock_model_class, mock_strategy_class, mock_feature_engine
    ):
        """Test walk-forward with insufficient data"""
        from ml.backtest.walk_forward import WalkForwardBacktest

        # Create very short data
        dates = pd.date_range('2020-01-01', periods=50, freq='D')
        short_data = pd.DataFrame({
            'open': 100,
            'high': 101,
            'low': 99,
            'close': 100,
            'volume': 1000000
        }, index=dates)

        backtest = WalkForwardBacktest(
            model_class=mock_model_class,
            strategy_class=mock_strategy_class,
            feature_engine=mock_feature_engine
        )

        # This should still work but with limited iterations
        result = backtest.run(
            data=short_data,
            train_period=20,
            test_period=5,
            step=5
        )

        assert result is not None

    def test_backtest_result_dataclass(self):
        """Test BacktestResult dataclass structure"""
        from ml.backtest.walk_forward import BacktestResult

        # Create sample data
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        returns = pd.Series([0.01] * 10, index=dates)
        signals = pd.Series([1] * 10, index=dates)

        result = BacktestResult(
            returns=returns,
            market_returns=returns,
            signals=signals,
            predictions=signals,
            probabilities=pd.DataFrame({'prob_down': 0.1, 'prob_flat': 0.2, 'prob_up': 0.7}, index=dates),
            trades=[],
            metrics={}
        )

        assert isinstance(result.returns, pd.Series)
        assert isinstance(result.signals, pd.Series)
        assert isinstance(result.trades, list)
        assert isinstance(result.metrics, dict)
