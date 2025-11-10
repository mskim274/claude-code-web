"""
ML Trading Strategy

Machine learning prediction-based trading strategy with configurable
confidence thresholds and holding periods.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


class MLTradingStrategy:
    """
    ML 예측 기반 매매 전략

    LightGBM 모델의 예측 확률을 사용하여 매매 신호를 생성합니다.
    확률이 임계값을 초과할 때만 거래 신호를 발생시킵니다.

    Attributes:
        model: 학습된 LightGBM 모델
        threshold: 매매 신호 확률 임계값 (0.5-1.0)
        hold_days: 포지션 보유 기간 (일)

    Example:
        >>> from ml.models import LGBMStockClassifier
        >>> model = LGBMStockClassifier(params)
        >>> model.fit(X_train, y_train)
        >>> strategy = MLTradingStrategy(model, threshold=0.6, hold_days=1)
        >>> signals = strategy.generate_signals(X_test)
    """

    def __init__(
        self,
        model,
        threshold: float = 0.6,
        hold_days: int = 1
    ):
        """
        전략 초기화

        Args:
            model: 학습된 LightGBM 모델 (predict_proba 메서드 필요)
            threshold: 매매 신호 확률 임계값 (0.5-1.0)
                - 높을수록 더 확실한 신호만 생성 (보수적)
                - 낮을수록 더 많은 신호 생성 (공격적)
            hold_days: 포지션 보유 기간 (일)
                - 1: 일간 트레이딩
                - 5: 주간 스윙 트레이딩
                - 20: 월간 포지션 트레이딩

        Raises:
            ValueError: threshold가 0~1 범위를 벗어나는 경우
        """
        if not 0 <= threshold <= 1:
            raise ValueError(f"threshold must be between 0 and 1, got {threshold}")

        self.model = model
        self.threshold = threshold
        self.hold_days = hold_days

    def generate_signals(
        self,
        X: pd.DataFrame,
        return_proba: bool = False
    ) -> pd.Series | Tuple[pd.Series, pd.DataFrame]:
        """
        매매 신호 생성

        모델의 예측 확률을 기반으로 매매 신호를 생성합니다.
        확률이 threshold를 초과하는 경우에만 신호를 발생시킵니다.

        Args:
            X: Features (DataFrame with datetime index)
            return_proba: 확률도 함께 반환할지 여부

        Returns:
            signals (pd.Series):
                - 1: 매수 신호 (상승 확률 > threshold)
                - -1: 매도 신호 (하락 확률 > threshold)
                - 0: 관망 (확률이 낮거나 보합 예상)

            probabilities (pd.DataFrame, optional):
                - prob_down: 하락 확률
                - prob_flat: 보합 확률
                - prob_up: 상승 확률

        Example:
            >>> signals = strategy.generate_signals(X_test)
            >>> signals, proba = strategy.generate_signals(X_test, return_proba=True)
            >>> print(proba.head())
                         prob_down  prob_flat  prob_up
            2024-01-01      0.1       0.2       0.7
            2024-01-02      0.6       0.3       0.1
        """
        # 예측 확률 계산 (shape: [n_samples, 3])
        # 클래스 순서: [0: down, 1: flat, 2: up]
        proba = self.model.predict_proba(X)

        # 신호 초기화 (관망: 0)
        signals = pd.Series(0, index=X.index, name='signal')

        # 상승 확률이 threshold를 초과하면 매수 (1)
        signals[proba[:, 2] > self.threshold] = 1

        # 하락 확률이 threshold를 초과하면 매도 (-1)
        signals[proba[:, 0] > self.threshold] = -1

        if return_proba:
            # 확률을 DataFrame으로 변환
            probabilities = pd.DataFrame(
                proba,
                columns=['prob_down', 'prob_flat', 'prob_up'],
                index=X.index
            )
            return signals, probabilities

        return signals

    def calculate_returns(
        self,
        signals: pd.Series,
        prices: pd.Series
    ) -> pd.Series:
        """
        전략 수익률 계산

        매매 신호와 가격 데이터를 사용하여 전략의 수익률을 계산합니다.
        미래 데이터 유출을 방지하기 위해 신호를 1일 shift합니다.

        Args:
            signals: 매매 신호 (1, 0, -1)
            prices: 종가 시계열

        Returns:
            전략 수익률 시계열

        Note:
            - 신호는 t일 종가 기준으로 생성됨
            - 실제 진입은 t+1일에 이루어짐
            - 따라서 신호를 1일 shift하여 수익률 계산

        Example:
            >>> signals = pd.Series([1, 0, -1, 0])  # t일 신호
            >>> prices = pd.Series([100, 102, 101, 103])
            >>> returns = strategy.calculate_returns(signals, prices)
            >>> # t+1일 수익률 = shift된 신호 * 시장 수익률
        """
        # 시장 수익률 계산
        market_returns = prices.pct_change()

        # 전략 수익률 = 신호(t-1) * 시장수익률(t)
        # shift(1): t일 신호가 t+1일 수익률에 영향
        strategy_returns = signals.shift(1) * market_returns

        return strategy_returns

    def get_positions(
        self,
        signals: pd.Series
    ) -> pd.Series:
        """
        포지션 계산 (신호를 hold_days만큼 유지)

        매매 신호가 발생하면 hold_days 동안 포지션을 유지합니다.
        새로운 신호가 발생하면 기존 포지션은 종료되고 새 포지션이 시작됩니다.

        Args:
            signals: 매매 신호 (1: buy, -1: sell, 0: hold)

        Returns:
            포지션 시계열 (1: long, -1: short, 0: flat)

        Example:
            >>> strategy = MLTradingStrategy(model, hold_days=3)
            >>> signals = pd.Series([1, 0, 0, 0, 0, -1, 0, 0, 0, 0])
            >>> positions = strategy.get_positions(signals)
            >>> # Result: [1, 1, 1, 0, 0, -1, -1, -1, 0, 0]
            >>> # Signal at day 0 → hold long for 3 days
            >>> # Signal at day 5 → hold short for 3 days
        """
        positions = pd.Series(0, index=signals.index, name='position')

        for idx in range(len(signals)):
            if signals.iloc[idx] != 0:
                # 신호 발생 시점부터 hold_days만큼 포지션 유지
                end_idx = min(idx + self.hold_days, len(signals))
                positions.iloc[idx:end_idx] = signals.iloc[idx]

        return positions

    def __repr__(self) -> str:
        """String representation of the strategy"""
        return (
            f"MLTradingStrategy("
            f"threshold={self.threshold}, "
            f"hold_days={self.hold_days})"
        )
