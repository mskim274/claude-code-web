"""
모멘텀 지표 (Momentum Indicators)

RSI, MACD 등 가격 변화의 속도와 강도를 측정하는 지표
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


class MomentumIndicators:
    """모멘텀 지표 계산 클래스"""

    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) - 상대강도지수

        과매수/과매도 상태를 파악하는 지표 (0-100 범위)
        70 이상: 과매수, 30 이하: 과매도

        Args:
            close: 종가 시리즈
            period: RSI 계산 기간 (기본값: 14)

        Returns:
            pd.Series: RSI 값 (0-100)
        """
        if period <= 0:
            raise ValueError("period must be greater than 0")

        if not TALIB_AVAILABLE:
            # Fallback calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        result = talib.RSI(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'RSI_{period}')

    @staticmethod
    def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)

        추세의 강도, 방향, 모멘텀을 파악하는 지표

        Args:
            close: 종가 시리즈
            fast: 빠른 EMA 기간 (기본값: 12)
            slow: 느린 EMA 기간 (기본값: 26)
            signal_period: 시그널선 기간 (기본값: 9)

        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (MACD, Signal, Histogram)
        """
        if not TALIB_AVAILABLE:
            # Fallback calculation
            ema_fast = close.ewm(span=fast, adjust=False).mean()
            ema_slow = close.ewm(span=slow, adjust=False).mean()
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            hist = macd - signal
            return macd, signal, hist

        macd, signal, hist = talib.MACD(close.values, fastperiod=fast, slowperiod=slow, signalperiod=signal_period)
        return (
            pd.Series(macd, index=close.index, name='MACD'),
            pd.Series(signal, index=close.index, name='MACD_Signal'),
            pd.Series(hist, index=close.index, name='MACD_Hist')
        )

    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                            fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator - 스토캐스틱

        현재가가 일정 기간의 최고가/최저가 범위에서 어디에 위치하는지 표시 (0-100 범위)

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            fastk_period: Fast %K 기간 (기본값: 14)
            slowk_period: Slow %K 기간 (기본값: 3)
            slowd_period: Slow %D 기간 (기본값: 3)

        Returns:
            Tuple[pd.Series, pd.Series]: (Slow %K, Slow %D)
        """
        if not TALIB_AVAILABLE:
            # Fallback calculation
            lowest_low = low.rolling(window=fastk_period).min()
            highest_high = high.rolling(window=fastk_period).max()
            fastk = 100 * (close - lowest_low) / (highest_high - lowest_low)
            slowk = fastk.rolling(window=slowk_period).mean()
            slowd = slowk.rolling(window=slowd_period).mean()
            return slowk, slowd

        slowk, slowd = talib.STOCH(high.values, low.values, close.values,
                                   fastk_period=fastk_period, slowk_period=slowk_period,
                                   slowk_matype=0, slowd_period=slowd_period, slowd_matype=0)
        return (
            pd.Series(slowk, index=close.index, name='STOCH_K'),
            pd.Series(slowd, index=close.index, name='STOCH_D')
        )

    @staticmethod
    def calculate_stochastic_rsi(close: pd.Series, period: int = 14,
                                fastk_period: int = 14, fastd_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic RSI - 스토캐스틱 RSI

        RSI에 스토캐스틱 공식을 적용한 지표

        Args:
            close: 종가 시리즈
            period: RSI 기간 (기본값: 14)
            fastk_period: Fast %K 기간 (기본값: 14)
            fastd_period: Fast %D 기간 (기본값: 3)

        Returns:
            Tuple[pd.Series, pd.Series]: (Fast %K, Fast %D)
        """
        if not TALIB_AVAILABLE:
            # Calculate RSI first
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Apply stochastic to RSI
            lowest_rsi = rsi.rolling(window=fastk_period).min()
            highest_rsi = rsi.rolling(window=fastk_period).max()
            fastk = 100 * (rsi - lowest_rsi) / (highest_rsi - lowest_rsi)
            fastd = fastk.rolling(window=fastd_period).mean()
            return fastk, fastd

        fastk, fastd = talib.STOCHRSI(close.values, timeperiod=period,
                                      fastk_period=fastk_period, fastd_period=fastd_period,
                                      fastd_matype=0)
        return (
            pd.Series(fastk, index=close.index, name='STOCHRSI_K'),
            pd.Series(fastd, index=close.index, name='STOCHRSI_D')
        )

    @staticmethod
    def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        CCI (Commodity Channel Index) - 상품 채널 지수

        가격이 평균에서 얼마나 벗어났는지 측정 (일반적으로 -100 ~ +100)

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: CCI 값
        """
        if not TALIB_AVAILABLE:
            tp = (high + low + close) / 3
            sma = tp.rolling(window=period).mean()
            mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
            cci = (tp - sma) / (0.015 * mad)
            return cci

        result = talib.CCI(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'CCI_{period}')

    @staticmethod
    def calculate_roc(close: pd.Series, period: int = 10) -> pd.Series:
        """
        ROC (Rate of Change) - 변화율

        현재가와 N일 전 가격의 변화율 (%)

        Args:
            close: 종가 시리즈
            period: 비교 기간 (기본값: 10)

        Returns:
            pd.Series: ROC 값 (%)
        """
        if not TALIB_AVAILABLE:
            roc = ((close - close.shift(period)) / close.shift(period)) * 100
            return roc

        result = talib.ROC(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'ROC_{period}')

    @staticmethod
    def calculate_mom(close: pd.Series, period: int = 10) -> pd.Series:
        """
        MOM (Momentum) - 모멘텀

        현재가와 N일 전 가격의 차이

        Args:
            close: 종가 시리즈
            period: 비교 기간 (기본값: 10)

        Returns:
            pd.Series: Momentum 값
        """
        if not TALIB_AVAILABLE:
            mom = close - close.shift(period)
            return mom

        result = talib.MOM(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'MOM_{period}')

    @staticmethod
    def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """
        MFI (Money Flow Index) - 자금 흐름 지수

        거래량을 고려한 RSI (0-100 범위)

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: MFI 값 (0-100)
        """
        if not TALIB_AVAILABLE:
            tp = (high + low + close) / 3
            mf = tp * volume
            mf_pos = mf.where(tp > tp.shift(1), 0).rolling(window=period).sum()
            mf_neg = mf.where(tp < tp.shift(1), 0).rolling(window=period).sum()
            mfr = mf_pos / mf_neg
            mfi = 100 - (100 / (1 + mfr))
            return mfi

        result = talib.MFI(high.values, low.values, close.values, volume.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'MFI_{period}')

    @staticmethod
    def calculate_willr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        WILLR (Williams' %R) - 윌리엄스 %R

        스토캐스틱과 유사하지만 -100 ~ 0 범위로 표시
        -20 이상: 과매수, -80 이하: 과매도

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: Williams %R 값 (-100 ~ 0)
        """
        if not TALIB_AVAILABLE:
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            willr = -100 * (highest_high - close) / (highest_high - lowest_low)
            return willr

        result = talib.WILLR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'WILLR_{period}')

    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        ADX (Average Directional Movement Index) - 평균 방향성 지수

        추세의 강도를 측정 (0-100, 높을수록 강한 추세)
        25 이상: 강한 추세

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: ADX 값
        """
        if not TALIB_AVAILABLE:
            # Simplified ADX calculation
            tr = pd.DataFrame({
                'hl': high - low,
                'hc': abs(high - close.shift(1)),
                'lc': abs(low - close.shift(1))
            }).max(axis=1)

            atr = tr.rolling(window=period).mean()
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low

            plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
            minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            return adx

        result = talib.ADX(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'ADX_{period}')

    @staticmethod
    def calculate_adxr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        ADXR (Average Directional Movement Index Rating)

        ADX의 이동평균

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: ADXR 값
        """
        if not TALIB_AVAILABLE:
            # Fallback to ADX
            return MomentumIndicators.calculate_adx(high, low, close, period)

        result = talib.ADXR(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'ADXR_{period}')

    @staticmethod
    def calculate_apo(close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """
        APO (Absolute Price Oscillator) - 절대 가격 오실레이터

        MACD와 유사하지만 시그널선 없이 단일 라인

        Args:
            close: 종가 시리즈
            fast: 빠른 EMA 기간 (기본값: 12)
            slow: 느린 EMA 기간 (기본값: 26)

        Returns:
            pd.Series: APO 값
        """
        if not TALIB_AVAILABLE:
            ema_fast = close.ewm(span=fast, adjust=False).mean()
            ema_slow = close.ewm(span=slow, adjust=False).mean()
            return ema_fast - ema_slow

        result = talib.APO(close.values, fastperiod=fast, slowperiod=slow, matype=0)
        return pd.Series(result, index=close.index, name='APO')

    @staticmethod
    def calculate_aroon(high: pd.Series, low: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """
        Aroon Indicator - 아론 지표

        추세의 시작과 강도를 측정 (0-100 범위)

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            Tuple[pd.Series, pd.Series]: (Aroon Up, Aroon Down)
        """
        if not TALIB_AVAILABLE:
            aroon_up = high.rolling(window=period + 1).apply(
                lambda x: (period - x.argmax()) / period * 100, raw=False
            )
            aroon_down = low.rolling(window=period + 1).apply(
                lambda x: (period - x.argmin()) / period * 100, raw=False
            )
            return aroon_up, aroon_down

        aroon_up, aroon_down = talib.AROON(high.values, low.values, timeperiod=period)
        return (
            pd.Series(aroon_up, index=high.index, name='AROON_UP'),
            pd.Series(aroon_down, index=low.index, name='AROON_DOWN')
        )

    @staticmethod
    def calculate_aroonosc(high: pd.Series, low: pd.Series, period: int = 14) -> pd.Series:
        """
        Aroon Oscillator - 아론 오실레이터

        Aroon Up - Aroon Down (-100 ~ 100 범위)

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: Aroon Oscillator 값
        """
        if not TALIB_AVAILABLE:
            aroon_up, aroon_down = MomentumIndicators.calculate_aroon(high, low, period)
            return aroon_up - aroon_down

        result = talib.AROONOSC(high.values, low.values, timeperiod=period)
        return pd.Series(result, index=high.index, name='AROONOSC')

    @staticmethod
    def calculate_bop(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        BOP (Balance Of Power) - 세력 균형

        매수/매도 압력의 균형을 측정

        Args:
            open_: 시가 시리즈
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈

        Returns:
            pd.Series: BOP 값
        """
        if not TALIB_AVAILABLE:
            bop = (close - open_) / (high - low)
            bop = bop.replace([np.inf, -np.inf], np.nan)
            return bop

        result = talib.BOP(open_.values, high.values, low.values, close.values)
        return pd.Series(result, index=close.index, name='BOP')

    @staticmethod
    def calculate_cmo(close: pd.Series, period: int = 14) -> pd.Series:
        """
        CMO (Chande Momentum Oscillator) - 찬드 모멘텀 오실레이터

        RSI와 유사하지만 -100 ~ 100 범위

        Args:
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: CMO 값 (-100 ~ 100)
        """
        if not TALIB_AVAILABLE:
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).sum()
            loss = -delta.where(delta < 0, 0).rolling(window=period).sum()
            cmo = 100 * (gain - loss) / (gain + loss)
            return cmo

        result = talib.CMO(close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'CMO_{period}')

    @staticmethod
    def calculate_dx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        DX (Directional Movement Index) - 방향성 지수

        ADX의 기초가 되는 지표

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: DX 값
        """
        if not TALIB_AVAILABLE:
            # Simplified calculation - use ADX as approximation
            return MomentumIndicators.calculate_adx(high, low, close, period)

        result = talib.DX(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'DX_{period}')

    @staticmethod
    def calculate_minus_di(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        MINUS_DI (Minus Directional Indicator) - 마이너스 방향성 지표

        하락 추세의 강도 측정

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: -DI 값
        """
        if not TALIB_AVAILABLE:
            tr = pd.DataFrame({
                'hl': high - low,
                'hc': abs(high - close.shift(1)),
                'lc': abs(low - close.shift(1))
            }).max(axis=1)

            atr = tr.rolling(window=period).mean()
            down_move = low.shift(1) - low
            minus_dm = down_move.where(down_move > 0, 0)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
            return minus_di

        result = talib.MINUS_DI(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'MINUS_DI_{period}')

    @staticmethod
    def calculate_plus_di(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        PLUS_DI (Plus Directional Indicator) - 플러스 방향성 지표

        상승 추세의 강도 측정

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: +DI 값
        """
        if not TALIB_AVAILABLE:
            tr = pd.DataFrame({
                'hl': high - low,
                'hc': abs(high - close.shift(1)),
                'lc': abs(low - close.shift(1))
            }).max(axis=1)

            atr = tr.rolling(window=period).mean()
            up_move = high - high.shift(1)
            plus_dm = up_move.where(up_move > 0, 0)
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            return plus_di

        result = talib.PLUS_DI(high.values, low.values, close.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'PLUS_DI_{period}')

    @staticmethod
    def calculate_ppo(close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """
        PPO (Percentage Price Oscillator) - 퍼센트 가격 오실레이터

        MACD의 퍼센트 버전

        Args:
            close: 종가 시리즈
            fast: 빠른 EMA 기간 (기본값: 12)
            slow: 느린 EMA 기간 (기본값: 26)

        Returns:
            pd.Series: PPO 값 (%)
        """
        if not TALIB_AVAILABLE:
            ema_fast = close.ewm(span=fast, adjust=False).mean()
            ema_slow = close.ewm(span=slow, adjust=False).mean()
            ppo = ((ema_fast - ema_slow) / ema_slow) * 100
            return ppo

        result = talib.PPO(close.values, fastperiod=fast, slowperiod=slow, matype=0)
        return pd.Series(result, index=close.index, name='PPO')
