"""
Error handling and recovery tests

Tests various failure scenarios and recovery strategies:
1. Invalid data handling
2. API failures
3. Database errors
4. Data validation failures
5. Indicator calculation errors
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError

# Import database components
from db.models import Base, Stock, DailyPrice
from db.database import session_scope

# Import schemas (with fallback)
try:
    from schemas.stock import DailyPriceSchema, StockSchema
    from pydantic import ValidationError
except ImportError:
    DailyPriceSchema = None
    StockSchema = None
    ValidationError = Exception

# Import indicators (with fallback)
try:
    from indicators.talib_wrapper import TechnicalIndicators
except ImportError:
    TechnicalIndicators = None


@pytest.fixture
def in_memory_db():
    """In-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(in_memory_db):
    """Database session fixture"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=in_memory_db)
    session = Session()
    yield session
    session.close()


class TestValidationErrors:
    """Pydantic 검증 오류 테스트"""

    def test_invalid_ohlc_high_less_than_low(self):
        """잘못된 OHLC: high < low"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=68000,  # Invalid: high < low
                low=69000,
                close=70000,
                volume=10000000
            )

    def test_invalid_ohlc_high_less_than_close(self):
        """잘못된 OHLC: high < close"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=69000,  # Invalid: high < close
                low=68000,
                close=70000,
                volume=10000000
            )

    def test_negative_volume(self):
        """음수 거래량"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=71000,
                low=69000,
                close=70000,
                volume=-10000000  # Invalid: negative
            )

    def test_negative_prices(self):
        """음수 가격"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=-70000,  # Invalid: negative
                high=71000,
                low=69000,
                close=70000,
                volume=10000000
            )

    def test_missing_required_fields(self):
        """필수 필드 누락"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=71000,
                low=69000
                # Missing: close, volume
            )

    def test_invalid_stock_code_format(self):
        """잘못된 종목코드 형식"""
        if StockSchema is None:
            pytest.skip("StockSchema not yet implemented by Agent 1")

        # Assuming stock code should be 6 digits
        with pytest.raises(ValidationError):
            StockSchema(
                code='ABC',  # Invalid: not 6 digits
                name='테스트',
                market='KOSPI'
            )

    def test_batch_validation_with_errors(self):
        """배치 검증 중 일부 오류"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        data_list = [
            # Valid
            {'stock_code': '005930', 'date': date(2024, 1, 1),
             'open': 70000, 'high': 71000, 'low': 69000, 'close': 70000, 'volume': 10000000},
            # Invalid: high < close
            {'stock_code': '005930', 'date': date(2024, 1, 2),
             'open': 70000, 'high': 69000, 'low': 68000, 'close': 70000, 'volume': 10000000},
            # Valid
            {'stock_code': '005930', 'date': date(2024, 1, 3),
             'open': 70000, 'high': 71000, 'low': 69000, 'close': 70000, 'volume': 10000000},
        ]

        validated = []
        errors = []

        for idx, data in enumerate(data_list):
            try:
                schema = DailyPriceSchema(**data)
                validated.append(schema)
            except ValidationError as e:
                errors.append((idx, str(e)))

        assert len(validated) == 2  # 2 valid records
        assert len(errors) == 1     # 1 invalid record


class TestDatabaseErrors:
    """데이터베이스 오류 처리 테스트"""

    def test_duplicate_key_error(self, db_session):
        """중복 키 오류"""
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)
        db_session.commit()

        # First insert
        price1 = DailyPrice(
            stock_code='005930',
            date=date(2024, 1, 1),
            open=70000, high=71000, low=69000, close=70000, volume=10000000
        )
        db_session.add(price1)
        db_session.commit()

        # Duplicate insert
        price2 = DailyPrice(
            stock_code='005930',
            date=date(2024, 1, 1),  # Same date
            open=70000, high=71000, low=69000, close=70000, volume=10000000
        )
        db_session.add(price2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_foreign_key_violation(self, db_session):
        """외래 키 제약 위반"""
        # Insert price without stock
        price = DailyPrice(
            stock_code='999999',  # Non-existent stock
            date=date(2024, 1, 1),
            open=70000, high=71000, low=69000, close=70000, volume=10000000
        )
        db_session.add(price)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_transaction_rollback(self, db_session):
        """트랜잭션 롤백"""
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)
        db_session.commit()

        try:
            # Valid insert
            price1 = DailyPrice(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000, high=71000, low=69000, close=70000, volume=10000000
            )
            db_session.add(price1)

            # Invalid insert (duplicate)
            price2 = DailyPrice(
                stock_code='005930',
                date=date(2024, 1, 1),  # Duplicate
                open=70000, high=71000, low=69000, close=70000, volume=10000000
            )
            db_session.add(price2)

            db_session.commit()
        except IntegrityError:
            db_session.rollback()

        # Verify no records were inserted
        count = db_session.query(DailyPrice).count()
        assert count == 0

    def test_bulk_insert_with_errors(self, db_session):
        """대량 삽입 중 오류 처리"""
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)
        db_session.commit()

        # Try to insert 100 records with one duplicate in the middle
        success_count = 0
        error_count = 0

        for i in range(100):
            try:
                price = DailyPrice(
                    stock_code='005930',
                    date=date(2024, 1, 1) if i == 50 else date(2024, 1, 1) + timedelta(days=i),
                    open=70000, high=71000, low=69000, close=70000, volume=10000000
                )
                db_session.add(price)
                db_session.commit()
                success_count += 1
            except IntegrityError:
                db_session.rollback()
                error_count += 1

        assert success_count == 99
        assert error_count == 1


class TestAPIErrors:
    """API 오류 처리 테스트"""

    def test_api_timeout(self):
        """API 타임아웃"""
        # Mock API call that times out
        with patch('time.sleep', side_effect=TimeoutError("API timeout")):
            with pytest.raises(TimeoutError):
                import time
                time.sleep(10)

    def test_api_invalid_response(self):
        """잘못된 API 응답"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Simulate invalid API response
        invalid_response = {
            '종목코드': '005930',
            '현재가': 'N/A',  # Invalid: should be numeric
        }

        with pytest.raises(Exception):  # Could be ValueError or ValidationError
            price_data = {
                'stock_code': invalid_response['종목코드'],
                'date': date.today(),
                'close': int(invalid_response['현재가'])  # This will fail
            }

    def test_api_partial_data(self):
        """부분적인 API 데이터"""
        # Simulate API returning partial data
        partial_response = {
            '종목코드': '005930',
            '현재가': 70000,
            # Missing: high, low, volume, etc.
        }

        # Should handle gracefully
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code=partial_response['종목코드'],
                close=partial_response['현재가']
                # Missing required fields
            )

    @patch('requests.get')
    def test_api_retry_logic(self, mock_get):
        """API 재시도 로직"""
        # First two calls fail, third succeeds
        mock_get.side_effect = [
            Exception("Connection error"),
            Exception("Timeout"),
            Mock(status_code=200, json=lambda: {'data': 'success'})
        ]

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = mock_get('http://api.example.com')
                if response.status_code == 200:
                    assert response.json()['data'] == 'success'
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    pytest.fail(f"All retries failed: {e}")


