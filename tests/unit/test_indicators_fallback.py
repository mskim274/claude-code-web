"""
기술적 지표 테스트 (Fallback 구현)

TA-Lib 없이도 실행 가능한 fallback 구현 테스트
"""
import pytest
import pandas as pd
import numpy as np

from backtest.indicators.talib_wrapper import TechnicalIndicators


class TestTrendIndicatorsFallback:
    """추세 지표 Fallback 테스트"""

    def test_sma_calculation(self, sample_ohlcv):
        """SMA 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        sma = indicators.calculate_sma(sample_ohlcv['close'], period=20)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_ohlcv)
        assert sma.iloc[:19].isna().all()
        assert sma.iloc[19:].notna().any()

    def test_ema_calculation(self, sample_ohlcv):
        """EMA 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        ema = indicators.calculate_ema(sample_ohlcv['close'], period=12)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_ohlcv)
        assert ema.notna().any()

    def test_wma_calculation(self, sample_ohlcv):
        """WMA 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        wma = indicators.calculate_wma(sample_ohlcv['close'], period=20)

        assert isinstance(wma, pd.Series)
        assert len(wma) == len(sample_ohlcv)
        assert wma.notna().any()


class TestMomentumIndicatorsFallback:
    """모멘텀 지표 Fallback 테스트"""

    def test_rsi_calculation(self, sample_ohlcv):
        """RSI 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        rsi = indicators.calculate_rsi(sample_ohlcv['close'], period=14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_ohlcv)
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all()
            assert (valid_rsi <= 100).all()

    def test_macd_calculation(self, sample_ohlcv):
        """MACD 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        macd, signal, hist = indicators.calculate_macd(sample_ohlcv['close'])

        assert isinstance(macd, pd.Series)
        assert isinstance(signal, pd.Series)
        assert isinstance(hist, pd.Series)
        assert len(macd) == len(sample_ohlcv)

    def test_stochastic_calculation(self, sample_ohlcv):
        """Stochastic 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        slowk, slowd = indicators.calculate_stochastic(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close']
        )

        assert isinstance(slowk, pd.Series)
        assert isinstance(slowd, pd.Series)
        assert len(slowk) == len(sample_ohlcv)


class TestVolatilityIndicatorsFallback:
    """변동성 지표 Fallback 테스트"""

    def test_bollinger_bands_calculation(self, sample_ohlcv):
        """볼린저 밴드 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        upper, middle, lower = indicators.calculate_bollinger_bands(
            sample_ohlcv['close'], period=20, std=2
        )

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_ohlcv)

        valid_idx = upper.notna() & middle.notna() & lower.notna()
        if valid_idx.any():
            assert (upper[valid_idx] >= middle[valid_idx]).all()
            assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_atr_calculation(self, sample_ohlcv):
        """ATR 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        atr = indicators.calculate_atr(
            sample_ohlcv['high'], sample_ohlcv['low'], sample_ohlcv['close'], period=14
        )

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_ohlcv)
        valid_atr = atr.dropna()
        if len(valid_atr) > 0:
            assert (valid_atr >= 0).all()


class TestVolumeIndicatorsFallback:
    """거래량 지표 Fallback 테스트"""

    def test_obv_calculation(self, sample_ohlcv):
        """OBV 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        obv = indicators.calculate_obv(sample_ohlcv['close'], sample_ohlcv['volume'])

        assert isinstance(obv, pd.Series)
        assert len(obv) == len(sample_ohlcv)
        assert obv.notna().any()

    def test_ad_calculation(self, sample_ohlcv):
        """AD 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        ad = indicators.calculate_ad(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume']
        )

        assert isinstance(ad, pd.Series)
        assert len(ad) == len(sample_ohlcv)
        assert ad.notna().any()

    def test_cmf_calculation(self, sample_ohlcv):
        """CMF 계산 테스트 (Fallback)"""
        indicators = TechnicalIndicators()
        cmf = indicators.calculate_cmf(
            sample_ohlcv['high'], sample_ohlcv['low'],
            sample_ohlcv['close'], sample_ohlcv['volume'], period=20
        )

        assert isinstance(cmf, pd.Series)
        assert len(cmf) == len(sample_ohlcv)
        assert cmf.notna().any()


