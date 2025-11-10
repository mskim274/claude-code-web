"""
추세 지표 (Trend Indicators)

이동평균 등 추세를 파악하기 위한 기술적 지표
"""
import pandas as pd
import numpy as np
from typing import Tuple

# TA-Lib import with fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False


class TrendIndicators:
    """추세 지표 계산 클래스"""

    @staticmethod
    def calculate_sma(close: pd.Series, period: int = 20) -> pd.Series:
        """
        SMA (Simple Moving Average) - 단순 이동평균

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: SMA 값

        Raises:
            ValueError: period가 0 이하인 경우
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Fallback: pandas rolling mean
            return close.rolling(window=period).mean()

        result = talib.SMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'SMA_{period}')

    @staticmethod
    def calculate_ema(close: pd.Series, period: int = 20) -> pd.Series:
        """
        EMA (Exponential Moving Average) - 지수 이동평균

        최근 데이터에 더 높은 가중치를 부여하는 이동평균

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: EMA 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Fallback: pandas ewm
            return close.ewm(span=period, adjust=False).mean()

        result = talib.EMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'EMA_{period}')

    @staticmethod
    def calculate_wma(close: pd.Series, period: int = 20) -> pd.Series:
        """
        WMA (Weighted Moving Average) - 가중 이동평균

        선형 가중치를 적용한 이동평균 (최근 데이터에 더 높은 가중치)

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: WMA 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Fallback: manual calculation
            weights = np.arange(1, period + 1)
            result = close.rolling(window=period).apply(
                lambda x: np.dot(x, weights) / weights.sum(), raw=True
            )
            return result

        result = talib.WMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'WMA_{period}')

    @staticmethod
    def calculate_dema(close: pd.Series, period: int = 20) -> pd.Series:
        """
        DEMA (Double Exponential Moving Average) - 이중 지수 이동평균

        EMA를 두 번 적용하여 지연을 줄인 이동평균

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: DEMA 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # DEMA = 2 * EMA - EMA(EMA)
            ema1 = close.ewm(span=period, adjust=False).mean()
            ema2 = ema1.ewm(span=period, adjust=False).mean()
            return 2 * ema1 - ema2

        result = talib.DEMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'DEMA_{period}')

    @staticmethod
    def calculate_tema(close: pd.Series, period: int = 20) -> pd.Series:
        """
        TEMA (Triple Exponential Moving Average) - 삼중 지수 이동평균

        EMA를 세 번 적용하여 지연을 더욱 줄인 이동평균

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: TEMA 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # TEMA = 3 * EMA - 3 * EMA(EMA) + EMA(EMA(EMA))
            ema1 = close.ewm(span=period, adjust=False).mean()
            ema2 = ema1.ewm(span=period, adjust=False).mean()
            ema3 = ema2.ewm(span=period, adjust=False).mean()
            return 3 * ema1 - 3 * ema2 + ema3

        result = talib.TEMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'TEMA_{period}')

    @staticmethod
    def calculate_trima(close: pd.Series, period: int = 20) -> pd.Series:
        """
        TRIMA (Triangular Moving Average) - 삼각 이동평균

        이동평균의 이동평균으로 부드러운 곡선 생성

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: TRIMA 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # TRIMA = SMA(SMA)
            sma1 = close.rolling(window=period).mean()
            return sma1.rolling(window=period).mean()

        result = talib.TRIMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'TRIMA_{period}')

    @staticmethod
    def calculate_kama(close: pd.Series, period: int = 20) -> pd.Series:
        """
        KAMA (Kaufman Adaptive Moving Average) - 카우프만 적응형 이동평균

        시장 변동성에 따라 적응하는 이동평균

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: KAMA 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Simplified KAMA calculation
            direction = abs(close - close.shift(period))
            volatility = close.diff().abs().rolling(window=period).sum()
            er = direction / volatility  # Efficiency Ratio
            er = er.fillna(0)

            fast_sc = 2 / (2 + 1)
            slow_sc = 2 / (30 + 1)
            sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

            kama = pd.Series(index=close.index, dtype=float)
            kama.iloc[period] = close.iloc[period]

            for i in range(period + 1, len(close)):
                kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (close.iloc[i] - kama.iloc[i-1])

            return kama

        result = talib.KAMA(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'KAMA_{period}')

    @staticmethod
    def calculate_mama(close: pd.Series, fastlimit: float = 0.5, slowlimit: float = 0.05) -> Tuple[pd.Series, pd.Series]:
        """
        MAMA (MESA Adaptive Moving Average) - MESA 적응형 이동평균

        FAMA (Following Adaptive Moving Average)와 함께 반환

        Args:
            close: 종가 시리즈
            fastlimit: 빠른 한계 (기본값: 0.5)
            slowlimit: 느린 한계 (기본값: 0.05)

        Returns:
            Tuple[pd.Series, pd.Series]: (MAMA, FAMA)
        """
        if not TALIB_AVAILABLE:
            # Fallback to EMA
            mama = close.ewm(span=12, adjust=False).mean()
            fama = close.ewm(span=26, adjust=False).mean()
            return mama, fama

        mama, fama = talib.MAMA(close.values, fastlimit=fastlimit, slowlimit=slowlimit)
        return (
            pd.Series(mama, index=close.index, name='MAMA'),
            pd.Series(fama, index=close.index, name='FAMA')
        )

    @staticmethod
    def calculate_t3(close: pd.Series, period: int = 5, vfactor: float = 0.7) -> pd.Series:
        """
        T3 (Triple Exponential Moving Average) - 삼중 지수 이동평균

        TEMA와 유사하지만 volume factor를 사용

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 5)
            vfactor: Volume factor (기본값: 0.7)

        Returns:
            pd.Series: T3 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Fallback to TEMA
            ema1 = close.ewm(span=period, adjust=False).mean()
            ema2 = ema1.ewm(span=period, adjust=False).mean()
            ema3 = ema2.ewm(span=period, adjust=False).mean()
            return 3 * ema1 - 3 * ema2 + ema3

        result = talib.T3(close.values, timeperiod=period, vfactor=vfactor)
        return pd.Series(result, index=close.index, name=f'T3_{period}')

    @staticmethod
    def calculate_sar(high: pd.Series, low: pd.Series, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """
        SAR (Parabolic SAR) - 포물선형 SAR

        추세 전환 시점을 파악하는 지표

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            acceleration: 가속 인자 (기본값: 0.02)
            maximum: 최대값 (기본값: 0.2)

        Returns:
            pd.Series: SAR 값
        """
        if not TALIB_AVAILABLE:
            # Simplified SAR calculation
            sar = pd.Series(index=high.index, dtype=float)
            sar.iloc[0] = low.iloc[0]

            for i in range(1, len(high)):
                # 간단한 SAR 근사
                if high.iloc[i] > sar.iloc[i-1]:
                    sar.iloc[i] = min(low.iloc[i-1], sar.iloc[i-1])
                else:
                    sar.iloc[i] = max(high.iloc[i-1], sar.iloc[i-1])

            return sar

        result = talib.SAR(high.values, low.values, acceleration=acceleration, maximum=maximum)
        return pd.Series(result, index=high.index, name='SAR')
