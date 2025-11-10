"""
Pydantic 스키마 단위 테스트 (TDD)
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError
from unittest.mock import MagicMock

from db.schemas import (
    StockSchema,
    DailyPriceSchema,
    MinutePriceSchema,
    TickPriceSchema,
    InvestorTradingSchema,
    StockInfoSchema,
    CollectionLogSchema,
)


# ==================== Stock 스키마 테스트 ====================

class TestStockSchema:
    """Stock 스키마 테스트"""

    def test_stock_schema_valid(self):
        """유효한 종목 데이터로 스키마 생성"""
        data = {
            "code": "005930",
            "name": "삼성전자",
            "market": "KOSPI"
        }
        stock = StockSchema(**data)
        assert stock.code == "005930"
        assert stock.name == "삼성전자"
        assert stock.market == "KOSPI"

    def test_stock_schema_with_optional_fields(self):
        """선택적 필드를 포함한 유효한 데이터"""
        data = {
            "code": "005930",
            "name": "삼성전자",
            "market": "KOSPI",
            "sector": "전기전자",
            "listing_date": date(1975, 6, 11)
        }
        stock = StockSchema(**data)
        assert stock.sector == "전기전자"
        assert stock.listing_date == date(1975, 6, 11)

    def test_stock_schema_invalid_code_non_numeric(self):
        """종목코드가 숫자가 아닌 경우 (영문 포함)"""
        with pytest.raises(ValidationError) as exc_info:
            StockSchema(code="abc123", name="테스트", market="KOSPI")
        errors = exc_info.value.errors()
        assert any("code" in str(error["loc"]) for error in errors)

    def test_stock_schema_invalid_code_too_short(self):
        """종목코드가 너무 짧은 경우 (6자 미만)"""
        with pytest.raises(ValidationError) as exc_info:
            StockSchema(code="12345", name="테스트", market="KOSPI")
        errors = exc_info.value.errors()
        assert any("code" in str(error["loc"]) for error in errors)

    def test_stock_schema_invalid_code_too_long(self):
        """종목코드가 너무 긴 경우 (10자 초과)"""
        with pytest.raises(ValidationError) as exc_info:
            StockSchema(code="12345678901", name="테스트", market="KOSPI")
        errors = exc_info.value.errors()
        assert any("code" in str(error["loc"]) for error in errors)

    def test_stock_schema_invalid_market(self):
        """잘못된 시장 구분 (KOSPI, KOSDAQ 외)"""
        with pytest.raises(ValidationError) as exc_info:
            StockSchema(code="005930", name="삼성전자", market="NYSE")
        errors = exc_info.value.errors()
        assert any("market" in str(error["loc"]) for error in errors)

    def test_stock_schema_empty_name(self):
        """종목명이 비어있는 경우"""
        with pytest.raises(ValidationError) as exc_info:
            StockSchema(code="005930", name="", market="KOSPI")
        errors = exc_info.value.errors()
        assert any("name" in str(error["loc"]) for error in errors)

    def test_stock_schema_name_too_long(self):
        """종목명이 너무 긴 경우 (100자 초과)"""
        long_name = "A" * 101
        with pytest.raises(ValidationError) as exc_info:
            StockSchema(code="005930", name=long_name, market="KOSPI")
        errors = exc_info.value.errors()
        assert any("name" in str(error["loc"]) for error in errors)

    def test_stock_schema_kosdaq_market(self):
        """KOSDAQ 시장 종목"""
        data = {
            "code": "035720",
            "name": "카카오",
            "market": "KOSDAQ"
        }
        stock = StockSchema(**data)
        assert stock.market == "KOSDAQ"


# ==================== DailyPrice 스키마 테스트 ====================

class TestDailyPriceSchema:
    """DailyPrice 스키마 테스트"""

    def test_daily_price_schema_valid(self):
        """유효한 일봉 데이터로 스키마 생성"""
        data = {
            "stock_code": "005930",
            "date": date(2024, 1, 1),
            "open": 70000,
            "high": 72000,
            "low": 69000,
            "close": 71000,
            "volume": 10000000
        }
        daily_price = DailyPriceSchema(**data)
        assert daily_price.stock_code == "005930"
        assert daily_price.close == 71000
        assert daily_price.volume == 10000000

    def test_daily_price_schema_high_low_validation(self):
        """고가가 저가보다 낮은 경우 (잘못됨)"""
        with pytest.raises(ValidationError) as exc_info:
            DailyPriceSchema(
                stock_code="005930",
                date=date(2024, 1, 1),
                open=70000,
                high=69000,  # high < low (잘못됨)
                low=70000,
                close=69500,
                volume=1000000
            )
        errors = exc_info.value.errors()
        # 가격 검증 에러가 있어야 함
        assert len(errors) > 0

    def test_daily_price_schema_close_out_of_range(self):
        """종가가 고가/저가 범위를 벗어난 경우"""
        with pytest.raises(ValidationError) as exc_info:
            DailyPriceSchema(
                stock_code="005930",
                date=date(2024, 1, 1),
                open=70000,
                high=72000,
                low=69000,
                close=73000,  # close > high (잘못됨)
                volume=1000000
            )
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_daily_price_schema_negative_price(self):
        """음수 가격"""
        with pytest.raises(ValidationError) as exc_info:
            DailyPriceSchema(
                stock_code="005930",
                date=date(2024, 1, 1),
                open=-1,
                high=72000,
                low=69000,
                close=71000,
                volume=1000000
            )
        errors = exc_info.value.errors()
        assert any("open" in str(error["loc"]) for error in errors)

    def test_daily_price_schema_zero_volume(self):
        """거래량이 0인 경우 (허용되어야 함 - 거래정지 등)"""
        data = {
            "stock_code": "005930",
            "date": date(2024, 1, 1),
            "open": 70000,
            "high": 70000,
            "low": 70000,
            "close": 70000,
            "volume": 0
        }
        daily_price = DailyPriceSchema(**data)
        assert daily_price.volume == 0

    def test_daily_price_schema_with_optional_fields(self):
        """선택적 필드를 포함한 유효한 데이터"""
        data = {
            "stock_code": "005930",
            "date": date(2024, 1, 1),
            "open": 70000,
            "high": 72000,
            "low": 69000,
            "close": 71000,
            "volume": 10000000,
            "trading_value": 710000000000,
            "change": 1000,
            "change_rate": 1.43,
            "adj_close": 71000.0,
            "adj_factor": 1.0
        }
        daily_price = DailyPriceSchema(**data)
        assert daily_price.trading_value == 710000000000
        assert daily_price.change == 1000
        assert daily_price.change_rate == 1.43

    def test_daily_price_schema_open_out_of_range(self):
        """시가가 고가/저가 범위를 벗어난 경우"""
        with pytest.raises(ValidationError) as exc_info:
            DailyPriceSchema(
                stock_code="005930",
                date=date(2024, 1, 1),
                open=73000,  # open > high (잘못됨)
                high=72000,
                low=69000,
                close=71000,
                volume=1000000
            )
        errors = exc_info.value.errors()
        assert len(errors) > 0


# ==================== MinutePrice 스키마 테스트 ====================

class TestMinutePriceSchema:
    """MinutePrice 스키마 테스트"""

    def test_minute_price_schema_valid(self):
        """유효한 분봉 데이터로 스키마 생성"""
        data = {
            "stock_code": "005930",
            "datetime": datetime(2024, 1, 1, 9, 0, 0),
            "interval": 1,
            "open": 70000,
            "high": 72000,
            "low": 69000,
            "close": 71000,
            "volume": 1000000
        }
        minute_price = MinutePriceSchema(**data)
        assert minute_price.interval == 1
        assert minute_price.close == 71000

    def test_minute_price_schema_valid_intervals(self):
        """유효한 분봉 간격들 (1, 3, 5, 10, 15, 30, 45, 60)"""
        valid_intervals = [1, 3, 5, 10, 15, 30, 45, 60]
        for interval in valid_intervals:
            data = {
                "stock_code": "005930",
                "datetime": datetime(2024, 1, 1, 9, 0, 0),
                "interval": interval,
                "open": 70000,
                "high": 72000,
                "low": 69000,
                "close": 71000,
                "volume": 1000000
            }
            minute_price = MinutePriceSchema(**data)
            assert minute_price.interval == interval

    def test_minute_price_schema_invalid_interval(self):
        """잘못된 분봉 간격 (허용되지 않는 값)"""
        with pytest.raises(ValidationError) as exc_info:
            MinutePriceSchema(
                stock_code="005930",
                datetime=datetime(2024, 1, 1, 9, 0, 0),
                interval=7,  # 허용되지 않는 간격
                open=70000,
                high=72000,
                low=69000,
                close=71000,
                volume=1000000
            )
        errors = exc_info.value.errors()
        assert any("interval" in str(error["loc"]) for error in errors)

    def test_minute_price_schema_price_validation(self):
        """가격 검증 (high >= close >= low)"""
        with pytest.raises(ValidationError) as exc_info:
            MinutePriceSchema(
                stock_code="005930",
                datetime=datetime(2024, 1, 1, 9, 0, 0),
                interval=1,
                open=70000,
                high=69000,  # high < low (잘못됨)
                low=70000,
                close=69500,
                volume=1000000
            )
        errors = exc_info.value.errors()
        assert len(errors) > 0


# ==================== TickPrice 스키마 테스트 ====================

class TestTickPriceSchema:
    """TickPrice 스키마 테스트"""

    def test_tick_price_schema_valid(self):
        """유효한 틱 데이터로 스키마 생성"""
        data = {
            "stock_code": "005930",
            "datetime": datetime(2024, 1, 1, 9, 0, 0),
            "price": 71000,
            "volume": 100
        }
        tick_price = TickPriceSchema(**data)
        assert tick_price.price == 71000
        assert tick_price.volume == 100

    def test_tick_price_schema_with_optional_fields(self):
        """선택적 필드를 포함한 유효한 데이터"""
        data = {
            "stock_code": "005930",
            "datetime": datetime(2024, 1, 1, 9, 0, 0),
            "price": 71000,
            "volume": 100,
            "change": 1000,
            "ask_volume": 5000,
            "bid_volume": 3000,
            "market_type": "장중"
        }
        tick_price = TickPriceSchema(**data)
        assert tick_price.ask_volume == 5000
        assert tick_price.bid_volume == 3000
        assert tick_price.market_type == "장중"

    def test_tick_price_schema_negative_price(self):
        """음수 가격"""
        with pytest.raises(ValidationError) as exc_info:
            TickPriceSchema(
                stock_code="005930",
                datetime=datetime(2024, 1, 1, 9, 0, 0),
                price=-1,
                volume=100
            )
        errors = exc_info.value.errors()
        assert any("price" in str(error["loc"]) for error in errors)

    def test_tick_price_schema_zero_volume(self):
        """거래량이 0인 경우"""
        data = {
            "stock_code": "005930",
            "datetime": datetime(2024, 1, 1, 9, 0, 0),
            "price": 71000,
            "volume": 0
        }
        tick_price = TickPriceSchema(**data)
        assert tick_price.volume == 0


# ==================== InvestorTrading 스키마 테스트 ====================

class TestInvestorTradingSchema:
    """InvestorTrading 스키마 테스트"""

    def test_investor_trading_schema_valid(self):
        """유효한 투자자 매매 동향 데이터로 스키마 생성"""
        data = {
            "stock_code": "005930",
            "date": date(2024, 1, 1),
            "institution_buy": 1000000,
            "institution_sell": 800000,
            "institution_net": 200000,
            "foreign_buy": 500000,
            "foreign_sell": 600000,
            "foreign_net": -100000,
            "individual_buy": 300000,
            "individual_sell": 200000,
            "individual_net": 100000
        }
        investor_trading = InvestorTradingSchema(**data)
        assert investor_trading.institution_net == 200000
        assert investor_trading.foreign_net == -100000
        assert investor_trading.individual_net == 100000

    def test_investor_trading_schema_with_defaults(self):
        """기본값이 적용된 경우"""
        data = {
            "stock_code": "005930",
            "date": date(2024, 1, 1)
        }
        investor_trading = InvestorTradingSchema(**data)
        assert investor_trading.institution_buy == 0
        assert investor_trading.institution_sell == 0
        assert investor_trading.institution_net == 0

    def test_investor_trading_schema_negative_net(self):
        """순매수가 음수인 경우 (매도 > 매수)"""
        data = {
            "stock_code": "005930",
            "date": date(2024, 1, 1),
            "institution_buy": 100000,
            "institution_sell": 200000,
            "institution_net": -100000
        }
        investor_trading = InvestorTradingSchema(**data)
        assert investor_trading.institution_net == -100000


# ==================== StockInfo 스키마 테스트 ====================

class TestStockInfoSchema:
    """StockInfo 스키마 테스트"""

    def test_stock_info_schema_valid(self):
        """유효한 종목 상세 정보로 스키마 생성"""
        data = {
            "stock_code": "005930",
            "market_cap": 400000000000000,
            "shares_outstanding": 5969782550,
            "par_value": 100,
            "per": 15.5,
            "pbr": 1.2,
            "roe": 8.5,
            "eps": 5000,
            "bps": 50000
        }
        stock_info = StockInfoSchema(**data)
        assert stock_info.stock_code == "005930"
        assert stock_info.per == 15.5
        assert stock_info.pbr == 1.2

    def test_stock_info_schema_minimal(self):
        """최소 필수 필드만 있는 경우"""
        data = {
            "stock_code": "005930"
        }
        stock_info = StockInfoSchema(**data)
        assert stock_info.stock_code == "005930"
        assert stock_info.per is None

    def test_stock_info_schema_with_52w_high_low(self):
        """52주 고저 정보를 포함한 경우"""
        data = {
            "stock_code": "005930",
            "high_52w": 80000,
            "low_52w": 60000,
            "high_52w_date": date(2024, 3, 15),
            "low_52w_date": date(2024, 1, 10)
        }
        stock_info = StockInfoSchema(**data)
        assert stock_info.high_52w == 80000
        assert stock_info.low_52w == 60000

    def test_stock_info_schema_negative_per(self):
        """음수 PER (적자 기업의 경우 허용)"""
        data = {
            "stock_code": "005930",
            "per": -5.0
        }
        stock_info = StockInfoSchema(**data)
        assert stock_info.per == -5.0


# ==================== CollectionLog 스키마 테스트 ====================

class TestCollectionLogSchema:
    """CollectionLog 스키마 테스트"""

    def test_collection_log_schema_valid(self):
        """유효한 수집 로그 데이터로 스키마 생성"""
        data = {
            "stock_code": "005930",
            "collection_type": "daily",
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 31),
            "status": "success",
            "records_collected": 20
        }
        collection_log = CollectionLogSchema(**data)
        assert collection_log.collection_type == "daily"
        assert collection_log.status == "success"
        assert collection_log.records_collected == 20

    def test_collection_log_schema_valid_status(self):
        """유효한 상태 값들 (success, failed, in_progress)"""
        valid_statuses = ["success", "failed", "in_progress"]
        for status in valid_statuses:
            data = {
                "collection_type": "daily",
                "status": status
            }
            collection_log = CollectionLogSchema(**data)
            assert collection_log.status == status

    def test_collection_log_schema_invalid_status(self):
        """잘못된 상태 값"""
        with pytest.raises(ValidationError) as exc_info:
            CollectionLogSchema(
                collection_type="daily",
                status="invalid_status"
            )
        errors = exc_info.value.errors()
        assert any("status" in str(error["loc"]) for error in errors)

    def test_collection_log_schema_without_stock_code(self):
        """종목코드가 없는 경우 (전체 수집)"""
        data = {
            "collection_type": "daily",
            "status": "success",
            "records_collected": 1000
        }
        collection_log = CollectionLogSchema(**data)
        assert collection_log.stock_code is None
        assert collection_log.records_collected == 1000

    def test_collection_log_schema_with_error_message(self):
        """에러 메시지를 포함한 실패 로그"""
        data = {
            "stock_code": "005930",
            "collection_type": "daily",
            "status": "failed",
            "records_collected": 0,
            "error_message": "Connection timeout"
        }
        collection_log = CollectionLogSchema(**data)
        assert collection_log.status == "failed"
        assert collection_log.error_message == "Connection timeout"

    def test_collection_log_schema_error_message_too_long(self):
        """에러 메시지가 너무 긴 경우 (500자 초과)"""
        long_message = "A" * 501
        with pytest.raises(ValidationError) as exc_info:
            CollectionLogSchema(
                collection_type="daily",
                status="failed",
                error_message=long_message
            )
        errors = exc_info.value.errors()
        assert any("error_message" in str(error["loc"]) for error in errors)


# ==================== SQLAlchemy 호환성 테스트 ====================

class TestSQLAlchemyCompatibility:
    """SQLAlchemy ORM 모델과 Pydantic 스키마 호환성 테스트"""

    def test_stock_from_orm(self):
        """Stock ORM 모델을 Pydantic 스키마로 변환"""
        # Mock SQLAlchemy 모델 객체
        mock_stock = MagicMock()
        mock_stock.code = "005930"
        mock_stock.name = "삼성전자"
        mock_stock.market = "KOSPI"
        mock_stock.sector = "전기전자"
        mock_stock.listing_date = date(1975, 6, 11)
        mock_stock.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_stock.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        # Pydantic 스키마로 변환
        stock_schema = StockSchema.model_validate(mock_stock)

        assert stock_schema.code == "005930"
        assert stock_schema.name == "삼성전자"
        assert stock_schema.market == "KOSPI"

    def test_daily_price_from_orm(self):
        """DailyPrice ORM 모델을 Pydantic 스키마로 변환"""
        mock_daily_price = MagicMock()
        mock_daily_price.id = 1
        mock_daily_price.stock_code = "005930"
        mock_daily_price.date = date(2024, 1, 1)
        mock_daily_price.open = 70000
        mock_daily_price.high = 72000
        mock_daily_price.low = 69000
        mock_daily_price.close = 71000
        mock_daily_price.volume = 10000000
        mock_daily_price.trading_value = 710000000000
        mock_daily_price.change = 1000
        mock_daily_price.change_rate = 1.43
        mock_daily_price.adj_close = 71000.0
        mock_daily_price.adj_factor = 1.0
        mock_daily_price.created_at = datetime(2024, 1, 1, 0, 0, 0)

        daily_price_schema = DailyPriceSchema.model_validate(mock_daily_price)

        assert daily_price_schema.stock_code == "005930"
        assert daily_price_schema.close == 71000
        assert daily_price_schema.volume == 10000000

    def test_minute_price_from_orm(self):
        """MinutePrice ORM 모델을 Pydantic 스키마로 변환"""
        mock_minute_price = MagicMock()
        mock_minute_price.id = 1
        mock_minute_price.stock_code = "005930"
        mock_minute_price.datetime = datetime(2024, 1, 1, 9, 0, 0)
        mock_minute_price.interval = 1
        mock_minute_price.open = 70000
        mock_minute_price.high = 72000
        mock_minute_price.low = 69000
        mock_minute_price.close = 71000
        mock_minute_price.volume = 1000000
        mock_minute_price.created_at = datetime(2024, 1, 1, 9, 0, 0)

        minute_price_schema = MinutePriceSchema.model_validate(mock_minute_price)

        assert minute_price_schema.stock_code == "005930"
        assert minute_price_schema.interval == 1
        assert minute_price_schema.close == 71000

    def test_tick_price_from_orm(self):
        """TickPrice ORM 모델을 Pydantic 스키마로 변환"""
        mock_tick_price = MagicMock()
        mock_tick_price.id = 1
        mock_tick_price.stock_code = "005930"
        mock_tick_price.datetime = datetime(2024, 1, 1, 9, 0, 0)
        mock_tick_price.price = 71000
        mock_tick_price.volume = 100
        mock_tick_price.change = 1000
        mock_tick_price.ask_volume = 5000
        mock_tick_price.bid_volume = 3000
        mock_tick_price.market_type = "장중"
        mock_tick_price.created_at = datetime(2024, 1, 1, 9, 0, 0)

        tick_price_schema = TickPriceSchema.model_validate(mock_tick_price)

        assert tick_price_schema.price == 71000
        assert tick_price_schema.volume == 100
        assert tick_price_schema.market_type == "장중"

    def test_investor_trading_from_orm(self):
        """InvestorTrading ORM 모델을 Pydantic 스키마로 변환"""
        mock_investor_trading = MagicMock()
        mock_investor_trading.id = 1
        mock_investor_trading.stock_code = "005930"
        mock_investor_trading.date = date(2024, 1, 1)
        mock_investor_trading.institution_buy = 1000000
        mock_investor_trading.institution_sell = 800000
        mock_investor_trading.institution_net = 200000
        mock_investor_trading.foreign_buy = 500000
        mock_investor_trading.foreign_sell = 600000
        mock_investor_trading.foreign_net = -100000
        mock_investor_trading.individual_buy = 300000
        mock_investor_trading.individual_sell = 200000
        mock_investor_trading.individual_net = 100000
        mock_investor_trading.created_at = datetime(2024, 1, 1, 0, 0, 0)

        investor_trading_schema = InvestorTradingSchema.model_validate(mock_investor_trading)

        assert investor_trading_schema.institution_net == 200000
        assert investor_trading_schema.foreign_net == -100000

    def test_stock_info_from_orm(self):
        """StockInfo ORM 모델을 Pydantic 스키마로 변환"""
        mock_stock_info = MagicMock()
        mock_stock_info.stock_code = "005930"
        mock_stock_info.market_cap = 400000000000000
        mock_stock_info.shares_outstanding = 5969782550
        mock_stock_info.par_value = 100
        mock_stock_info.per = 15.5
        mock_stock_info.pbr = 1.2
        mock_stock_info.roe = 8.5
        mock_stock_info.eps = 5000
        mock_stock_info.bps = 50000
        mock_stock_info.dividend_yield = 2.5
        mock_stock_info.dividend_per_share = 1000
        mock_stock_info.credit_ratio = 5.0
        mock_stock_info.short_selling_ratio = 3.0
        mock_stock_info.high_52w = 80000
        mock_stock_info.low_52w = 60000
        mock_stock_info.high_52w_date = date(2024, 3, 15)
        mock_stock_info.low_52w_date = date(2024, 1, 10)
        mock_stock_info.updated_at = datetime(2024, 1, 1, 0, 0, 0)

        stock_info_schema = StockInfoSchema.model_validate(mock_stock_info)

        assert stock_info_schema.stock_code == "005930"
        assert stock_info_schema.per == 15.5
        assert stock_info_schema.pbr == 1.2

    def test_collection_log_from_orm(self):
        """CollectionLog ORM 모델을 Pydantic 스키마로 변환"""
        mock_collection_log = MagicMock()
        mock_collection_log.id = 1
        mock_collection_log.stock_code = "005930"
        mock_collection_log.collection_type = "daily"
        mock_collection_log.start_date = date(2024, 1, 1)
        mock_collection_log.end_date = date(2024, 1, 31)
        mock_collection_log.status = "success"
        mock_collection_log.records_collected = 20
        mock_collection_log.error_message = None
        mock_collection_log.started_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_collection_log.completed_at = datetime(2024, 1, 1, 1, 0, 0)

        collection_log_schema = CollectionLogSchema.model_validate(mock_collection_log)

        assert collection_log_schema.collection_type == "daily"
        assert collection_log_schema.status == "success"
        assert collection_log_schema.records_collected == 20