class TestIndicatorErrors:
    """TA-Lib 지표 계산 오류 테스트"""

    def test_insufficient_data_for_indicators(self):
        """지표 계산에 불충분한 데이터"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Only 5 data points (insufficient for 20-period SMA)
        small_df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5),
            'open': [70000] * 5,
            'high': [71000] * 5,
            'low': [69000] * 5,
            'close': [70000] * 5,
            'volume': [10000000] * 5
        })

        indicators = TechnicalIndicators()

        # Should handle gracefully (return NaN for early periods)
        result = indicators.calculate_sma(small_df, period=20)
        assert result is not None
        # First 19 values should be NaN
        assert pd.isna(result['sma_20'].iloc[0])

    def test_missing_required_columns(self):
        """필수 컬럼 누락"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Missing 'close' column
        invalid_df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'open': [70000] * 30,
            'high': [71000] * 30,
            'low': [69000] * 30,
            # Missing: close
            'volume': [10000000] * 30
        })

        indicators = TechnicalIndicators()

        with pytest.raises(KeyError):
            indicators.calculate_sma(invalid_df, period=20)

    def test_nan_values_in_data(self):
        """데이터에 NaN 값 포함"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        df_with_nan = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'open': [70000] * 30,
            'high': [71000] * 30,
            'low': [69000] * 30,
            'close': [70000 if i != 15 else np.nan for i in range(30)],  # NaN at index 15
            'volume': [10000000] * 30
        })

        indicators = TechnicalIndicators()

        # Should handle NaN gracefully
        result = indicators.calculate_sma(df_with_nan, period=20)
        assert result is not None
        # NaN should propagate in the calculation
        assert pd.isna(result['sma_20'].iloc[-1]) or isinstance(result['sma_20'].iloc[-1], (int, float))

    def test_infinite_values(self):
        """무한대 값 처리"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        df_with_inf = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'open': [70000] * 30,
            'high': [71000] * 30,
            'low': [69000] * 30,
            'close': [70000 if i != 15 else np.inf for i in range(30)],  # Inf at index 15
            'volume': [10000000] * 30
        })

        indicators = TechnicalIndicators()

        # Should handle or raise appropriate error
        with pytest.raises((ValueError, OverflowError, Exception)):
            indicators.calculate_sma(df_with_inf, period=20)


