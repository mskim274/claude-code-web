"""
Unit tests for TechnicalFeatureEngine

TDD Phase: Red - Write tests first
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestTechnicalFeatureEngine:
    """TechnicalFeatureEngine 테스트"""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """테스트용 OHLCV 데이터 생성"""
        np.random.seed(42)
        n_days = 200  # 충분한 데이터 (지표 계산을 위해)

        dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')

        # 현실적인 주가 데이터 생성
        base_price = 50000
        price_changes = np.random.randn(n_days) * 1000

        close = base_price + np.cumsum(price_changes)
        close = np.maximum(close, 1000)  # 최소 1000원

        df = pd.DataFrame({
            'date': dates,
            'open': close * (1 + np.random.randn(n_days) * 0.01),
            'high': close * (1 + np.abs(np.random.randn(n_days)) * 0.02),
            'low': close * (1 - np.abs(np.random.randn(n_days)) * 0.02),
            'close': close,
            'volume': np.random.randint(100000, 1000000, n_days)
        })

        # high >= close >= low 보장
        df['high'] = df[['high', 'close', 'open']].max(axis=1)
        df['low'] = df[['low', 'close', 'open']].min(axis=1)

        return df

    def test_create_features_returns_dataframe(self, sample_ohlcv_data):
        """create_features가 DataFrame을 반환하는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_all_50_indicators_calculated(self, sample_ohlcv_data):
        """50개 이상의 지표가 계산되는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # 원본 컬럼 + 50+ 지표
        original_columns = sample_ohlcv_data.columns
        new_columns = set(result.columns) - set(original_columns)

        # 최소 50개 이상의 새로운 컬럼
        assert len(new_columns) >= 50, f"Expected at least 50 features, got {len(new_columns)}"

    def test_no_nan_after_dropna(self, sample_ohlcv_data):
        """dropna 후 NaN이 없는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # NaN이 없어야 함
        assert not result.isnull().any().any(), "Features contain NaN values"

    def test_label_generation_correct(self, sample_ohlcv_data):
        """레이블 생성이 올바른지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        labels = engine.create_labels(sample_ohlcv_data, forward_days=1, threshold=0.01)

        assert isinstance(labels, pd.Series)
        # 레이블은 0, 1, 2 중 하나
        assert set(labels.dropna().unique()).issubset({0, 1, 2})

    def test_label_generation_threshold(self, sample_ohlcv_data):
        """threshold에 따른 레이블 생성 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()

        # 임계값 1%
        labels_1pct = engine.create_labels(sample_ohlcv_data, forward_days=1, threshold=0.01)

        # 임계값 5%
        labels_5pct = engine.create_labels(sample_ohlcv_data, forward_days=1, threshold=0.05)

        # 5% 임계값은 더 많은 보합(1) 레이블을 가져야 함
        count_1pct_neutral = (labels_1pct == 1).sum()
        count_5pct_neutral = (labels_5pct == 1).sum()

        assert count_5pct_neutral >= count_1pct_neutral

    def test_create_features_preserves_index(self, sample_ohlcv_data):
        """인덱스가 유지되는지 확인 (dropna 후에도)"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # 인덱스가 단조증가해야 함
        assert result.index.is_monotonic_increasing

    def test_price_features_added(self, sample_ohlcv_data):
        """가격 관련 파생 피처가 추가되는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # 가격 파생 피처
        expected_price_features = [
            'price_range', 'body_size', 'upper_shadow', 'lower_shadow'
        ]

        for feature in expected_price_features:
            assert feature in result.columns, f"Missing price feature: {feature}"

    def test_volume_features_added(self, sample_ohlcv_data):
        """거래량 관련 파생 피처가 추가되는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # 거래량 파생 피처
        expected_volume_features = [
            'volume_ma5', 'volume_ma20', 'volume_ratio'
        ]

        for feature in expected_volume_features:
            assert feature in result.columns, f"Missing volume feature: {feature}"

    def test_trend_features_added(self, sample_ohlcv_data):
        """추세 관련 파생 피처가 추가되는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # 추세 파생 피처
        expected_trend_features = [
            'return_5d', 'return_10d', 'return_20d', 'return_60d'
        ]

        for feature in expected_trend_features:
            assert feature in result.columns, f"Missing trend feature: {feature}"

    def test_talib_indicators_integrated(self, sample_ohlcv_data):
        """TA-Lib 지표가 통합되는지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # 주요 TA-Lib 지표 확인
        expected_talib_features = [
            'SMA_20', 'EMA_12', 'RSI_14', 'MACD',
            'BB_Upper', 'BB_Lower', 'ATR_14'
        ]

        for feature in expected_talib_features:
            assert feature in result.columns, f"Missing TA-Lib feature: {feature}"

    def test_forward_days_parameter(self, sample_ohlcv_data):
        """forward_days 파라미터 테스트"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()

        labels_1d = engine.create_labels(sample_ohlcv_data, forward_days=1)
        labels_5d = engine.create_labels(sample_ohlcv_data, forward_days=5)

        # 레이블은 다를 수 있음 (미래 시점이 다르므로)
        assert len(labels_1d) == len(labels_5d)

    def test_create_features_with_custom_indicators(self, sample_ohlcv_data):
        """커스텀 TechnicalIndicators로 초기화"""
        from ml.features.technical_features import TechnicalFeatureEngine
        from backtest.indicators import TechnicalIndicators

        custom_indicators = TechnicalIndicators()
        engine = TechnicalFeatureEngine(indicators=custom_indicators)

        result = engine.create_features(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_features_are_numeric(self, sample_ohlcv_data):
        """모든 피처가 숫자형인지 확인"""
        from ml.features.technical_features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        result = engine.create_features(sample_ohlcv_data)

        # date 제외하고 모두 숫자형
        numeric_columns = result.select_dtypes(include=[np.number]).columns
        non_date_columns = [col for col in result.columns if col != 'date']

        assert len(numeric_columns) >= len(non_date_columns) - 1
