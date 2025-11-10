"""
Walk-Forward Backtesting

Time-series walk-forward validation for ML trading strategies.
Prevents future data leakage by training on past data and testing on future data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BacktestResult:
    """
    백테스트 결과 데이터 클래스

    Attributes:
        returns: 전략 수익률 시계열
        market_returns: 시장 수익률 시계열
        signals: 매매 신호 시계열 (1: buy, -1: sell, 0: hold)
        predictions: 모델 예측 시계열
        probabilities: 예측 확률 DataFrame (prob_down, prob_flat, prob_up)
        trades: 거래 내역 리스트
        metrics: 성능 지표 딕셔너리
    """
    returns: pd.Series
    market_returns: pd.Series
    signals: pd.Series
    predictions: pd.Series
    probabilities: pd.DataFrame
    trades: List[Dict]
    metrics: Dict[str, float]


class WalkForwardBacktest:
    """
    Walk-Forward 검증 백테스팅

    시계열 데이터의 순서를 유지하며 과거 데이터로 학습하고 미래 데이터로 테스트합니다.
    미래 데이터 유출을 방지하여 실전과 유사한 환경에서 전략을 검증합니다.

    Process:
        1. [Train: 0~252일] → [Test: 252~273일]
        2. [Train: 21~273일] → [Test: 273~294일]
        3. [Train: 42~294일] → [Test: 294~315일]
        ... (step 간격으로 이동)

    Attributes:
        model_class: ML 모델 클래스
        strategy_class: 트레이딩 전략 클래스
        feature_engine: Feature Engineering 엔진

    Example:
        >>> from ml.models import LGBMStockClassifier
        >>> from ml.backtest import MLTradingStrategy, WalkForwardBacktest
        >>> from ml.features import TechnicalFeatureEngine
        >>>
        >>> backtest = WalkForwardBacktest(
        ...     model_class=LGBMStockClassifier,
        ...     strategy_class=MLTradingStrategy,
        ...     feature_engine=TechnicalFeatureEngine()
        ... )
        >>>
        >>> result = backtest.run(
        ...     data=ohlcv_df,
        ...     train_period=252,  # 1년 학습
        ...     test_period=21,    # 1개월 테스트
        ...     step=21            # 1개월씩 이동
        ... )
        >>>
        >>> print(f"Sharpe Ratio: {result.metrics['sharpe_ratio']:.2f}")
    """

    def __init__(
        self,
        model_class,
        strategy_class,
        feature_engine
    ):
        """
        Walk-Forward 백테스트 초기화

        Args:
            model_class: ML 모델 클래스 (fit, predict 메서드 필요)
            strategy_class: 트레이딩 전략 클래스
            feature_engine: Feature Engineering 엔진 (create_features, create_labels 메서드 필요)
        """
        self.model_class = model_class
        self.strategy_class = strategy_class
        self.feature_engine = feature_engine

    def run(
        self,
        data: pd.DataFrame,
        train_period: int = 252,
        test_period: int = 21,
        step: int = 21,
        model_params: Optional[Dict] = None,
        strategy_params: Optional[Dict] = None
    ) -> BacktestResult:
        """
        Walk-Forward 백테스팅 실행

        시계열 순서를 유지하며 학습과 테스트를 반복합니다.
        각 반복마다 과거 데이터로 모델을 재학습하고 미래 데이터로 평가합니다.

        Args:
            data: OHLCV 데이터 (columns: open, high, low, close, volume)
            train_period: 학습 기간 (일)
            test_period: 테스트 기간 (일)
            step: 이동 간격 (일)
            model_params: 모델 하이퍼파라미터 (optional)
            strategy_params: 전략 파라미터 (optional)

        Returns:
            BacktestResult: 백테스트 결과

        Note:
            - 미래 데이터 유출 방지를 위해 학습 데이터는 항상 테스트 데이터보다 과거
            - 각 테스트 기간마다 모델을 재학습하여 최신 시장 상황 반영

        Example:
            >>> result = backtest.run(
            ...     data=df,
            ...     train_period=252,  # 1년 (약 252 거래일)
            ...     test_period=21,    # 1개월 (약 21 거래일)
            ...     step=21            # 1개월씩 이동
            ... )
        """
        all_signals = []
        all_predictions = []
        all_probabilities = []
        all_trades = []

        # Feature Engineering
        features = self.feature_engine.create_features(data)
        labels = self.feature_engine.create_labels(features)

        # 레이블이 있는 인덱스만 사용
        valid_indices = features.index.intersection(labels.index)
        features = features.loc[valid_indices]
        labels = labels.loc[valid_indices]

        # Walk-Forward loop
        for start_idx in range(0, len(features) - train_period - test_period, step):
            train_end = start_idx + train_period
            test_end = train_end + test_period

            # 데이터 범위 체크
            if test_end > len(features):
                break

            # 학습 데이터
            X_train = features.iloc[start_idx:train_end]
            y_train = labels.iloc[start_idx:train_end]

            # 테스트 데이터
            X_test = features.iloc[train_end:test_end]
            y_test = labels.iloc[train_end:test_end]

            # 모델 학습
            model = self.model_class(params=model_params)
            model.fit(X_train, y_train)

            # 전략 생성
            strategy = self.strategy_class(model, **(strategy_params or {}))

            # 신호 생성
            signals, proba = strategy.generate_signals(X_test, return_proba=True)
            predictions = model.predict(X_test)

            all_signals.append(signals)
            all_predictions.append(pd.Series(predictions, index=X_test.index))
            all_probabilities.append(proba)

            # 거래 내역 기록
            for idx, signal in signals.items():
                if signal != 0:
                    trade = {
                        'date': idx,
                        'signal': int(signal),
                        'prediction': int(predictions[X_test.index.get_loc(idx)]),
                        'probability': proba.loc[idx].tolist()
                    }
                    all_trades.append(trade)

        # 결과 병합
        if not all_signals:
            # No data to backtest
            raise ValueError("Insufficient data for walk-forward backtesting")

        signals_series = pd.concat(all_signals)
        predictions_series = pd.concat(all_predictions)
        probabilities_df = pd.concat(all_probabilities)

        # 수익률 계산
        strategy_returns = self._calculate_strategy_returns(
            signals_series,
            data['close']
        )
        market_returns = data['close'].pct_change()

        # 성능 지표 계산
        from ml.backtest.performance_metrics import PerformanceEvaluator
        evaluator = PerformanceEvaluator()

        # Classification metrics
        y_true_for_metrics = labels.loc[signals_series.index]
        classification_metrics = evaluator.evaluate_classification(
            y_true_for_metrics.values,
            predictions_series.values
        )

        # Trading metrics
        trading_metrics = evaluator.evaluate_trading(strategy_returns)

        # 통합 메트릭
        metrics = {**classification_metrics, **trading_metrics}

        return BacktestResult(
            returns=strategy_returns,
            market_returns=market_returns[strategy_returns.index],
            signals=signals_series,
            predictions=predictions_series,
            probabilities=probabilities_df,
            trades=all_trades,
            metrics=metrics
        )

    def _calculate_strategy_returns(
        self,
        signals: pd.Series,
        prices: pd.Series
    ) -> pd.Series:
        """
        전략 수익률 계산 (미래 데이터 유출 방지)

        신호는 t일 종가 기준으로 생성되며, 실제 진입은 t+1일에 이루어집니다.
        따라서 신호를 1일 shift하여 수익률을 계산합니다.

        Args:
            signals: 매매 신호 (1, 0, -1)
            prices: 종가 시계열

        Returns:
            전략 수익률 시계열

        Note:
            - t일 신호 → t+1일 진입 → t+1일 수익률 실현
            - shift(1)로 미래 데이터 유출 방지
        """
        # 시장 수익률
        market_returns = prices.pct_change()

        # 전략 수익률 = 신호(t-1) * 시장수익률(t)
        # shift(1): t일 신호가 t+1일 수익률에 영향
        strategy_returns = signals.shift(1) * market_returns[signals.index]

        # NaN 제거
        strategy_returns = strategy_returns.dropna()

        return strategy_returns

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"WalkForwardBacktest("
            f"model_class={self.model_class.__name__}, "
            f"strategy_class={self.strategy_class.__name__})"
        )
