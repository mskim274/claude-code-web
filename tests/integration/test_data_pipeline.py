"""
Data pipeline integration tests

Tests the complete data flow:
1. API → Pydantic Schema
2. Pydantic Schema → SQLAlchemy Model
3. SQLAlchemy Model → Database
4. Database → Pydantic Schema
5. Pydantic Schema → DataFrame
6. DataFrame → TA-Lib Indicators
7. Indicators → Backtesting Engine
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Import database components
from db.models import Base, Stock, DailyPrice, MinutePrice, StockInfo
from db.database import session_scope

# Import schemas (with fallback)
try:
    from schemas.stock import StockSchema, DailyPriceSchema, MinutePriceSchema, StockInfoSchema
except ImportError:
    StockSchema = None
    DailyPriceSchema = None
    MinutePriceSchema = None
    StockInfoSchema = None

# Import indicators (with fallback)
try:
    from indicators.talib_wrapper import TechnicalIndicators
except ImportError:
    TechnicalIndicators = None

# Import backtest engine
from backtest.engine import BacktestEngine
from backtest.strategy import MovingAverageCrossStrategy


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


class TestAPIToPydantic:
    """API 응답 → Pydantic 스키마 변환 테스트"""

    def test_kiwoom_api_response_to_daily_price_schema(self, mock_kiwoom_response):
        """키움 API 응답을 DailyPrice 스키마로 변환"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Simulate API response transformation
        api_data = {
            'stock_code': mock_kiwoom_response['종목코드'],
            'date': date.today(),
            'open': abs(int(mock_kiwoom_response['시가'])),
            'high': abs(int(mock_kiwoom_response['고가'])),
            'low': abs(int(mock_kiwoom_response['저가'])),
            'close': abs(int(mock_kiwoom_response['현재가'])),
            'volume': int(mock_kiwoom_response['거래량'])
        }

        schema = DailyPriceSchema(**api_data)
        assert schema.stock_code == '005930'
        assert schema.close > 0

    def test_batch_api_response_conversion(self):
        """대량 API 응답 일괄 변환"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Simulate 100 API responses
        api_responses = []
        for i in range(100):
            api_responses.append({
                'stock_code': '005930',
                'date': date(2024, 1, 1) + timedelta(days=i),
                'open': 70000 + i * 10,
                'high': 71000 + i * 10,
                'low': 69000 + i * 10,
                'close': 70500 + i * 10,
                'volume': 10000000 + i * 1000
            })

        schemas = [DailyPriceSchema(**resp) for resp in api_responses]
        assert len(schemas) == 100
        assert all(s.volume > 0 for s in schemas)


class TestPydanticToSQLAlchemy:
    """Pydantic 스키마 → SQLAlchemy 모델 변환 테스트"""

    def test_daily_price_schema_to_model(self, sample_daily_prices):
        """DailyPrice 스키마를 SQLAlchemy 모델로 변환"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        price_data = sample_daily_prices[0]
        schema = DailyPriceSchema(**price_data)

        # Convert to SQLAlchemy model
        model = DailyPrice(**schema.model_dump())

        assert model.stock_code == schema.stock_code
        assert model.close == schema.close
        assert model.volume == schema.volume

    def test_stock_schema_to_model(self, sample_stock_data):
        """Stock 스키마를 SQLAlchemy 모델로 변환"""
        if StockSchema is None:
            pytest.skip("StockSchema not yet implemented by Agent 1")

        schema = StockSchema(**sample_stock_data)
        model = Stock(**schema.model_dump())

        assert model.code == schema.code
        assert model.name == schema.name
        assert model.market == schema.market