class TestIntegrationFallback:
    """통합 테스트 (Fallback)"""

    def test_calculate_all_indicators(self, sample_ohlcv):
        """전체 지표 계산 테스트"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_all(sample_ohlcv)

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

        try:
            result = indicators.calculate_all(sample_ohlcv)
            assert result is not None
            assert len(result.columns) > len(sample_ohlcv.columns)
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

        result = indicators.calculate_sma(empty_series, period=20)
        assert len(result) == 0

    def test_nan_data_handling(self, sample_ohlcv):
        """NaN 데이터 처리 테스트"""
        indicators = TechnicalIndicators()

        close_with_nan = sample_ohlcv['close'].copy()
        close_with_nan.iloc[10:15] = np.nan

        result = indicators.calculate_sma(close_with_nan, period=5)
        assert isinstance(result, pd.Series)
        assert len(result) == len(close_with_nan)

    def test_get_indicator_list(self):
        """지표 목록 조회 테스트"""
        indicators = TechnicalIndicators()
        indicator_list = indicators.get_indicator_list()

        assert 'trend' in indicator_list
        assert 'momentum' in indicator_list
        assert 'volatility' in indicator_list
        assert 'volume' in indicator_list

        # 각 카테고리에 지표가 있는지 확인
        assert len(indicator_list['trend']) >= 10
        assert len(indicator_list['momentum']) >= 20
        assert len(indicator_list['volatility']) >= 10
        assert len(indicator_list['volume']) >= 10

    def test_get_indicator_count(self):
        """지표 개수 조회 테스트"""
        indicators = TechnicalIndicators()
        count = indicators.get_indicator_count()

        # 최소 50개 이상의 지표
        assert count >= 50

    def test_repr(self):
        """문자열 표현 테스트"""
        indicators = TechnicalIndicators()
        repr_str = repr(indicators)

        assert 'TechnicalIndicators' in repr_str
        assert 'total_indicators' in repr_str


class TestEdgeCasesFallback:
    """경계 케이스 테스트 (Fallback)"""

    def test_minimum_data_for_indicators(self):
        """최소 데이터로 지표 계산 테스트"""
        indicators = TechnicalIndicators()

        dates = pd.date_range(start='2024-01-01', periods=14, freq='D')
        min_data = pd.DataFrame({
            'close': np.random.randn(14) + 70000,
            'high': np.random.randn(14) + 71000,
            'low': np.random.randn(14) + 69000,
            'volume': np.random.randint(1000000, 5000000, 14)
        }, index=dates)

        rsi = indicators.calculate_rsi(min_data['close'], period=14)
        assert isinstance(rsi, pd.Series)

    def test_all_same_values(self):
        """모든 값이 동일한 경우 테스트"""
        indicators = TechnicalIndicators()

        same_values = pd.Series([70000] * 30, dtype=float)

        sma = indicators.calculate_sma(same_values, period=20)
        valid_sma = sma.dropna()
        if len(valid_sma) > 0:
            assert (valid_sma == 70000).all()

    def test_extreme_volatility(self):
        """극단적 변동성 테스트"""
        indicators = TechnicalIndicators()

        volatile_data = pd.Series([70000 + (-1)**i * 5000 for i in range(30)], dtype=float)

        rsi = indicators.calculate_rsi(volatile_data, period=14)
        assert isinstance(rsi, pd.Series)
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


class TestPerformanceFallback:
    """성능 테스트 (Fallback)"""

    def test_large_dataset_performance(self):
        """대용량 데이터 처리 성능 테스트"""
        import time

        indicators = TechnicalIndicators()

        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        large_data = pd.DataFrame({
            'open': np.random.randn(252) + 70000,
            'high': np.random.randn(252) + 71000,
            'low': np.random.randn(252) + 69000,
            'close': np.random.randn(252) + 70000,
            'volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)

        start_time = time.time()
        result = indicators.calculate_all(large_data)
        elapsed_time = time.time() - start_time

        # 2초 이내에 완료되어야 함 (fallback이 더 느림)
        assert elapsed_time < 2.0, f"Took too long: {elapsed_time:.2f}s"
        assert result is not None
        assert len(result) == len(large_data)

    def test_multiple_indicator_calculations(self, sample_ohlcv):
        """여러 지표 순차 계산 테스트"""
        indicators = TechnicalIndicators()

        # 여러 지표를 순차적으로 계산
        sma_20 = indicators.calculate_sma(sample_ohlcv['close'], period=20)
        ema_12 = indicators.calculate_ema(sample_ohlcv['close'], period=12)
        rsi_14 = indicators.calculate_rsi(sample_ohlcv['close'], period=14)
        macd, signal, hist = indicators.calculate_macd(sample_ohlcv['close'])

        # 모두 계산되어야 함
        assert sma_20 is not None
        assert ema_12 is not None
        assert rsi_14 is not None
        assert macd is not None
        assert signal is not None
        assert hist is not None


class TestDataFrameOperations:
    """DataFrame 연산 테스트"""

    def test_missing_volume_column(self, sample_ohlcv):
        """volume 컬럼이 없는 경우 테스트"""
        indicators = TechnicalIndicators()

        # volume 컬럼 제거
        ohlc_data = sample_ohlcv[['open', 'high', 'low', 'close']].copy()

        # 에러 없이 실행되어야 함
        result = indicators.calculate_all(ohlc_data)
        assert result is not None

        # volume 관련 지표는 계산되지 않거나 0으로 채워짐
        assert 'volume' in result.columns  # 더미 데이터로 생성됨

    def test_missing_open_column(self, sample_ohlcv):
        """open 컬럼이 없는 경우 테스트"""
        indicators = TechnicalIndicators()

        # open 컬럼 제거
        hlcv_data = sample_ohlcv[['high', 'low', 'close', 'volume']].copy()

        # 에러 없이 실행되어야 함
        result = indicators.calculate_all(hlcv_data)
        assert result is not None

        # BOP는 계산되지 않음
        assert 'BOP' not in result.columns or result['BOP'].isna().all()

    def test_column_preservation(self, sample_ohlcv):
        """원본 컬럼 보존 테스트"""
        indicators = TechnicalIndicators()

        original_columns = list(sample_ohlcv.columns)
        result = indicators.calculate_all(sample_ohlcv)

        # 원본 컬럼이 모두 존재해야 함
        for col in original_columns:
            assert col in result.columns

        # 원본 데이터는 변경되지 않아야 함
        for col in original_columns:
            if col != 'date':  # date는 인덱스일 수 있음
                pd.testing.assert_series_equal(
                    sample_ohlcv[col].reset_index(drop=True),
                    result[col].reset_index(drop=True),
                    check_names=False
                )
