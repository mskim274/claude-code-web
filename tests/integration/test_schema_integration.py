"""
Integration tests for Pydantic schemas with SQLAlchemy models and TA-Lib indicators

Tests the integration between:
1. SQLAlchemy models (db.models)
2. Pydantic schemas (to be created by Agent 1)
3. TA-Lib indicators (to be created by Agent 2)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import List, Dict
from unittest.mock import Mock, patch, MagicMock

# SQLAlchemy models
from db.models import Stock, DailyPrice, MinutePrice, StockInfo

# These will be available after Agent 1 completes
try:
    from schemas.stock import StockSchema, DailyPriceSchema, MinutePriceSchema, StockInfoSchema
except ImportError:
    # Mock schemas for Phase 1
    StockSchema = Mock
    DailyPriceSchema = Mock
    MinutePriceSchema = Mock
    StockInfoSchema = Mock

# These will be available after Agent 2 completes
try:
    from indicators.talib_wrapper import TechnicalIndicators
except ImportError:
    # Mock TechnicalIndicators for Phase 1
    TechnicalIndicators = Mock


class TestSQLAlchemyToPydantic:
    """SQLAlchemy 모델 → Pydantic 스키마 변환 테스트"""

    def test_stock_model_to_schema(self, sample_stock_data):
        """Stock 모델을 Pydantic 스키마로 변환"""
        # Create SQLAlchemy model instance
        stock = Stock(
            code=sample_stock_data['code'],
            name=sample_stock_data['name'],
            market=sample_stock_data['market'],
            sector=sample_stock_data['sector'],
            listing_date=sample_stock_data['listing_date']
        )

        # Convert to Pydantic schema (will work after Agent 1)
        if hasattr(StockSchema, 'model_validate'):
            schema = StockSchema.model_validate(stock, from_attributes=True)
            assert schema.code == sample_stock_data['code']
            assert schema.name == sample_stock_data['name']
            assert schema.market == sample_stock_data['market']
        else:
            pytest.skip("StockSchema not yet implemented by Agent 1")

    def test_daily_price_model_to_schema(self, sample_daily_prices):
        """DailyPrice 모델을 Pydantic 스키마로 변환"""
        price_data = sample_daily_prices[0]

        daily_price = DailyPrice(
            stock_code=price_data['stock_code'],
            date=price_data['date'],
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            volume=price_data['volume']
        )

        if hasattr(DailyPriceSchema, 'model_validate'):
            schema = DailyPriceSchema.model_validate(daily_price, from_attributes=True)
            assert schema.stock_code == price_data['stock_code']
            assert schema.close == price_data['close']
            assert schema.high >= schema.close
            assert schema.high >= schema.low
        else:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

    def test_minute_price_model_to_schema(self, sample_minute_prices):
        """MinutePrice 모델을 Pydantic 스키마로 변환"""
        price_data = sample_minute_prices[0]

        minute_price = MinutePrice(
            stock_code=price_data['stock_code'],
            datetime=price_data['datetime'],
            interval=price_data['interval'],
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            volume=price_data['volume']
        )

        if hasattr(MinutePriceSchema, 'model_validate'):
            schema = MinutePriceSchema.model_validate(minute_price, from_attributes=True)
            assert schema.stock_code == price_data['stock_code']
            assert schema.interval == price_data['interval']
            assert schema.high >= schema.close
        else:
            pytest.skip("MinutePriceSchema not yet implemented by Agent 1")

    def test_batch_conversion(self, sample_daily_prices):
        """대량 데이터 일괄 변환 테스트"""
        models = [
            DailyPrice(**price_data)
            for price_data in sample_daily_prices
        ]

        if hasattr(DailyPriceSchema, 'model_validate'):
            schemas = [
                DailyPriceSchema.model_validate(model, from_attributes=True)
                for model in models
            ]
            assert len(schemas) == len(sample_daily_prices)

            # Verify all conversions maintain data integrity
            for schema, original in zip(schemas, sample_daily_prices):
                assert schema.stock_code == original['stock_code']
                assert schema.close == original['close']
        else:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")


class TestPydanticToDataFrame:
    """Pydantic 스키마 → DataFrame 변환 테스트"""

    def test_daily_price_schema_to_dataframe(self, sample_daily_prices):
        """DailyPrice 스키마를 DataFrame으로 변환"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Create schemas
        schemas = [DailyPriceSchema(**price_data) for price_data in sample_daily_prices]

        # Convert to DataFrame
        df = pd.DataFrame([schema.model_dump() for schema in schemas])

        assert len(df) == len(sample_daily_prices)
        assert 'date' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns

        # Verify OHLC integrity
        assert (df['high'] >= df['close']).all()
        assert (df['high'] >= df['low']).all()
        assert (df['close'] >= df['low']).all()

    def test_dataframe_preserves_types(self, sample_daily_prices):
        """DataFrame 변환 시 타입 보존 확인"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        schemas = [DailyPriceSchema(**price_data) for price_data in sample_daily_prices]
        df = pd.DataFrame([schema.model_dump() for schema in schemas])

        # Check data types
        assert df['open'].dtype in [np.int64, np.int32]
        assert df['high'].dtype in [np.int64, np.int32]
        assert df['low'].dtype in [np.int64, np.int32]
        assert df['close'].dtype in [np.int64, np.int32]
        assert df['volume'].dtype in [np.int64, np.int32]


class TestPydanticWithTALib:
    """Pydantic 스키마 + TA-Lib 통합 테스트"""

    def test_pydantic_to_talib_pipeline(self, sample_ohlcv):
        """Pydantic → DataFrame → TA-Lib 전체 파이프라인"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")
        if not hasattr(TechnicalIndicators, 'calculate_sma'):
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Simulate: Pydantic schemas
        schemas = []
        for idx, row in sample_ohlcv.iterrows():
            schema = DailyPriceSchema(
                stock_code='005930',
                date=row['date'].date() if isinstance(row['date'], pd.Timestamp) else row['date'],
                open=int(row['open']),
                high=int(row['high']),
                low=int(row['low']),
                close=int(row['close']),
                volume=int(row['volume'])
            )
            schemas.append(schema)

        # Convert to DataFrame
        df = pd.DataFrame([s.model_dump() for s in schemas])

        # Calculate indicators with TA-Lib
        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        # Verify indicators are added
        assert 'sma_20' in df_with_indicators.columns
        assert 'rsi_14' in df_with_indicators.columns
        assert len(df_with_indicators) == len(df)

    def test_indicators_validation_with_pydantic(self, sample_ohlcv):
        """TA-Lib 지표 계산 후 Pydantic으로 재검증"""
        if not hasattr(TechnicalIndicators, 'calculate_sma'):
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(sample_ohlcv)

        # Validate each row with Pydantic
        if hasattr(DailyPriceSchema, 'model_validate'):
            for idx, row in df_with_indicators.iterrows():
                # Should still pass OHLCV validation
                assert row['high'] >= row['close']
                assert row['high'] >= row['low']
                assert row['close'] >= row['low']

                # Indicators should be valid numbers or NaN
                if not pd.isna(row.get('rsi_14')):
                    assert 0 <= row['rsi_14'] <= 100
                if not pd.isna(row.get('macd')):
                    assert isinstance(row['macd'], (int, float))

    def test_invalid_data_handling(self):
        """잘못된 데이터 처리 테스트"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Invalid: high < close
        with pytest.raises(Exception):  # Should raise ValidationError
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=69000,  # Invalid: high < close
                low=68000,
                close=70000,
                volume=1000000
            )

        # Invalid: negative volume
        with pytest.raises(Exception):  # Should raise ValidationError
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=71000,
                low=69000,
                close=70000,
                volume=-1000000  # Invalid: negative
            )


class TestFullPipeline:
    """전체 파이프라인 통합 테스트: DB → 스키마 → 지표 → 백테스팅"""

    def test_db_to_backtest_pipeline(self, sample_daily_prices):
        """DB 조회 → Pydantic → DataFrame → TA-Lib → 백테스팅"""
        # Phase 1: Mock the entire pipeline
        # This will be fully implemented after Agent 1 and 2 complete

        # 1. Simulate DB query
        db_results = [DailyPrice(**price_data) for price_data in sample_daily_prices]

        # 2. Convert to Pydantic schemas
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("Waiting for Agent 1 to implement schemas")

        schemas = [
            DailyPriceSchema.model_validate(model, from_attributes=True)
            for model in db_results
        ]

        # 3. Convert to DataFrame
        df = pd.DataFrame([s.model_dump() for s in schemas])

        # 4. Add TA-Lib indicators
        if not hasattr(TechnicalIndicators, 'calculate_all'):
            pytest.skip("Waiting for Agent 2 to implement indicators")

        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        # 5. Verify pipeline integrity
        assert len(df_with_indicators) == len(sample_daily_prices)
        assert 'close' in df_with_indicators.columns
        assert 'sma_20' in df_with_indicators.columns

        # 6. Ready for backtesting
        assert df_with_indicators['close'].notna().all()

    @pytest.mark.slow
    def test_large_dataset_pipeline(self):
        """대량 데이터 파이프라인 테스트 (1000일치)"""
        # Generate 1000 days of data
        large_data = []
        base_date = date(2020, 1, 1)

        for i in range(1000):
            large_data.append({
                'stock_code': '005930',
                'date': base_date + timedelta(days=i),
                'open': 70000 + i * 10,
                'high': 71000 + i * 10,
                'low': 69000 + i * 10,
                'close': 70500 + i * 10,
                'volume': 10000000 + i * 1000
            })

        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("Waiting for Agent 1")
        if not hasattr(TechnicalIndicators, 'calculate_all'):
            pytest.skip("Waiting for Agent 2")

        # Full pipeline
        schemas = [DailyPriceSchema(**data) for data in large_data]
        df = pd.DataFrame([s.model_dump() for s in schemas])

        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        assert len(df_with_indicators) == 1000
        assert df_with_indicators['close'].notna().all()


class TestSchemaValidation:
    """스키마 검증 규칙 테스트"""

    def test_ohlc_validation_rules(self):
        """OHLC 검증 규칙 테스트"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Valid OHLC
        valid_data = DailyPriceSchema(
            stock_code='005930',
            date=date(2024, 1, 1),
            open=70000,
            high=71000,
            low=69000,
            close=70500,
            volume=10000000
        )
        assert valid_data.high >= valid_data.close
        assert valid_data.high >= valid_data.low

    def test_date_range_validation(self):
        """날짜 범위 검증 테스트"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Future date should be allowed (for testing)
        future_data = DailyPriceSchema(
            stock_code='005930',
            date=date(2030, 1, 1),
            open=70000,
            high=71000,
            low=69000,
            close=70500,
            volume=10000000
        )
        assert future_data.date.year == 2030

    def test_stock_code_format(self):
        """종목코드 형식 검증"""
        if not hasattr(StockSchema, 'model_validate'):
            pytest.skip("StockSchema not yet implemented by Agent 1")

        # Valid 6-digit stock code
        stock = StockSchema(
            code='005930',
            name='삼성전자',
            market='KOSPI'
        )
        assert len(stock.code) == 6
        assert stock.code.isdigit()


class TestErrorRecovery:
    """에러 복구 및 처리 테스트"""

    def test_missing_data_handling(self):
        """누락된 데이터 처리"""
        incomplete_data = {
            'stock_code': '005930',
            'date': date(2024, 1, 1),
            'open': 70000,
            'high': 71000,
            'low': 69000,
            'close': 70500,
            # volume is missing
        }

        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(Exception):  # Should raise ValidationError
            DailyPriceSchema(**incomplete_data)

    def test_type_coercion(self):
        """타입 강제 변환 테스트"""
        if not hasattr(DailyPriceSchema, 'model_validate'):
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # String numbers should be coerced to int
        data_with_strings = {
            'stock_code': '005930',
            'date': date(2024, 1, 1),
            'open': '70000',  # String
            'high': '71000',  # String
            'low': '69000',   # String
            'close': '70500', # String
            'volume': '10000000'  # String
        }

        schema = DailyPriceSchema(**data_with_strings)
        assert isinstance(schema.open, int)
        assert isinstance(schema.close, int)


# Additional helper functions for testing

def generate_random_ohlcv(days: int, base_price: int = 70000) -> pd.DataFrame:
    """Generate random OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')

    np.random.seed(42)

    data = {
        'date': dates,
        'open': base_price + np.random.randint(-1000, 1000, days),
        'high': base_price + np.random.randint(500, 2000, days),
        'low': base_price + np.random.randint(-2000, -500, days),
        'close': base_price + np.random.randint(-1000, 1000, days),
        'volume': np.random.randint(1000000, 5000000, days)
    }

    df = pd.DataFrame(data)

    # Ensure OHLC integrity
    df['high'] = df[['open', 'high', 'close']].max(axis=1) + 100
    df['low'] = df[['open', 'low', 'close']].min(axis=1) - 100

    return df


@pytest.fixture
def large_ohlcv():
    """Fixture for large OHLCV dataset (1000 days)"""
    return generate_random_ohlcv(days=1000)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    return session
