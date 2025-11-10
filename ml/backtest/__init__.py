"""
Backtesting Module for ML Trading Strategies

This module provides tools for backtesting machine learning based trading strategies:
- MLTradingStrategy: ML prediction-based trading strategy
- WalkForwardBacktest: Walk-forward validation backtesting
- PerformanceEvaluator: Performance metrics calculation
"""

from .ml_strategy import MLTradingStrategy

__all__ = [
    'MLTradingStrategy',
]

# Import other modules when they are available
try:
    from .walk_forward import WalkForwardBacktest, BacktestResult
    __all__.extend(['WalkForwardBacktest', 'BacktestResult'])
except ImportError:
    pass

try:
    from .performance_metrics import PerformanceEvaluator
    __all__.append('PerformanceEvaluator')
except ImportError:
    pass