class TestDatabaseOperations:
    """데이터베이스 저장 및 조회 테스트"""

    def test_save_and_retrieve_daily_prices(self, db_session, sample_daily_prices):
        """일봉 데이터 저장 및 조회"""
        # First, create stock
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)
        db_session.commit()

        # Save daily prices
        for price_data in sample_daily_prices:
            daily_price = DailyPrice(**price_data)
            db_session.add(daily_price)
        db_session.commit()

        # Retrieve
        saved_prices = db_session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).all()

        assert len(saved_prices) == len(sample_daily_prices)
        assert saved_prices[0].close == sample_daily_prices[0]['close']

    def test_save_with_pydantic_validation(self, db_session, sample_daily_prices):
        """Pydantic 검증 후 데이터베이스 저장"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Create stock first
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)
        db_session.commit()

        # Validate with Pydantic then save
        for price_data in sample_daily_prices:
            schema = DailyPriceSchema(**price_data)  # Validation
            model = DailyPrice(**schema.model_dump())
            db_session.add(model)
        db_session.commit()

        # Verify
        count = db_session.query(DailyPrice).count()
        assert count == len(sample_daily_prices)

    def test_retrieve_and_validate_with_pydantic(self, db_session, sample_daily_prices):
        """데이터베이스 조회 후 Pydantic 검증"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Setup
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for price_data in sample_daily_prices:
            db_session.add(DailyPrice(**price_data))
        db_session.commit()

        # Retrieve and validate
        saved_prices = db_session.query(DailyPrice).all()
        schemas = [
            DailyPriceSchema.model_validate(price, from_attributes=True)
            for price in saved_prices
        ]

        assert len(schemas) == len(sample_daily_prices)
        assert all(s.high >= s.close for s in schemas)


class TestDatabaseToDataFrame:
    """데이터베이스 → DataFrame 변환 테스트"""

    def test_query_to_dataframe_direct(self, db_session, sample_daily_prices):
        """DB 쿼리 결과를 DataFrame으로 직접 변환"""
        # Setup
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for price_data in sample_daily_prices:
            db_session.add(DailyPrice(**price_data))
        db_session.commit()

        # Query and convert
        query = db_session.query(DailyPrice).filter(DailyPrice.stock_code == '005930')
        df = pd.read_sql(query.statement, db_session.bind)

        assert len(df) == len(sample_daily_prices)
        assert 'close' in df.columns
        assert 'volume' in df.columns

    def test_query_via_pydantic_to_dataframe(self, db_session, sample_daily_prices):
        """DB → Pydantic → DataFrame 변환"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Setup
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for price_data in sample_daily_prices:
            db_session.add(DailyPrice(**price_data))
        db_session.commit()

        # Query → Pydantic → DataFrame
        saved_prices = db_session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).all()

        schemas = [
            DailyPriceSchema.model_validate(price, from_attributes=True)
            for price in saved_prices
        ]

        df = pd.DataFrame([s.model_dump() for s in schemas])

        assert len(df) == len(sample_daily_prices)
        assert (df['high'] >= df['close']).all()


class TestDataFrameToIndicators:
    """DataFrame → TA-Lib 지표 계산 테스트"""

    def test_dataframe_to_indicators(self, sample_ohlcv):
        """DataFrame에 TA-Lib 지표 추가"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(sample_ohlcv)

        assert 'sma_20' in df_with_indicators.columns
        assert 'rsi_14' in df_with_indicators.columns
        assert len(df_with_indicators) == len(sample_ohlcv)

    def test_db_to_indicators_pipeline(self, db_session, sample_daily_prices):
        """DB → DataFrame → 지표 계산 전체 파이프라인"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Setup database
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for price_data in sample_daily_prices:
            db_session.add(DailyPrice(**price_data))
        db_session.commit()

        # Query
        query = db_session.query(DailyPrice).filter(DailyPrice.stock_code == '005930')
        df = pd.read_sql(query.statement, db_session.bind)

        # Calculate indicators
        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        assert 'sma_20' in df_with_indicators.columns
        assert len(df_with_indicators) == len(sample_daily_prices)


class TestFullPipeline:
    """전체 데이터 파이프라인 통합 테스트"""

    def test_complete_data_flow(self, db_session):
        """API → 스키마 → DB → 스키마 → DataFrame → 지표"""
        if DailyPriceSchema is None or TechnicalIndicators is None:
            pytest.skip("Waiting for Agent 1 and Agent 2")

        # 1. Simulate API data
        api_data = []
        for i in range(100):
            api_data.append({
                'stock_code': '005930',
                'date': date(2024, 1, 1) + timedelta(days=i),
                'open': 70000 + i * 10,
                'high': 71000 + i * 10,
                'low': 69000 + i * 10,
                'close': 70500 + i * 10,
                'volume': 10000000
            })

        # 2. Validate with Pydantic
        schemas = [DailyPriceSchema(**data) for data in api_data]

        # 3. Save to database
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for schema in schemas:
            model = DailyPrice(**schema.model_dump())
            db_session.add(model)
        db_session.commit()

        # 4. Retrieve from database
        saved_prices = db_session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).all()

        # 5. Convert to Pydantic
        retrieved_schemas = [
            DailyPriceSchema.model_validate(price, from_attributes=True)
            for price in saved_prices
        ]

        # 6. Convert to DataFrame
        df = pd.DataFrame([s.model_dump() for s in retrieved_schemas])

        # 7. Calculate indicators
        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        # Verify complete pipeline
        assert len(df_with_indicators) == 100
        assert 'sma_20' in df_with_indicators.columns
        assert (df_with_indicators['high'] >= df_with_indicators['close']).all()

    def test_pipeline_to_backtesting(self, db_session, sample_daily_prices):
        """전체 파이프라인 → 백테스팅 엔진"""
        # Setup database
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for price_data in sample_daily_prices:
            db_session.add(DailyPrice(**price_data))
        db_session.commit()

        # Query to DataFrame
        query = db_session.query(DailyPrice).filter(DailyPrice.stock_code == '005930')
        df = pd.read_sql(query.statement, db_session.bind)

        # Add indicators (if available)
        if TechnicalIndicators is not None:
            indicators = TechnicalIndicators()
            df = indicators.calculate_all(df)

        # Create backtest strategy
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=10)

        # Generate signals
        signals = strategy.generate_signals(df)

        assert signals is not None
        assert 'signal' in signals.columns
        assert len(signals) == len(df)


class TestDataIntegrity:
    """데이터 무결성 검증 테스트"""

    def test_roundtrip_data_integrity(self, db_session):
        """API → DB → 조회 데이터 무결성"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        # Original data
        original_data = {
            'stock_code': '005930',
            'date': date(2024, 1, 1),
            'open': 70000,
            'high': 71000,
            'low': 69000,
            'close': 70500,
            'volume': 10000000
        }

        # Save
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        schema = DailyPriceSchema(**original_data)
        model = DailyPrice(**schema.model_dump())
        db_session.add(model)
        db_session.commit()

        # Retrieve
        saved = db_session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930',
            DailyPrice.date == date(2024, 1, 1)
        ).first()

        retrieved_schema = DailyPriceSchema.model_validate(saved, from_attributes=True)

        # Verify integrity
        assert retrieved_schema.stock_code == original_data['stock_code']
        assert retrieved_schema.open == original_data['open']
        assert retrieved_schema.high == original_data['high']
        assert retrieved_schema.low == original_data['low']
        assert retrieved_schema.close == original_data['close']
        assert retrieved_schema.volume == original_data['volume']

    def test_concurrent_read_write(self, db_session):
        """동시 읽기/쓰기 테스트"""
        # This is a simplified test; real concurrent testing would use threading
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        # Write multiple records
        for i in range(10):
            price = DailyPrice(
                stock_code='005930',
                date=date(2024, 1, 1) + timedelta(days=i),
                open=70000, high=71000, low=69000, close=70500, volume=10000000
            )
            db_session.add(price)
        db_session.commit()

        # Read while "writing" (simulate)
        count = db_session.query(DailyPrice).count()
        assert count == 10


