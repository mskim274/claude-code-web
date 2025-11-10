"""
Unit tests for MLTradingStrategy

Tests for ML-based trading strategy signal generation and returns calculation.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock


class TestMLTradingStrategy:
    """Test suite for MLTradingStrategy class"""

    @pytest.fixture
    def mock_model(self):
        """Create a mock ML model"""
        model = MagicMock()
        return model

    @pytest.fixture
    def sample_features(self):
        """Create sample feature data"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'feature1': np.random.randn(10),
            'feature2': np.random.randn(10),
            'feature3': np.random.randn(10)
        }, index=dates)

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        prices = pd.Series([100, 102, 101, 105, 103, 107, 106, 110, 108, 112], index=dates)
        return prices

    def test_generate_signals_with_high_confidence_buy(self, mock_model, sample_features):
        """Test signal generation with high buy probability"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        # Mock predict_proba to return high probability for 'up' class
        # Shape: (n_samples, 3) for [down, flat, up]
        mock_model.predict_proba.return_value = np.array([
            [0.1, 0.2, 0.7],  # High up probability
            [0.15, 0.15, 0.7],
            [0.05, 0.25, 0.7]
        ])

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)
        signals = strategy.generate_signals(sample_features.iloc[:3])

        # All should be buy signals (1)
        assert len(signals) == 3
        assert all(signals == 1)

    def test_generate_signals_with_high_confidence_sell(self, mock_model, sample_features):
        """Test signal generation with high sell probability"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        # Mock predict_proba to return high probability for 'down' class
        mock_model.predict_proba.return_value = np.array([
            [0.75, 0.15, 0.1],  # High down probability
            [0.8, 0.1, 0.1],
            [0.7, 0.2, 0.1]
        ])

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)
        signals = strategy.generate_signals(sample_features.iloc[:3])

        # All should be sell signals (-1)
        assert len(signals) == 3
        assert all(signals == -1)

    def test_generate_signals_with_low_confidence(self, mock_model, sample_features):
        """Test signal generation with low confidence (no signal)"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        # Mock predict_proba to return uncertain probabilities
        mock_model.predict_proba.return_value = np.array([
            [0.3, 0.4, 0.3],  # No clear direction
            [0.35, 0.35, 0.3],
            [0.33, 0.33, 0.34]
        ])

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)
        signals = strategy.generate_signals(sample_features.iloc[:3])

        # All should be neutral (0)
        assert len(signals) == 3
        assert all(signals == 0)

    def test_threshold_behavior(self, mock_model, sample_features):
        """Test that threshold correctly filters signals"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        # Mock predict_proba with probability right at threshold
        mock_model.predict_proba.return_value = np.array([
            [0.1, 0.3, 0.6],   # Exactly at threshold
            [0.1, 0.3, 0.61],  # Just above threshold
            [0.1, 0.3, 0.59]   # Just below threshold
        ])

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)
        signals = strategy.generate_signals(sample_features.iloc[:3])

        # First: 0.6 is not > 0.6, should be 0
        # Second: 0.61 > 0.6, should be 1
        # Third: 0.59 is not > 0.6, should be 0
        assert signals.iloc[0] == 0
        assert signals.iloc[1] == 1
        assert signals.iloc[2] == 0

    def test_generate_signals_with_return_proba(self, mock_model, sample_features):
        """Test signal generation with probability return"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        proba_array = np.array([
            [0.1, 0.2, 0.7],
            [0.7, 0.2, 0.1],
            [0.3, 0.4, 0.3]
        ])
        mock_model.predict_proba.return_value = proba_array

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)
        signals, probabilities = strategy.generate_signals(sample_features.iloc[:3], return_proba=True)

        # Check signals
        assert len(signals) == 3
        assert signals.iloc[0] == 1   # High up
        assert signals.iloc[1] == -1  # High down
        assert signals.iloc[2] == 0   # Uncertain

        # Check probabilities DataFrame
        assert isinstance(probabilities, pd.DataFrame)
        assert probabilities.shape == (3, 3)
        assert list(probabilities.columns) == ['prob_down', 'prob_flat', 'prob_up']
        np.testing.assert_array_almost_equal(probabilities.values, proba_array)

    def test_calculate_returns(self, mock_model, sample_prices):
        """Test strategy returns calculation"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)

        # Create simple signals: buy on day 0, sell on day 5
        signals = pd.Series([1, 0, 0, 0, 0, -1, 0, 0, 0, 0], index=sample_prices.index)

        returns = strategy.calculate_returns(signals, sample_prices)

        # Check shape
        assert len(returns) == len(sample_prices)

        # Check that returns are shifted (signal on t affects return on t+1)
        # First return should be NaN (no previous signal)
        assert pd.isna(returns.iloc[0])

        # Check that signals affect returns correctly
        market_returns = sample_prices.pct_change()
        expected_return_day1 = signals.iloc[0] * market_returns.iloc[1]  # Buy signal * market return
        assert np.isclose(returns.iloc[1], expected_return_day1)

    def test_get_positions(self, mock_model):
        """Test position calculation with hold days"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6, hold_days=3)

        # Create signals: buy on day 0 and 5
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        signals = pd.Series([1, 0, 0, 0, 0, -1, 0, 0, 0, 0], index=dates)

        positions = strategy.get_positions(signals)

        # Position should be held for 3 days after signal
        # Day 0-2: long (hold_days=3)
        assert positions.iloc[0] == 1
        assert positions.iloc[1] == 1
        assert positions.iloc[2] == 1

        # Day 3-4: flat
        assert positions.iloc[3] == 0
        assert positions.iloc[4] == 0

        # Day 5-7: short
        assert positions.iloc[5] == -1
        assert positions.iloc[6] == -1
        assert positions.iloc[7] == -1

        # Day 8-9: flat
        assert positions.iloc[8] == 0
        assert positions.iloc[9] == 0

    def test_initialization_with_custom_parameters(self, mock_model):
        """Test strategy initialization with custom parameters"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        strategy = MLTradingStrategy(model=mock_model, threshold=0.75, hold_days=5)

        assert strategy.model == mock_model
        assert strategy.threshold == 0.75
        assert strategy.hold_days == 5

    def test_signals_index_matches_input(self, mock_model, sample_features):
        """Test that output signals have same index as input features"""
        from ml.backtest.ml_strategy import MLTradingStrategy

        mock_model.predict_proba.return_value = np.random.rand(len(sample_features), 3)

        strategy = MLTradingStrategy(model=mock_model, threshold=0.6)
        signals = strategy.generate_signals(sample_features)

        # Check that index matches
        pd.testing.assert_index_equal(signals.index, sample_features.index)
