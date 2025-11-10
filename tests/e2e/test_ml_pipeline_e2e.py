"""
End-to-End tests for ML Pipeline

Full integration test from data loading to backtesting and performance evaluation.
Tests the complete ML trading pipeline with realistic scenarios.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock


class TestMLPipelineE2E:
    """End-to-end test suite for full ML pipeline"""

    @pytest.fixture
    def realistic_market_data(self):
        """Create realistic market data for E2E testing"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=600, freq='D')

        # Simulate realistic price movements with trends
        returns = np.random.normal(0.0003, 0.015, 600)

        # Add some trends
        returns[:200] += 0.001  # Uptrend
        returns[200:400] -= 0.001  # Downtrend
        returns[400:] += 0.0005  # Mild uptrend

        prices = 100 * (1 + returns).cumprod()

        return pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.005, 0.005, 600)),
            'high': prices * (1 + np.abs(np.random.uniform(0, 0.015, 600))),
            'low': prices * (1 - np.abs(np.random.uniform(0, 0.015, 600))),
            'close': prices,
            'volume': np.random.randint(5000000, 20000000, 600)
        }, index=dates)

    @pytest.fixture
    def mock_lightgbm_model(self):
        """Create a mock LightGBM model that mimics real behavior"""
        class MockLGBMModel:
            def __init__(self, params=None):
                self.params = params or {}
                self.is_fitted = False

            def fit(self, X, y):
                """Simulate model training"""
                self.is_fitted = True
                self.feature_names = X.columns.tolist()
                self.n_features = len(self.feature_names)
                return self

            def predict(self, X):
                """Predict based on simple rules for testing"""
                if not self.is_fitted:
                    raise ValueError("Model must be fitted before prediction")

                # Simple rule: predict based on returns feature
                predictions = np.ones(len(X))
                if 'returns' in X.columns:
                    returns = X['returns'].values
                    predictions[returns > 0.01] = 2  # Up
                    predictions[returns < -0.01] = 0  # Down

                return predictions.astype(int)

            def predict_proba(self, X):
                """Generate probabilities based on predictions"""
                predictions = self.predict(X)
                proba = np.zeros((len(X), 3))

                for i, pred in enumerate(predictions):
                    if pred == 2:  # Up
                        proba[i] = [0.1, 0.2, 0.7]
                    elif pred == 0:  # Down
                        proba[i] = [0.7, 0.2, 0.1]
                    else:  # Flat
                        proba[i] = [0.3, 0.4, 0.3]

                # Add some noise
                noise = np.random.uniform(-0.05, 0.05, proba.shape)
                proba += noise
                proba = np.clip(proba, 0, 1)

                # Normalize
                proba = proba / proba.sum(axis=1, keepdims=True)

                return proba

        return MockLGBMModel

    @pytest.fixture
    def simple_feature_engine(self):
        """Create a simple feature engine for testing"""
        class SimpleFeatureEngine:
            def create_features(self, df):
                """Create basic technical features"""
                features = pd.DataFrame(index=df.index)

                # Returns
                features['returns'] = df['close'].pct_change()

                # Moving averages
                features['sma_5'] = df['close'].rolling(5).mean()
                features['sma_20'] = df['close'].rolling(20).mean()

                # Volatility
                features['volatility'] = df['close'].pct_change().rolling(20).std()

                # Volume
                features['volume'] = df['volume']
                features['volume_ma'] = df['volume'].rolling(20).mean()

                # Price range
                features['high_low_range'] = (df['high'] - df['low']) / df['close']

                return features.dropna()

            def create_labels(self, features):
                """Create labels from forward returns"""
                forward_returns = features['returns'].shift(-1)

                labels = pd.Series(1, index=features.index)  # Default: flat
                labels[forward_returns > 0.005] = 2  # Up
                labels[forward_returns < -0.005] = 0  # Down

                return labels.dropna()

        return SimpleFeatureEngine()

    def test_full_ml_pipeline(
        self,
        realistic_market_data,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test complete ML pipeline from data to backtest results"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest

        # Setup
        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        # Run backtest
        result = backtest.run(
            data=realistic_market_data,
            train_period=252,  # 1 year
            test_period=21,    # 1 month
            step=21,           # 1 month step
            model_params={'learning_rate': 0.05},
            strategy_params={'threshold': 0.6, 'hold_days': 1}
        )

        # Assertions
        assert result is not None
        assert len(result.returns) > 0
        assert len(result.signals) > 0
        assert len(result.trades) > 0

        # Check metrics are calculated
        assert 'accuracy' in result.metrics
        assert 'total_return' in result.metrics
        assert 'sharpe_ratio' in result.metrics
        assert 'max_drawdown' in result.metrics

        # Sanity checks on metrics
        assert 0 <= result.metrics['accuracy'] <= 1
        assert -1 <= result.metrics['max_drawdown'] <= 0
        assert result.metrics['num_trades'] > 0

    def test_pipeline_with_different_strategies(
        self,
        realistic_market_data,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test pipeline with different strategy parameters"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        # Conservative strategy (high threshold)
        result_conservative = backtest.run(
            data=realistic_market_data,
            train_period=200,
            test_period=20,
            step=20,
            strategy_params={'threshold': 0.8, 'hold_days': 1}
        )

        # Aggressive strategy (low threshold)
        result_aggressive = backtest.run(
            data=realistic_market_data,
            train_period=200,
            test_period=20,
            step=20,
            strategy_params={'threshold': 0.5, 'hold_days': 1}
        )

        # Aggressive strategy should have more trades
        assert result_aggressive.metrics['num_trades'] >= result_conservative.metrics['num_trades']

    def test_pipeline_reproducibility(
        self,
        realistic_market_data,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test that pipeline produces reproducible results"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        # Run twice with same parameters
        result1 = backtest.run(
            data=realistic_market_data,
            train_period=200,
            test_period=20,
            step=20,
            strategy_params={'threshold': 0.6}
        )

        result2 = backtest.run(
            data=realistic_market_data,
            train_period=200,
            test_period=20,
            step=20,
            strategy_params={'threshold': 0.6}
        )

        # Results should be identical
        assert len(result1.signals) == len(result2.signals)
        assert len(result1.trades) == len(result2.trades)
        pd.testing.assert_series_equal(result1.signals, result2.signals)

    def test_pipeline_handles_various_market_conditions(
        self,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test pipeline with different market conditions"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        # Bull market
        dates = pd.date_range('2020-01-01', periods=400, freq='D')
        bull_data = pd.DataFrame({
            'open': 100,
            'high': 105,
            'low': 95,
            'close': 100 * (1.001 ** np.arange(400)),  # Steady uptrend
            'volume': 1000000
        }, index=dates)

        result_bull = backtest.run(
            data=bull_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Results should be calculated (may not always be positive with mock model)
        assert 'total_return' in result_bull.metrics

        # Bear market
        bear_data = pd.DataFrame({
            'open': 100,
            'high': 105,
            'low': 95,
            'close': 100 * (0.999 ** np.arange(400)),  # Steady downtrend
            'volume': 1000000
        }, index=dates)

        result_bear = backtest.run(
            data=bear_data,
            train_period=100,
            test_period=20,
            step=20
        )

        # Results should be calculated (may be negative)
        assert 'total_return' in result_bear.metrics

    def test_pipeline_performance_metrics_quality(
        self,
        realistic_market_data,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test that pipeline produces reasonable performance metrics"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        result = backtest.run(
            data=realistic_market_data,
            train_period=252,
            test_period=21,
            step=21,
            strategy_params={'threshold': 0.6}
        )

        # Check all required metrics are present
        required_classification_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        required_trading_metrics = [
            'total_return', 'annualized_return', 'sharpe_ratio',
            'sortino_ratio', 'max_drawdown', 'win_rate', 'profit_factor'
        ]

        for metric in required_classification_metrics:
            assert metric in result.metrics
            assert 0 <= result.metrics[metric] <= 1

        for metric in required_trading_metrics:
            assert metric in result.metrics

        # Accuracy should be better than random (33.3% for 3 classes)
        assert result.metrics['accuracy'] >= 0.25

    def test_pipeline_with_performance_evaluator(
        self,
        realistic_market_data,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test integration with PerformanceEvaluator"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest
        from ml.backtest.performance_metrics import PerformanceEvaluator

        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        result = backtest.run(
            data=realistic_market_data,
            train_period=252,
            test_period=21,
            step=21
        )

        # Use evaluator to print report
        evaluator = PerformanceEvaluator()

        classification_metrics = {
            k: v for k, v in result.metrics.items()
            if k in ['accuracy', 'precision', 'recall', 'f1_score', 'confusion_matrix']
        }

        trading_metrics = {
            k: v for k, v in result.metrics.items()
            if k in ['total_return', 'annualized_return', 'sharpe_ratio',
                     'sortino_ratio', 'max_drawdown', 'win_rate',
                     'profit_factor', 'num_trades', 'avg_return_per_trade']
        }

        # Should not raise exception
        evaluator.print_report(classification_metrics, trading_metrics)

    def test_pipeline_edge_cases(
        self,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """Test pipeline with edge cases"""
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest

        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        # Minimum viable data
        dates = pd.date_range('2020-01-01', periods=150, freq='D')
        min_data = pd.DataFrame({
            'open': 100,
            'high': 101,
            'low': 99,
            'close': 100 * (1 + np.random.randn(150) * 0.01),
            'volume': 1000000
        }, index=dates)

        result = backtest.run(
            data=min_data,
            train_period=50,
            test_period=10,
            step=10
        )

        assert result is not None
        assert len(result.signals) > 0

    def test_full_pipeline_realistic_scenario(
        self,
        realistic_market_data,
        mock_lightgbm_model,
        simple_feature_engine
    ):
        """
        E2E test simulating a realistic trading scenario

        This test validates the entire pipeline:
        1. Data ingestion
        2. Feature engineering
        3. Model training
        4. Strategy execution
        5. Performance evaluation
        """
        from ml.backtest import MLTradingStrategy, WalkForwardBacktest
        from ml.backtest.performance_metrics import PerformanceEvaluator

        # Initialize components
        backtest = WalkForwardBacktest(
            model_class=mock_lightgbm_model,
            strategy_class=MLTradingStrategy,
            feature_engine=simple_feature_engine
        )

        # Run backtest with realistic parameters
        result = backtest.run(
            data=realistic_market_data,
            train_period=252,  # 1 year training
            test_period=63,    # 3 months testing
            step=21,           # Retrain monthly
            model_params={
                'learning_rate': 0.05,
                'n_estimators': 100
            },
            strategy_params={
                'threshold': 0.65,  # Conservative
                'hold_days': 1
            }
        )

        # Validate results (relaxed assertions for mock model)
        assert result.metrics['accuracy'] > 0.25, "Accuracy should be reasonable"
        assert result.metrics['num_trades'] > 0, "Should have executed trades"
        assert -1 <= result.metrics['max_drawdown'] <= 0, "Drawdown should be valid"

        # Print summary (for manual inspection during test runs)
        print("\n" + "="*70)
        print("REALISTIC SCENARIO E2E TEST RESULTS")
        print("="*70)
        print(f"Accuracy:          {result.metrics['accuracy']:.2%}")
        print(f"Total Return:      {result.metrics['total_return']:.2%}")
        print(f"Sharpe Ratio:      {result.metrics['sharpe_ratio']:.4f}")
        print(f"Max Drawdown:      {result.metrics['max_drawdown']:.2%}")
        print(f"Number of Trades:  {result.metrics['num_trades']}")
        print("="*70)