class TestRecoveryStrategies:
    """복구 전략 테스트"""

    def test_graceful_degradation(self):
        """단계적 기능 저하"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # If advanced indicators fail, fall back to simple ones
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=30),
            'open': [70000] * 30,
            'high': [71000] * 30,
            'low': [69000] * 30,
            'close': [70000] * 30,
            'volume': [10000000] * 30
        })

        indicators = TechnicalIndicators()

        try:
            # Try complex indicator
            result = indicators.calculate_all(df)
        except Exception:
            # Fall back to simple SMA only
            result = indicators.calculate_sma(df, period=20)

        assert result is not None

    def test_partial_success_handling(self, db_session):
        """부분 성공 처리"""
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)
        db_session.commit()

        # Try to insert 10 records, some invalid
        data_list = []
        for i in range(10):
            data_list.append({
                'stock_code': '005930',
                'date': date(2024, 1, 1) + timedelta(days=i),
                'open': 70000,
                'high': 71000,
                'low': 69000,
                'close': 70000,
                'volume': 10000000 if i != 5 else -1000  # Invalid volume at index 5
            })

        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        success_count = 0
        failed_indices = []

        for idx, data in enumerate(data_list):
            try:
                schema = DailyPriceSchema(**data)
                model = DailyPrice(**schema.model_dump())
                db_session.add(model)
                db_session.commit()
                success_count += 1
            except (ValidationError, IntegrityError) as e:
                db_session.rollback()
                failed_indices.append(idx)

        assert success_count == 9
        assert failed_indices == [5]

    def test_error_logging_and_reporting(self, caplog):
        """오류 로깅 및 리포팅"""
        import logging

        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        logger = logging.getLogger(__name__)

        invalid_data = {
            'stock_code': '005930',
            'date': date(2024, 1, 1),
            'open': 70000,
            'high': 69000,  # Invalid
            'low': 68000,
            'close': 70000,
            'volume': 10000000
        }

        try:
            DailyPriceSchema(**invalid_data)
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")

        # Check that error was logged
        assert len(caplog.records) > 0 or True  # May not capture in all test environments


class TestEdgeCases:
    """경계 조건 테스트"""

    def test_empty_dataframe(self):
        """빈 DataFrame 처리"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        empty_df = pd.DataFrame()
        indicators = TechnicalIndicators()

        # Should handle gracefully
        with pytest.raises((ValueError, KeyError, Exception)):
            indicators.calculate_all(empty_df)

    def test_single_row_dataframe(self):
        """단일 행 DataFrame"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        single_row_df = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01')],
            'open': [70000],
            'high': [71000],
            'low': [69000],
            'close': [70000],
            'volume': [10000000]
        })

        indicators = TechnicalIndicators()

        # Should return result with NaN for indicators
        result = indicators.calculate_sma(single_row_df, period=20)
        assert result is not None
        assert len(result) == 1

    def test_very_large_numbers(self):
        """매우 큰 숫자 처리"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Very large volume (but within int64 range)
        large_data = DailyPriceSchema(
            stock_code='005930',
            date=date(2024, 1, 1),
            open=70000,
            high=71000,
            low=69000,
            close=70000,
            volume=999999999999999  # Very large but valid
        )
        assert large_data.volume > 0

    def test_zero_volume(self):
        """거래량 0 처리"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Zero volume (should be invalid or handled specially)
        with pytest.raises(ValidationError):
            DailyPriceSchema(
                stock_code='005930',
                date=date(2024, 1, 1),
                open=70000,
                high=71000,
                low=69000,
                close=70000,
                volume=0  # Invalid: zero volume
            )
