"""
거래량 지표 (Volume Indicators)

OBV, 차이킨 등 거래량을 분석하는 지표
"""
import pandas as pd
import numpy as np

# TA-Lib import with fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False


class VolumeIndicators:
    """거래량 지표 계산 클래스"""

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        OBV (On Balance Volume) - 누적 거래량

        가격 상승 시 거래량을 더하고, 하락 시 빼는 누적 지표
        가격과 거래량의 관계 분석

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: OBV 값
        """
        if not TALIB_AVAILABLE:
            obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
            return obv.rename('OBV')

        result = talib.OBV(close.values, volume.values)
        return pd.Series(result, index=close.index, name='OBV')

    @staticmethod
    def calculate_ad(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        AD (Accumulation/Distribution Line) - 차이킨 누적/분산선

        종가의 위치와 거래량을 고려한 자금 흐름 분석

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: A/D Line 값
        """
        if not TALIB_AVAILABLE:
            clv = ((close - low) - (high - close)) / (high - low)
            clv = clv.replace([np.inf, -np.inf], 0).fillna(0)
            ad = (clv * volume).cumsum()
            return ad.rename('AD')

        result = talib.AD(high.values, low.values, close.values, volume.values)
        return pd.Series(result, index=close.index, name='AD')

    @staticmethod
    def calculate_adosc(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                       fast: int = 3, slow: int = 10) -> pd.Series:
        """
        ADOSC (Chaikin A/D Oscillator) - 차이킨 A/D 오실레이터

        A/D Line의 빠른/느린 EMA 차이

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈
            fast: 빠른 EMA 기간 (기본값: 3)
            slow: 느린 EMA 기간 (기본값: 10)

        Returns:
            pd.Series: A/D Oscillator 값
        """
        if not TALIB_AVAILABLE:
            ad = VolumeIndicators.calculate_ad(high, low, close, volume)
            fast_ema = ad.ewm(span=fast, adjust=False).mean()
            slow_ema = ad.ewm(span=slow, adjust=False).mean()
            adosc = fast_ema - slow_ema
            return adosc.rename('ADOSC')

        result = talib.ADOSC(high.values, low.values, close.values, volume.values,
                            fastperiod=fast, slowperiod=slow)
        return pd.Series(result, index=close.index, name='ADOSC')

    @staticmethod
    def calculate_cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                     period: int = 20) -> pd.Series:
        """
        CMF (Chaikin Money Flow) - 차이킨 자금 흐름

        일정 기간 동안의 자금 흐름을 측정
        양수: 매수 압력, 음수: 매도 압력

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈
            period: 계산 기간 (기본값: 20)

        Returns:
            pd.Series: CMF 값 (-1 ~ 1)
        """
        # TA-Lib에는 없는 지표 - 커스텀 계산
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
        mf_volume = mfm * volume

        cmf = mf_volume.rolling(window=period).sum() / volume.rolling(window=period).sum()
        return cmf.rename(f'CMF_{period}')

    @staticmethod
    def calculate_fi(close: pd.Series, volume: pd.Series, period: int = 13) -> pd.Series:
        """
        FI (Force Index) - 포스 인덱스

        가격 변화와 거래량을 곱한 지표
        양수: 매수 압력, 음수: 매도 압력

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈
            period: EMA 기간 (기본값: 13)

        Returns:
            pd.Series: Force Index 값
        """
        fi = close.diff() * volume
        fi_ema = fi.ewm(span=period, adjust=False).mean()
        return fi_ema.rename(f'FI_{period}')

    @staticmethod
    def calculate_eom(high: pd.Series, low: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """
        EOM (Ease of Movement) - 이동 용이성

        가격 이동이 얼마나 쉬운지 측정
        높은 값: 적은 거래량으로 큰 가격 변동

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            volume: 거래량 시리즈
            period: 이동평균 기간 (기본값: 14)

        Returns:
            pd.Series: EOM 값
        """
        midpoint_move = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
        box_ratio = (volume / 100000000) / (high - low)
        box_ratio = box_ratio.replace([np.inf, -np.inf], np.nan)

        eom = midpoint_move / box_ratio
        eom = eom.replace([np.inf, -np.inf], np.nan)
        eom_ma = eom.rolling(window=period).mean()

        return eom_ma.rename(f'EOM_{period}')

    @staticmethod
    def calculate_vpt(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        VPT (Volume Price Trend) - 거래량 가격 추세

        OBV의 변형으로 가격 변화율을 고려

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: VPT 값
        """
        price_change_pct = close.pct_change()
        vpt = (price_change_pct * volume).fillna(0).cumsum()
        return vpt.rename('VPT')

    @staticmethod
    def calculate_nvi(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        NVI (Negative Volume Index) - 네거티브 볼륨 인덱스

        거래량이 감소할 때만 가격 변화를 반영
        전문 투자자의 움직임 추적

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: NVI 값
        """
        nvi = pd.Series(index=close.index, dtype=float)
        nvi.iloc[0] = 1000  # Starting value

        for i in range(1, len(close)):
            if volume.iloc[i] < volume.iloc[i-1]:
                # Volume decreased
                price_change_pct = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
                nvi.iloc[i] = nvi.iloc[i-1] + (price_change_pct * nvi.iloc[i-1])
            else:
                nvi.iloc[i] = nvi.iloc[i-1]

        return nvi.rename('NVI')

    @staticmethod
    def calculate_pvi(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        PVI (Positive Volume Index) - 포지티브 볼륨 인덱스

        거래량이 증가할 때만 가격 변화를 반영
        개인 투자자의 움직임 추적

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: PVI 값
        """
        pvi = pd.Series(index=close.index, dtype=float)
        pvi.iloc[0] = 1000  # Starting value

        for i in range(1, len(close)):
            if volume.iloc[i] > volume.iloc[i-1]:
                # Volume increased
                price_change_pct = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
                pvi.iloc[i] = pvi.iloc[i-1] + (price_change_pct * pvi.iloc[i-1])
            else:
                pvi.iloc[i] = pvi.iloc[i-1]

        return pvi.rename('PVI')

    @staticmethod
    def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        VWAP (Volume Weighted Average Price) - 거래량 가중 평균가

        거래량으로 가중치를 준 평균 가격
        기관 투자자들이 많이 사용

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: VWAP 값
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap.rename('VWAP')


class AdditionalVolumeIndicators:
    """추가 거래량 지표"""

    @staticmethod
    def calculate_vwma(close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        VWMA (Volume Weighted Moving Average) - 거래량 가중 이동평균

        거래량으로 가중치를 준 이동평균

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈
            period: 이동평균 기간 (기본값: 20)

        Returns:
            pd.Series: VWMA 값
        """
        vwma = (close * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
        return vwma.rename(f'VWMA_{period}')

    @staticmethod
    def calculate_pvt(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        PVT (Price Volume Trend) - VPT와 동일

        Args:
            close: 종가 시리즈
            volume: 거래량 시리즈

        Returns:
            pd.Series: PVT 값
        """
        return VolumeIndicators.calculate_vpt(close, volume).rename('PVT')

    @staticmethod
    def calculate_mfi_custom(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                            period: int = 14) -> pd.Series:
        """
        MFI (Money Flow Index) - 커스텀 구현

        momentum.py의 MFI와 동일하지만 volume 모듈에도 포함

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
            return mfi.rename(f'MFI_{period}')

        result = talib.MFI(high.values, low.values, close.values, volume.values, timeperiod=period)
        return pd.Series(result, index=close.index, name=f'MFI_{period}')

    @staticmethod
    def calculate_volume_oscillator(volume: pd.Series, fast: int = 5, slow: int = 10) -> pd.Series:
        """
        Volume Oscillator - 거래량 오실레이터

        빠른/느린 거래량 이동평균의 차이를 퍼센트로 표시

        Args:
            volume: 거래량 시리즈
            fast: 빠른 이동평균 기간 (기본값: 5)
            slow: 느린 이동평균 기간 (기본값: 10)

        Returns:
            pd.Series: Volume Oscillator 값 (%)
        """
        fast_ma = volume.rolling(window=fast).mean()
        slow_ma = volume.rolling(window=slow).mean()
        vol_osc = ((fast_ma - slow_ma) / slow_ma) * 100
        return vol_osc.rename(f'VO_{fast}_{slow}')

    @staticmethod
    def calculate_volume_rate_of_change(volume: pd.Series, period: int = 14) -> pd.Series:
        """
        Volume ROC - 거래량 변화율

        거래량의 변화율

        Args:
            volume: 거래량 시리즈
            period: 비교 기간 (기본값: 14)

        Returns:
            pd.Series: Volume ROC 값 (%)
        """
        vroc = ((volume - volume.shift(period)) / volume.shift(period)) * 100
        return vroc.rename(f'VROC_{period}')

    @staticmethod
    def calculate_klinger_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                                     fast: int = 34, slow: int = 55, signal: int = 13) -> pd.Series:
        """
        Klinger Oscillator - 클링거 오실레이터

        장기 자금 흐름을 측정하는 거래량 기반 지표

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈
            fast: 빠른 EMA 기간 (기본값: 34)
            slow: 느린 EMA 기간 (기본값: 55)
            signal: 시그널선 기간 (기본값: 13)

        Returns:
            pd.Series: Klinger Oscillator 값
        """
        # Trend calculation
        typical_price = (high + low + close) / 3
        trend = (typical_price > typical_price.shift(1)).astype(int) * 2 - 1

        # Volume Force
        dm = high - low
        cm = dm.cumsum()
        vf = volume * trend * dm / cm * 100
        vf = vf.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Klinger Oscillator
        ko = vf.ewm(span=fast, adjust=False).mean() - vf.ewm(span=slow, adjust=False).mean()

        return ko.rename('KO')

    @staticmethod
    def calculate_accumulation_distribution_rating(high: pd.Series, low: pd.Series, close: pd.Series,
                                                   volume: pd.Series, period: int = 14) -> pd.Series:
        """
        Accumulation/Distribution Rating - 누적/분산 등급

        일정 기간 동안의 A/D 라인의 변화를 등급화

        Args:
            high: 고가 시리즈
            low: 저가 시리즈
            close: 종가 시리즈
            volume: 거래량 시리즈
            period: 계산 기간 (기본값: 14)

        Returns:
            pd.Series: A/D Rating 값
        """
        ad = VolumeIndicators.calculate_ad(high, low, close, volume)
        ad_roc = ad.diff(period)
        ad_rating = (ad_roc.rank(pct=True) - 0.5) * 200  # -100 to 100 scale
        return ad_rating.rename(f'AD_Rating_{period}')