class TestCaching:
    """데이터 캐싱 및 최적화 테스트"""

    @pytest.mark.slow
    def test_dataframe_caching_performance(self, db_session):
        """DataFrame 캐싱 성능 테스트"""
        import time

        # Setup large dataset
        stock = Stock(code='005930', name='삼성전자', market='KOSPI')
        db_session.add(stock)

        for i in range(1000):
            db_session.add(DailyPrice(
                stock_code='005930',
                date=date(2020, 1, 1) + timedelta(days=i),
                open=70000, high=71000, low=69000, close=70500, volume=10000000
            ))
        db_session.commit()

        # First query (cold)
        start = time.time()
        query = db_session.query(DailyPrice).filter(DailyPrice.stock_code == '005930')
        df1 = pd.read_sql(query.statement, db_session.bind)
        cold_time = time.time() - start

        # Second query (potentially cached)
        start = time.time()
        query = db_session.query(DailyPrice).filter(DailyPrice.stock_code == '005930')
        df2 = pd.read_sql(query.statement, db_session.bind)
        warm_time = time.time() - start

        print(f"\n✓ Query performance:")
        print(f"  Cold: {cold_time:.3f}s")
        print(f"  Warm: {warm_time:.3f}s")

        assert len(df1) == 1000
        assert len(df2) == 1000
