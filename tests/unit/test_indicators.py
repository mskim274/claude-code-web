"""
기술적 지표 테스트

TA-Lib을 사용한 기술적 지표 계산 함수들의 단위 테스트
"""
import pytest
import pandas as pd
import numpy as np
from typing import Tuple

# TA-Lib import with fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

from backtest.indicators.talib_wrapper import TechnicalIndicators


pytestmark = pytest.mark.skipif(not TALIB_AVAILABLE, reason="TA-Lib not installed")


class TestTrendIndicators:
    """추세 지표 테스트 (10개)"""

    def test_sma_calculation(self, sample_ohlcv):
        """SMA (Simple Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        sma = indicators.calculate_sma(sample_ohlcv['close'], period=20)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_ohlcv)
        # 처음 19개는 NaN이어야 함
        assert sma.iloc[:19].isna().all()
        # 20번째부터는 값이 있어야 함
        assert sma.iloc[19:].notna().any()

    def test_ema_calculation(self, sample_ohlcv):
        """EMA (Exponential Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        ema = indicators.calculate_ema(sample_ohlcv['close'], period=12)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_ohlcv)
        # EMA는 첫 번째 값부터 계산됨 (SMA보다 빠르게 반응)
        assert ema.notna().any()

    def test_wma_calculation(self, sample_ohlcv):
        """WMA (Weighted Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        wma = indicators.calculate_wma(sample_ohlcv['close'], period=20)

        assert isinstance(wma, pd.Series)
        assert len(wma) == len(sample_ohlcv)
        assert wma.notna().any()

    def test_dema_calculation(self, sample_ohlcv):
        """DEMA (Double Exponential Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        dema = indicators.calculate_dema(sample_ohlcv['close'], period=20)

        assert isinstance(dema, pd.Series)
        assert len(dema) == len(sample_ohlcv)
        assert dema.notna().any()

    def test_tema_calculation(self, sample_ohlcv):
        """TEMA (Triple Exponential Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        tema = indicators.calculate_tema(sample_ohlcv['close'], period=20)

        assert isinstance(tema, pd.Series)
        assert len(tema) == len(sample_ohlcv)
        assert tema.notna().any()

    def test_trima_calculation(self, sample_ohlcv):
        """TRIMA (Triangular Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        trima = indicators.calculate_trima(sample_ohlcv['close'], period=20)

        assert isinstance(trima, pd.Series)
        assert len(trima) == len(sample_ohlcv)
        assert trima.notna().any()

    def test_kama_calculation(self, sample_ohlcv):
        """KAMA (Kaufman Adaptive Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        kama = indicators.calculate_kama(sample_ohlcv['close'], period=20)

        assert isinstance(kama, pd.Series)
        assert len(kama) == len(sample_ohlcv)
        assert kama.notna().any()

    def test_mama_calculation(self, sample_ohlcv):
        """MAMA (MESA Adaptive Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        mama, fama = indicators.calculate_mama(sample_ohlcv['close'])

        assert isinstance(mama, pd.Series)
        assert isinstance(fama, pd.Series)
        assert len(mama) == len(sample_ohlcv)
        assert len(fama) == len(sample_ohlcv)
        assert mama.notna().any()
        assert fama.notna().any()

    def test_t3_calculation(self, sample_ohlcv):
        """T3 (Triple Exponential Moving Average) 계산 테스트"""
        indicators = TechnicalIndicators()
        t3 = indicators.calculate_t3(sample_ohlcv['close'], period=5)

        assert isinstance(t3, pd.Series)
        assert len(t3) == len(sample_ohlcv)
        assert t3.notna().any()

    def test_sar_calculation(self, sample_ohlcv):
        """SAR (Parabolic SAR) 계산 테스트"""
        indicators = TechnicalIndicators()
        sar = indicators.calculate_sar(sample_ohlcv['high'], sample_ohlcv['low'])

        assert isinstance(sar, pd.Series)
        assert len(sar) == len(sample_ohlcv)
        assert sar.notna().any()


class TestMomentumIndicators:
    """모멘텀 지표 테스트 (20개)"""

    def test_rsi_calculation(self, sample_ohlcv):
        """RSI (Relative Strength Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        rsi = indicators.calculate_rsi(sample_ohlcv['close'], period=14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_ohlcv)
        # RSI는 0-100 범위
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all()
            assert (valid_rsi <= 100).all()

    def test_macd_calculation(self, sample_ohlcv):
        """MACD (Moving Average Convergence Divergence) 계산 테스트"""
        indicators = TechnicalIndicators()
        macd, signal, hist = indicators.calculate_macd(
            sample_ohlcv['close'], fast=12, slow=26, signal_period=9
        )

        assert isinstance(macd, pd.Series)
        assert isinstance(signal, pd.Series)
        assert isinstance(hist, pd.Series)
        assert len(macd) == len(sample_ohlcv)
        assert len(signal) == len(sample_ohlcv)
        assert len(hist) == len(sample_ohlcv)
        assert macd.notna().any()

    def test_stochastic_calculation(self, sample_ohlcv):
        """Stochastic Oscillator 계산 테스트"""
        indicators = TechnicalIndicators()
        slowk, slowd = indicators.calculate_stochastic(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close']
        )

        assert isinstance(slowk, pd.Series)
        assert isinstance(slowd, pd.Series)
        assert len(slowk) == len(sample_ohlcv)
        assert len(slowd) == len(sample_ohlcv)
        # Stochastic은 0-100 범위
        valid_k = slowk.dropna()
        if len(valid_k) > 0:
            assert (valid_k >= 0).all()
            assert (valid_k <= 100).all()

    def test_stochastic_rsi_calculation(self, sample_ohlcv):
        """Stochastic RSI 계산 테스트"""
        indicators = TechnicalIndicators()
        fastk, fastd = indicators.calculate_stochastic_rsi(sample_ohlcv['close'])

        assert isinstance(fastk, pd.Series)
        assert isinstance(fastd, pd.Series)
        assert len(fastk) == len(sample_ohlcv)
        assert len(fastd) == len(sample_ohlcv)

    def test_cci_calculation(self, sample_ohlcv):
        """CCI (Commodity Channel Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        cci = indicators.calculate_cci(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(cci, pd.Series)
        assert len(cci) == len(sample_ohlcv)
        assert cci.notna().any()

    def test_roc_calculation(self, sample_ohlcv):
        """ROC (Rate of Change) 계산 테스트"""
        indicators = TechnicalIndicators()
        roc = indicators.calculate_roc(sample_ohlcv['close'], period=10)

        assert isinstance(roc, pd.Series)
        assert len(roc) == len(sample_ohlcv)
        assert roc.notna().any()

    def test_mom_calculation(self, sample_ohlcv):
        """MOM (Momentum) 계산 테스트"""
        indicators = TechnicalIndicators()
        mom = indicators.calculate_mom(sample_ohlcv['close'], period=10)

        assert isinstance(mom, pd.Series)
        assert len(mom) == len(sample_ohlcv)
        assert mom.notna().any()

    def test_mfi_calculation(self, sample_ohlcv):
        """MFI (Money Flow Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        mfi = indicators.calculate_mfi(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume'], period=14
        )

        assert isinstance(mfi, pd.Series)
        assert len(mfi) == len(sample_ohlcv)
        # MFI는 0-100 범위
        valid_mfi = mfi.dropna()
        if len(valid_mfi) > 0:
            assert (valid_mfi >= 0).all()
            assert (valid_mfi <= 100).all()

    def test_willr_calculation(self, sample_ohlcv):
        """WILLR (Williams' %R) 계산 테스트"""
        indicators = TechnicalIndicators()
        willr = indicators.calculate_willr(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(willr, pd.Series)
        assert len(willr) == len(sample_ohlcv)
        # WILLR은 -100 ~ 0 범위
        valid_willr = willr.dropna()
        if len(valid_willr) > 0:
            assert (valid_willr >= -100).all()
            assert (valid_willr <= 0).all()

    def test_adx_calculation(self, sample_ohlcv):
        """ADX (Average Directional Movement Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        adx = indicators.calculate_adx(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(adx, pd.Series)
        assert len(adx) == len(sample_ohlcv)
        assert adx.notna().any()

    def test_adxr_calculation(self, sample_ohlcv):
        """ADXR (Average Directional Movement Index Rating) 계산 테스트"""
        indicators = TechnicalIndicators()
        adxr = indicators.calculate_adxr(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(adxr, pd.Series)
        assert len(adxr) == len(sample_ohlcv)
        assert adxr.notna().any()

    def test_apo_calculation(self, sample_ohlcv):
        """APO (Absolute Price Oscillator) 계산 테스트"""
        indicators = TechnicalIndicators()
        apo = indicators.calculate_apo(sample_ohlcv['close'], fast=12, slow=26)

        assert isinstance(apo, pd.Series)
        assert len(apo) == len(sample_ohlcv)
        assert apo.notna().any()

    def test_aroon_calculation(self, sample_ohlcv):
        """Aroon Indicator 계산 테스트"""
        indicators = TechnicalIndicators()
        aroon_up, aroon_down = indicators.calculate_aroon(
            sample_ohlcv['high'], sample_ohlcv['low'], period=14
        )

        assert isinstance(aroon_up, pd.Series)
        assert isinstance(aroon_down, pd.Series)
        assert len(aroon_up) == len(sample_ohlcv)
        assert len(aroon_down) == len(sample_ohlcv)
        # Aroon은 0-100 범위
        valid_up = aroon_up.dropna()
        if len(valid_up) > 0:
            assert (valid_up >= 0).all()
            assert (valid_up <= 100).all()

    def test_aroonosc_calculation(self, sample_ohlcv):
        """Aroon Oscillator 계산 테스트"""
        indicators = TechnicalIndicators()
        aroonosc = indicators.calculate_aroonosc(
            sample_ohlcv['high'], sample_ohlcv['low'], period=14
        )

        assert isinstance(aroonosc, pd.Series)
        assert len(aroonosc) == len(sample_ohlcv)
        # Aroon Oscillator는 -100 ~ 100 범위
        valid_osc = aroonosc.dropna()
        if len(valid_osc) > 0:
            assert (valid_osc >= -100).all()
            assert (valid_osc <= 100).all()

    def test_bop_calculation(self, sample_ohlcv):
        """BOP (Balance Of Power) 계산 테스트"""
        indicators = TechnicalIndicators()
        bop = indicators.calculate_bop(
            sample_ohlcv['open'], sample_ohlcv['high'],
            sample_ohlcv['low'], sample_ohlcv['close']
        )

        assert isinstance(bop, pd.Series)
        assert len(bop) == len(sample_ohlcv)
        assert bop.notna().any()

    def test_cmo_calculation(self, sample_ohlcv):
        """CMO (Chande Momentum Oscillator) 계산 테스트"""
        indicators = TechnicalIndicators()
        cmo = indicators.calculate_cmo(sample_ohlcv['close'], period=14)

        assert isinstance(cmo, pd.Series)
        assert len(cmo) == len(sample_ohlcv)
        # CMO는 -100 ~ 100 범위
        valid_cmo = cmo.dropna()
        if len(valid_cmo) > 0:
            assert (valid_cmo >= -100).all()
            assert (valid_cmo <= 100).all()

    def test_dx_calculation(self, sample_ohlcv):
        """DX (Directional Movement Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        dx = indicators.calculate_dx(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(dx, pd.Series)
        assert len(dx) == len(sample_ohlcv)
        assert dx.notna().any()

    def test_minus_di_calculation(self, sample_ohlcv):
        """MINUS_DI (Minus Directional Indicator) 계산 테스트"""
        indicators = TechnicalIndicators()
        minus_di = indicators.calculate_minus_di(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(minus_di, pd.Series)
        assert len(minus_di) == len(sample_ohlcv)
        assert minus_di.notna().any()

    def test_plus_di_calculation(self, sample_ohlcv):
        """PLUS_DI (Plus Directional Indicator) 계산 테스트"""
        indicators = TechnicalIndicators()
        plus_di = indicators.calculate_plus_di(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(plus_di, pd.Series)
        assert len(plus_di) == len(sample_ohlcv)
        assert plus_di.notna().any()

    def test_ppo_calculation(self, sample_ohlcv):
        """PPO (Percentage Price Oscillator) 계산 테스트"""
        indicators = TechnicalIndicators()
        ppo = indicators.calculate_ppo(sample_ohlcv['close'], fast=12, slow=26)

        assert isinstance(ppo, pd.Series)
        assert len(ppo) == len(sample_ohlcv)
        assert ppo.notna().any()


class TestVolatilityIndicators:
    """변동성 지표 테스트 (10개)"""

    def test_bollinger_bands_calculation(self, sample_ohlcv):
        """Bollinger Bands 계산 테스트"""
        indicators = TechnicalIndicators()
        upper, middle, lower = indicators.calculate_bollinger_bands(
            sample_ohlcv['close'], period=20, std=2
        )

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_ohlcv)
        assert len(middle) == len(sample_ohlcv)
        assert len(lower) == len(sample_ohlcv)

        # 상단 >= 중간 >= 하단 검증 (NaN이 아닌 값만)
        valid_idx = upper.notna() & middle.notna() & lower.notna()
        if valid_idx.any():
            assert (upper[valid_idx] >= middle[valid_idx]).all()
            assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_atr_calculation(self, sample_ohlcv):
        """ATR (Average True Range) 계산 테스트"""
        indicators = TechnicalIndicators()
        atr = indicators.calculate_atr(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv)
        # ATR은 항상 양수
        valid_atr = atr.dropna()
        if len(valid_atr) > 0:
            assert (valid_atr >= 0).all()

    def test_natr_calculation(self, sample_ohlcv):
        """NATR (Normalized Average True Range) 계산 테스트"""
        indicators = TechnicalIndicators()
        natr = indicators.calculate_natr(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(natr, pd.Series)
        assert len(natr) == len(sample_ohlcv)
        assert natr.notna().any()

    def test_trange_calculation(self, sample_ohlcv):
        """TRANGE (True Range) 계산 테스트"""
        indicators = TechnicalIndicators()
        trange = indicators.calculate_trange(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close']
        )

        assert isinstance(trange, pd.Series)
        assert len(trange) == len(sample_ohlcv)
        # True Range는 항상 양수
        valid_trange = trange.dropna()
        if len(valid_trange) > 0:
            assert (valid_trange >= 0).all()

    def test_keltner_channel_calculation(self, sample_ohlcv):
        """Keltner Channel 계산 테스트"""
        indicators = TechnicalIndicators()
        upper, middle, lower = indicators.calculate_keltner_channel(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=20, multiplier=2
        )

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_ohlcv)

        # 상단 >= 중간 >= 하단 검증
        valid_idx = upper.notna() & middle.notna() & lower.notna()
        if valid_idx.any():
            assert (upper[valid_idx] >= middle[valid_idx]).all()
            assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_donchian_channel_calculation(self, sample_ohlcv):
        """Donchian Channel 계산 테스트"""
        indicators = TechnicalIndicators()
        upper, middle, lower = indicators.calculate_donchian_channel(
            sample_ohlcv['high'], sample_ohlcv['low'], period=20
        )

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_ohlcv)

        # 상단 >= 중간 >= 하단 검증
        valid_idx = upper.notna() & middle.notna() & lower.notna()
        if valid_idx.any():
            assert (upper[valid_idx] >= middle[valid_idx]).all()
            assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_stddev_calculation(self, sample_ohlcv):
        """STDDEV (Standard Deviation) 계산 테스트"""
        indicators = TechnicalIndicators()
        stddev = indicators.calculate_stddev(sample_ohlcv['close'], period=20)

        assert isinstance(stddev, pd.Series)
        assert len(stddev) == len(sample_ohlcv)
        # 표준편차는 항상 양수
        valid_stddev = stddev.dropna()
        if len(valid_stddev) > 0:
            assert (valid_stddev >= 0).all()

    def test_var_calculation(self, sample_ohlcv):
        """VAR (Variance) 계산 테스트"""
        indicators = TechnicalIndicators()
        var = indicators.calculate_var(sample_ohlcv['close'], period=20)

        assert isinstance(var, pd.Series)
        assert len(var) == len(sample_ohlcv)
        # 분산은 항상 양수
        valid_var = var.dropna()
        if len(valid_var) > 0:
            assert (valid_var >= 0).all()

    def test_linearreg_calculation(self, sample_ohlcv):
        """LINEARREG (Linear Regression) 계산 테스트"""
        indicators = TechnicalIndicators()
        linearreg = indicators.calculate_linearreg(sample_ohlcv['close'], period=14)

        assert isinstance(linearreg, pd.Series)
        assert len(linearreg) == len(sample_ohlcv)
        assert linearreg.notna().any()

    def test_tsf_calculation(self, sample_ohlcv):
        """TSF (Time Series Forecast) 계산 테스트"""
        indicators = TechnicalIndicators()
        tsf = indicators.calculate_tsf(sample_ohlcv['close'], period=14)

        assert isinstance(tsf, pd.Series)
        assert len(tsf) == len(sample_ohlcv)
        assert tsf.notna().any()


class TestVolumeIndicators:
    """거래량 지표 테스트 (10개)"""

    def test_obv_calculation(self, sample_ohlcv):
        """OBV (On Balance Volume) 계산 테스트"""
        indicators = TechnicalIndicators()
        obv = indicators.calculate_obv(sample_ohlcv['close'], sample_ohlcv['volume'])

        assert isinstance(obv, pd.Series)
        assert len(obv) == len(sample_ohlcv)
        assert obv.notna().any()

    def test_ad_calculation(self, sample_ohlcv):
        """AD (Chaikin A/D Line) 계산 테스트"""
        indicators = TechnicalIndicators()
        ad = indicators.calculate_ad(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume']
        )

        assert isinstance(ad, pd.Series)
        assert len(ad) == len(sample_ohlcv)
        assert ad.notna().any()

    def test_adosc_calculation(self, sample_ohlcv):
        """ADOSC (Chaikin A/D Oscillator) 계산 테스트"""
        indicators = TechnicalIndicators()
        adosc = indicators.calculate_adosc(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume'], fast=3, slow=10
        )

        assert isinstance(adosc, pd.Series)
        assert len(adosc) == len(sample_ohlcv)
        assert adosc.notna().any()

    def test_cmf_calculation(self, sample_ohlcv):
        """CMF (Chaikin Money Flow) 계산 테스트"""
        indicators = TechnicalIndicators()
        cmf = indicators.calculate_cmf(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume'], period=20
        )

        assert isinstance(cmf, pd.Series)
        assert len(cmf) == len(sample_ohlcv)
        assert cmf.notna().any()

    def test_fi_calculation(self, sample_ohlcv):
        """FI (Force Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        fi = indicators.calculate_fi(sample_ohlcv['close'], sample_ohlcv['volume'], period=13)

        assert isinstance(fi, pd.Series)
        assert len(fi) == len(sample_ohlcv)
        assert fi.notna().any()

    def test_eom_calculation(self, sample_ohlcv):
        """EOM (Ease of Movement) 계산 테스트"""
        indicators = TechnicalIndicators()
        eom = indicators.calculate_eom(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['volume'], period=14
        )

        assert isinstance(eom, pd.Series)
        assert len(eom) == len(sample_ohlcv)
        assert eom.notna().any()

    def test_vpt_calculation(self, sample_ohlcv):
        """VPT (Volume Price Trend) 계산 테스트"""
        indicators = TechnicalIndicators()
        vpt = indicators.calculate_vpt(sample_ohlcv['close'], sample_ohlcv['volume'])

        assert isinstance(vpt, pd.Series)
        assert len(vpt) == len(sample_ohlcv)
        assert vpt.notna().any()

    def test_nvi_calculation(self, sample_ohlcv):
        """NVI (Negative Volume Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        nvi = indicators.calculate_nvi(sample_ohlcv['close'], sample_ohlcv['volume'])

        assert isinstance(nvi, pd.Series)
        assert len(nvi) == len(sample_ohlcv)
        assert nvi.notna().any()

    def test_pvi_calculation(self, sample_ohlcv):
        """PVI (Positive Volume Index) 계산 테스트"""
        indicators = TechnicalIndicators()
        pvi = indicators.calculate_pvi(sample_ohlcv['close'], sample_ohlcv['volume'])

        assert isinstance(pvi, pd.Series)
        assert len(pvi) == len(sample_ohlcv)
        assert pvi.notna().any()

    def test_vwap_calculation(self, sample_ohlcv):
        """VWAP (Volume Weighted Average Price) 계산 테스트"""
        indicators = TechnicalIndicators()
        vwap = indicators.calculate_vwap(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume']
        )

        assert isinstance(vwap, pd.Series)
        assert len(vwap) == len(sample_ohlcv)
        assert vwap.notna().any()


class TestIntegration:
    """통합 테스트"""

    def test_calculate_all_indicators(self, sample_ohlcv):
        """전체 지표 계산 테스트"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_all(sample_ohlcv)

        # 원본 DataFrame이 복사되어야 함
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv)

        # 원본 컬럼 존재
        for col in sample_ohlcv.columns:
            assert col in result.columns

        # 주요 지표 컬럼 존재 확인
        expected_indicators = [
            'SMA_20', 'EMA_12', 'RSI_14', 'MACD',
            'MACD_Signal', 'MACD_Hist', 'BB_Upper', 'BB_Middle', 'BB_Lower',
            'ATR_14', 'OBV'
        ]

        for indicator in expected_indicators:
            assert indicator in result.columns, f"{indicator} not found in result"

    def test_calculate_all_no_errors(self, sample_ohlcv):
        """전체 지표 계산 시 에러가 없어야 함"""
        indicators = TechnicalIndicators()

        # 에러 없이 실행되어야 함
        try:
            result = indicators.calculate_all(sample_ohlcv)
            assert result is not None
        except Exception as e:
            pytest.fail(f"calculate_all raised an exception: {e}")

    def test_invalid_period_handling(self, sample_ohlcv):
        """잘못된 파라미터 처리 테스트"""
        indicators = TechnicalIndicators()

        # period가 0 이하인 경우
        with pytest.raises((ValueError, Exception)):
            indicators.calculate_sma(sample_ohlcv['close'], period=0)

        # period가 데이터 길이보다 큰 경우 (NaN 반환)
        result = indicators.calculate_sma(sample_ohlcv['close'], period=100)
        assert result.isna().all()

    def test_empty_data_handling(self):
        """빈 데이터 처리 테스트"""
        indicators = TechnicalIndicators()
        empty_series = pd.Series([], dtype=float)

        # 빈 시리즈는 빈 결과 반환
        result = indicators.calculate_sma(empty_series, period=20)
        assert len(result) == 0

    def test_nan_data_handling(self, sample_ohlcv):
        """NaN 데이터 처리 테스트"""
        indicators = TechnicalIndicators()

        # 일부 데이터를 NaN으로 설정
        close_with_nan = sample_ohlcv['close'].copy()
        close_with_nan.iloc[10:15] = np.nan

        # NaN이 있어도 계산 가능해야 함
        result = indicators.calculate_sma(close_with_nan, period=5)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close_with_nan)


class TestEdgeCases:
    """경계 케이스 테스트"""

    def test_minimum_data_for_indicators(self):
        """최소 데이터로 지표 계산 테스트"""
        indicators = TechnicalIndicators()

        # 최소 데이터 (14일)
        dates = pd.date_range(start='2024-01-01', periods=14, freq='D')
        min_data = pd.DataFrame({
            'close': np.random.randn(14) + 70000,
            'high': np.random.randn(14) + 71000,
            'low': np.random.randn(14) + 69000,
            'volume': np.random.randint(1000000, 5000000, 14)
        }, index=dates)

        # RSI 계산 (14일 필요)
        rsi = indicators.calculate_rsi(min_data['close'], period=14)
        assert isinstance(rsi, pd.Series)

    def test_all_same_values(self):
        """모든 값이 동일한 경우 테스트"""
        indicators = TechnicalIndicators()

        # 모든 값이 동일한 시리즈
        same_values = pd.Series([70000] * 30, dtype=float)

        # SMA는 동일한 값 반환
        sma = indicators.calculate_sma(same_values, period=20)
        valid_sma = sma.dropna()
        if len(valid_sma) > 0:
            assert (valid_sma == 70000).all()

    def test_extreme_volatility(self):
        """극단적 변동성 테스트"""
        indicators = TechnicalIndicators()

        # 극단적으로 변동하는 데이터
        volatile_data = pd.Series([70000 + (-1)**i * 5000 for i in range(30)], dtype=float)

        # 계산 가능해야 함
        rsi = indicators.calculate_rsi(volatile_data, period=14)
        assert isinstance(rsi, pd.Series)
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


class TestPerformance:
    """성능 테스트"""

    def test_large_dataset_performance(self):
        """대용량 데이터 처리 성능 테스트"""
        import time

        indicators = TechnicalIndicators()

        # 1년치 데이터 (252 거래일)
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        large_data = pd.DataFrame({
            'open': np.random.randn(252) + 70000,
            'high': np.random.randn(252) + 71000,
            'low': np.random.randn(252) + 69000,
            'close': np.random.randn(252) + 70000,
            'volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)

        # 전체 지표 계산 시간 측정
        start_time = time.time()
        result = indicators.calculate_all(large_data)
        elapsed_time = time.time() - start_time

        # 1초 이내에 완료되어야 함
        assert elapsed_time < 1.0, f"Took too long: {elapsed_time:.2f}s"
        assert result is not None
        assert len(result) == len(large_data)
