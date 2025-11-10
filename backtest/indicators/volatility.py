"""
변동성 지표 (Volatility Indicators)

볼린저 밴드, ATR 등 가격 변동성을 측정하는 지표
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


class VolatilityIndicators:
    """변동성 지표 계산 클래스"""

    @staticmethod
    def calculate_bollinger_bands(close: pd.Series, period: int = 20, std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands - 볼린저 밴드

        가격의 변동성을 표준편차를 이용하여 표시
        상단밴드: 과매수 신호
        하단밴드: 과매도 신호

        Args:
            close: 종가 시리즈
            period: 이동평균 기간 (기본값: 20)
            std: 표준편차 배수 (기본값: 2)

        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (Upper Band, Middle Band, Lower Band)
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Fallback calculation
            middle = close.rolling(window=period).mean()
            std_dev = close.rolling(window=period).std()
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            return upper, middle, lower

        upper, middle, lower = talib.BBANDS(close.values, timeperiod=period, nbdevup=std, nbdevdn=std, matype=0)
        return (
            pd.Series(upper, index=close.index, name='BB_Upper'),
            pd.Series(middle, index=close.index, name='BB_Middle'),
            pd.Series(lower, index=close.index, name='BB_Lower')
        )

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        ATR (Average True Range) - 평균 진실 범위

        가격 변동성의 크기를 측정 (항상 양수)
        높을수록 변동성이 큼

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 평균 기간 (기본값: 14)

        Returns:
            pd.Series: ATR 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # True Range calculation
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return atr

        result = talib.ATR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'ATR_{period}')

    @staticmethod
    def calculate_natr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        NATR (Normalized Average True Range) - 정규화된 ATR

        ATR을 현재가로 나눈 백분율 버전

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 평균 기간 (기본값: 14)

        Returns:
            pd.Series: NATR 값 (%)
        """
        if not TALIB_AVAILABLE:
            atr = VolatilityIndicators.calculate_atr(high, low, close, period)
            natr = (atr / close) * 100
            return natr

        result = talib.NATR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'NATR_{period}')

    @staticmethod
    def calculate_trange(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        TRANGE (True Range) - 진실 범위

        당일의 실제 가격 변동 범위

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈

        Returns:
            pd.Series: True Range 값
        """
        if not TALIB_AVAILABLE:
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr

        result = talib.TRANGE(high.values, low.values, close.values)
        return pd.Series(result, index=close.index, name='TRANGE')

    @staticmethod
    def calculate_keltner_channel(high: pd.Series, low: pd.Series, close: pd.Series,
                                  period: int = 20, multiplier: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channel - 켈트너 채널

        ATR을 사용한 변동성 채널
        볼린저 밴드와 유사하지만 ATR 사용

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: EMA 기간 (기본값: 20)
            multiplier: ATR 배수 (기본값: 2)

        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (Upper Channel, Middle Channel, Lower Channel)
        """
        if not TALIB_AVAILABLE:
            middle = close.ewm(span=period, adjust=False).mean()

            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()

            upper = middle + (multiplier * atr)
            lower = middle - (multiplier * atr)
            return upper, middle, lower

        # Use EMA for middle line
        middle = pd.Series(talib.EMA(close.values, timeperiod=period), index=close.index)
        atr = VolatilityIndicators.calculate_atr(high, low, close, period)

        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)

        return (
            upper.rename('KC_Upper'),
            middle.rename('KC_Middle'),
            lower.rename('KC_Lower')
        )

    @staticmethod
    def calculate_donchian_channel(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Donchian Channel - 돈치안 채널

        일정 기간의 최고가/최저가를 사용한 채널
        추세 추종 전략에 사용

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            period: 조회 기간 (기본값: 20)

        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (Upper Channel, Middle Channel, Lower Channel)
        """
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()
        middle = (upper + lower) / 2

        return (
            upper.rename('DC_Upper'),
            middle.rename('DC_Middle'),
            lower.rename('DC_Lower')
        )

    @staticmethod
    def calculate_stddev(close: pd.Series, period: int = 20) -> pd.Series:
        """
        STDDEV (Standard Deviation) - 표준편차

        가격의 표준편차로 변동성 측정

        Args:
            close: 종가 시리즈
            period: 계산 기간 (기본값: 20)

        Returns:
            pd.Series: 표준편차 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            return close.rolling(window=period).std()

        result = talib.STDDEV(close.values, timeperiod=period, nbdev=1)
        return pd.Series(result, index=close.index, name=f'STDDEV_{period}')

    @staticmethod
    def calculate_var(close: pd.Series, period: int = 20) -> pd.Series:
        """
        VAR (Variance) - 분산

        가격의 분산으로 변동성 측정

        Args:
            close: 종가 시리즈
            period: 계산 기간 (기본값: 20)

        Returns:
            pd.Series: 분산 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            return close.rolling(window=period).var()

        result = talib.VAR(close.values, timeperiod=period, nbdev=1)
        return pd.Series(result, index=close.index, name=f'VAR_{period}')

    @staticmethod
    def calculate_linearreg(close: pd.Series, period: int = 14) -> pd.Series:
        """
        LINEARREG (Linear Regression) - 선형 회귀

        최소자승법을 이용한 추세선

        Args:
            close: 종가 시리즈
            period: 회귀 기간 (기본값: 14)

        Returns:
            pd.Series: 선형 회귀 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            def linear_regression(values):
                if len(values) < period:
                    return np.nan
                x = np.arange(len(values))
                y = values
                slope, intercept = np.polyfit(x, y, 1)
                return slope * (len(values) - 1) + intercept

            return close.rolling(window=period).apply(linear_regression, raw=True)

        result = talib.LINEARREG(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'LINEARREG_{period}')

    @staticmethod
    def calculate_tsf(close: pd.Series, period: int = 14) -> pd.Series:
        """
        TSF (Time Series Forecast) - 시계열 예측

        선형 회귀를 이용한 다음 값 예측

        Args:
            close: 종가 시리즈
            period: 예측 기간 (기본값: 14)

        Returns:
            pd.Series: 예측 값
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            def time_series_forecast(values):
                if len(values) < period:
                    return np.nan
                x = np.arange(len(values))
                y = values
                slope, intercept = np.polyfit(x, y, 1)
                return slope * len(values) + intercept  # Forecast next value

            return close.rolling(window=period).apply(time_series_forecast, raw=True)

        result = talib.TSF(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'TSF_{period}')


class AdditionalVolatilityIndicators:
    """추가 변동성 지표"""

    @staticmethod
    def calculate_historical_volatility(close: pd.Series, period: int = 20, trading_days: int = 252) -> pd.Series:
        """
        Historical Volatility - 역사적 변동성

        로그 수익률의 표준편차를 연율화

        Args:
            close: 종가 시리즈
            period: 계산 기간 (기본값: 20)
            trading_days: 연간 거래일 수 (기본값: 252)

        Returns:
            pd.Series: 연율화된 변동성 (%)
        """
        log_returns = np.log(close / close.shift(1))
        volatility = log_returns.rolling(window=period).std() * np.sqrt(trading_days) * 100
        return volatility.rename(f'HV_{period}')

    @staticmethod
    def calculate_ulcer_index(close: pd.Series, period: int = 14) -> pd.Series:
        """
        Ulcer Index - 울서 지수

        하락 변동성만을 측정하는 지표

        Args:
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: Ulcer Index 값
        """
        max_close = close.rolling(window=period).max()
        percentage_drawdown = 100 * (close - max_close) / max_close
        squared_avg = (percentage_drawdown ** 2).rolling(window=period).mean()
        ulcer = np.sqrt(squared_avg)
        return ulcer.rename(f'ULCER_{period}')

    @staticmethod
    def calculate_chandelier_exit(high: pd.Series, low: pd.Series, close: pd.Series,
                                  period: int = 22, multiplier: float = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Chandelier Exit - 샹들리에 출구

        ATR을 사용한 트레일링 스톱

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: ATR 기간 (기본값: 22)
            multiplier: ATR 배수 (기본값: 3)

        Returns:
            Tuple[pd.Series, pd.Series]: (Long Exit, Short Exit)
        """
        atr = VolatilityIndicators.calculate_atr(high, low, close, period)
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        long_exit = highest_high - (multiplier * atr)
        short_exit = lowest_low + (multiplier * atr)

        return (
            long_exit.rename('CE_Long'),
            short_exit.rename('CE_Short')
        )
