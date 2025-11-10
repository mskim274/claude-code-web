"""
Technical Feature Engineering

TA-Lib 기반 기술적 지표를 활용한 Feature Engineering
Phase 1에서 구현한 50개 지표를 재사용하고 추가 파생 피처 생성
"""

import pandas as pd
import numpy as np
from typing import List, Optional
import sys
import os
import logging

# backtest.indicators 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backtest.indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class TechnicalFeatureEngine:
    """
    TA-Lib 기반 기술적 지표 Feature Engineering

    Phase 1에서 구현한 50+ 기술적 지표를 활용하여
    ML 모델 학습에 필요한 피처를 생성합니다.

    Features:
        - TA-Lib 지표 50+ (Phase 1 재사용)
        - 가격 파생 피처 (캔들 패턴)
        - 거래량 파생 피처
        - 추세 파생 피처 (수익률)

    Example:
        >>> engine = TechnicalFeatureEngine()
        >>> features = engine.create_features(ohlcv_df)
        >>> labels = engine.create_labels(ohlcv_df, forward_days=1, threshold=0.01)
    """

    def __init__(self, indicators: Optional[TechnicalIndicators] = None):
        """
        초기화

        Args:
            indicators: TechnicalIndicators 인스턴스 (None이면 새로 생성)

        Example:
            >>> # 기본 사용
            >>> engine = TechnicalFeatureEngine()
            >>>
            >>> # 커스텀 indicators 사용
            >>> custom_indicators = TechnicalIndicators()
            >>> engine = TechnicalFeatureEngine(indicators=custom_indicators)
        """
        self.indicators = indicators or TechnicalIndicators()
        logger.info("TechnicalFeatureEngine initialized")

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        50+ 기술적 지표 및 파생 피처 생성

        Args:
            df: OHLCV 데이터프레임
                Required columns: date, open, high, low, close, volume

        Returns:
            Features DataFrame (50+ columns)

        Example:
            >>> df = pd.DataFrame({
            ...     'date': [...],
            ...     'open': [...],
            ...     'high': [...],
            ...     'low': [...],
            ...     'close': [...],
            ...     'volume': [...]
            ... })
            >>> features = engine.create_features(df)
            >>> print(features.columns)  # 원본 + 50+ 지표
        """
        logger.info(f"Creating features from {len(df)} rows")

        # Phase 1에서 구현한 50개 지표 계산
        result = self.indicators.calculate_all(df.copy())

        # 추가 파생 피처 생성
        result = self._add_price_features(result)
        result = self._add_volume_features(result)
        result = self._add_trend_features(result)

        # NaN 제거
        original_len = len(result)
        result = result.dropna()
        logger.info(f"Dropped {original_len - len(result)} rows with NaN")

        logger.info(f"Created {len(result.columns)} features from {len(df.columns)} original columns")

        return result

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        가격 관련 파생 피처 생성

        캔들 패턴 분석을 위한 피처:
            - price_range: (고가 - 저가) / 종가
            - body_size: |종가 - 시가| / 종가
            - upper_shadow: (고가 - max(시가, 종가)) / 종가
            - lower_shadow: (min(시가, 종가) - 저가) / 종가

        Args:
            df: OHLCV 데이터프레임

        Returns:
            가격 피처가 추가된 DataFrame
        """
        df = df.copy()

        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']

        logger.debug("Added 4 price features")

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        거래량 관련 파생 피처 생성

        거래량 분석 피처:
            - volume_ma5: 5일 평균 거래량
            - volume_ma20: 20일 평균 거래량
            - volume_ratio: 현재 거래량 / 20일 평균

        Args:
            df: OHLCV 데이터프레임

        Returns:
            거래량 피처가 추가된 DataFrame
        """
        df = df.copy()

        df['volume_ma5'] = df['volume'].rolling(5).mean()
        df['volume_ma20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']

        # inf 값 처리 (volume_ma20 = 0인 경우)
        df['volume_ratio'] = df['volume_ratio'].replace([np.inf, -np.inf], np.nan)

        logger.debug("Added 3 volume features")

        return df

    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        추세 관련 파생 피처 생성

        수익률 기반 추세 피처:
            - return_5d: 5일 수익률
            - return_10d: 10일 수익률
            - return_20d: 20일 수익률
            - return_60d: 60일 수익률

        Args:
            df: OHLCV 데이터프레임

        Returns:
            추세 피처가 추가된 DataFrame
        """
        df = df.copy()

        for period in [5, 10, 20, 60]:
            df[f'return_{period}d'] = df['close'].pct_change(period)

        logger.debug("Added 4 trend features")

        return df

    def create_labels(
        self,
        df: pd.DataFrame,
        forward_days: int = 1,
        threshold: float = 0.01
    ) -> pd.Series:
        """
        레이블 생성 (0: 하락, 1: 보합, 2: 상승)

        미래 N일 후 수익률을 기준으로 3-class 레이블 생성

        Args:
            df: 가격 데이터프레임 (close 컬럼 필요)
            forward_days: 미래 N일 후 수익률 (기본 1일)
            threshold: 상승/하락 판단 임계값 (1% = 0.01)

        Returns:
            Labels Series (0: 하락, 1: 보합, 2: 상승)

        Example:
            >>> # 1일 후 1% 임계값
            >>> labels = engine.create_labels(df, forward_days=1, threshold=0.01)
            >>>
            >>> # 5일 후 2% 임계값
            >>> labels = engine.create_labels(df, forward_days=5, threshold=0.02)
        """
        logger.info(
            f"Creating labels: forward_days={forward_days}, threshold={threshold:.2%}"
        )

        # forward_days일 후 수익률
        future_return = df['close'].pct_change(forward_days).shift(-forward_days)

        # 레이블 생성
        labels = pd.Series(1, index=df.index)  # 기본값: 보합
        labels[future_return < -threshold] = 0  # 하락
        labels[future_return > threshold] = 2   # 상승

        # 통계 로깅
        label_counts = labels.value_counts().sort_index()
        logger.info(
            f"Label distribution: "
            f"DOWN={label_counts.get(0, 0)} ({label_counts.get(0, 0)/len(labels):.1%}), "
            f"NEUTRAL={label_counts.get(1, 0)} ({label_counts.get(1, 0)/len(labels):.1%}), "
            f"UP={label_counts.get(2, 0)} ({label_counts.get(2, 0)/len(labels):.1%})"
        )

        return labels

    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """
        생성 가능한 모든 피처 이름 반환

        Args:
            df: OHLCV 데이터프레임

        Returns:
            피처 이름 리스트

        Example:
            >>> feature_names = engine.get_feature_names(df)
            >>> print(len(feature_names))  # 50+
        """
        result = self.create_features(df)
        return result.columns.tolist()

    def __repr__(self) -> str:
        """문자열 표현"""
        return "TechnicalFeatureEngine(indicators=TechnicalIndicators())"
