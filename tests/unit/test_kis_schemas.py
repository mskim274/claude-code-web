"""
Unit tests for KIS API Pydantic schemas.

TDD Red Phase: Write failing tests first.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

# Import will fail initially - this is expected in TDD Red phase
try:
    from collectors.apis.kis.schemas import (
        KISStockPrice,
        KISDailyPrice,
        KISOverseasStock,
        KISOverseasDaily,
        KISMarketType,
        KISExchange
    )
except ImportError:
    pytest.skip("KIS schemas not implemented yet", allow_module_level=True)


class TestKISStockPrice:
    """Test KISStockPrice schema."""

    def test_valid_stock_price(self):
        """Test creating valid stock price object."""
        stock = KISStockPrice(
            code="005930",
            name="삼성전자",
            current_price=70000,
            open=69000,
            high=71000,
            low=68500,
            volume=10000000,
            change=1000,
            change_rate=1.45
        )

        assert stock.code == "005930"
        assert stock.name == "삼성전자"
        assert stock.current_price == 70000
        assert stock.volume == 10000000

    def test_stock_price_with_negative_price_fails(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            KISStockPrice(
                code="005930",
                name="삼성전자",
                current_price=-1000,  # Invalid
                open=69000,
                high=71000,
                low=68500,
                volume=10000000
            )

        assert "current_price" in str(exc_info.value)

    def test_stock_price_with_negative_volume_fails(self):
        """Test that negative volume is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            KISStockPrice(
                code="005930",
                name="삼성전자",
                current_price=70000,
                open=69000,
                high=71000,
                low=68500,
                volume=-1000  # Invalid
            )

        assert "volume" in str(exc_info.value)

    def test_stock_price_missing_required_fields(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ValidationError):
            KISStockPrice(
                code="005930",
                name="삼성전자"
                # Missing required price fields
            )


class TestKISDailyPrice:
    """Test KISDailyPrice schema."""

    def test_valid_daily_price(self):
        """Test creating valid daily price object."""
        daily = KISDailyPrice(
            code="005930",
            date=date(2024, 1, 15),
            open=69000,
            high=71000,
            low=68500,
            close=70000,
            volume=15000000,
            change=1000,
            change_rate=1.45
        )

        assert daily.code == "005930"
        assert daily.date == date(2024, 1, 15)
        assert daily.close == 70000
        assert daily.volume == 15000000

    def test_daily_price_with_string_date(self):
        """Test that string dates are converted."""
        daily = KISDailyPrice(
            code="005930",
            date="2024-01-15",  # String date
            open=69000,
            high=71000,
            low=68500,
            close=70000,
            volume=15000000
        )

        assert isinstance(daily.date, date)
        assert daily.date == date(2024, 1, 15)

    def test_daily_price_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValidationError):
            KISDailyPrice(
                code="005930",
                date="15/01/2024",  # Invalid format
                open=69000,
                high=71000,
                low=68500,
                close=70000,
                volume=15000000
            )


class TestKISOverseasStock:
    """Test KISOverseasStock schema."""

    def test_valid_overseas_stock_nasdaq(self):
        """Test creating valid NASDAQ stock."""
        stock = KISOverseasStock(
            symbol="AAPL",
            exchange=KISExchange.NASDAQ,
            name="Apple Inc.",
            current_price=175.50,
            open=174.00,
            high=176.00,
            low=173.50,
            volume=50000000,
            currency="USD"
        )

        assert stock.symbol == "AAPL"
        assert stock.exchange == KISExchange.NASDAQ
        assert stock.current_price == 175.50
        assert stock.currency == "USD"

    def test_valid_overseas_stock_hkex(self):
        """Test creating valid Hong Kong stock."""
        stock = KISOverseasStock(
            symbol="00700",
            exchange=KISExchange.HKEX,
            name="Tencent",
            current_price=320.50,
            open=318.00,
            high=325.00,
            low=315.00,
            volume=10000000,
            currency="HKD"
        )

        assert stock.symbol == "00700"
        assert stock.exchange == KISExchange.HKEX
        assert stock.currency == "HKD"

    def test_overseas_stock_with_negative_price_fails(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValidationError):
            KISOverseasStock(
                symbol="AAPL",
                exchange=KISExchange.NASDAQ,
                name="Apple Inc.",
                current_price=-100.0,  # Invalid
                open=174.00,
                high=176.00,
                low=173.50,
                volume=50000000,
                currency="USD"
            )

    def test_overseas_stock_default_currency(self):
        """Test that currency defaults to USD."""
        stock = KISOverseasStock(
            symbol="AAPL",
            exchange=KISExchange.NASDAQ,
            name="Apple Inc.",
            current_price=175.50,
            open=174.00,
            high=176.00,
            low=173.50,
            volume=50000000
            # No currency specified
        )

        assert stock.currency == "USD"


class TestKISOverseasDaily:
    """Test KISOverseasDaily schema."""

    def test_valid_overseas_daily(self):
        """Test creating valid overseas daily price."""
        daily = KISOverseasDaily(
            symbol="AAPL",
            exchange=KISExchange.NASDAQ,
            date=date(2024, 1, 15),
            open=174.00,
            high=176.00,
            low=173.50,
            close=175.50,
            volume=50000000,
            currency="USD"
        )

        assert daily.symbol == "AAPL"
        assert daily.exchange == KISExchange.NASDAQ
        assert daily.date == date(2024, 1, 15)
        assert daily.close == 175.50

    def test_overseas_daily_with_string_date(self):
        """Test that string dates are converted."""
        daily = KISOverseasDaily(
            symbol="AAPL",
            exchange=KISExchange.NASDAQ,
            date="2024-01-15",
            open=174.00,
            high=176.00,
            low=173.50,
            close=175.50,
            volume=50000000
        )

        assert isinstance(daily.date, date)


class TestKISEnums:
    """Test KIS enum types."""

    def test_market_type_enum(self):
        """Test MarketType enum values."""
        assert KISMarketType.KOSPI.value == "KOSPI"
        assert KISMarketType.KOSDAQ.value == "KOSDAQ"
        assert KISMarketType.KONEX.value == "KONEX"

    def test_exchange_enum(self):
        """Test Exchange enum values."""
        assert KISExchange.NASDAQ.value == "NASDAQ"
        assert KISExchange.NYSE.value == "NYSE"
        assert KISExchange.AMEX.value == "AMEX"
        assert KISExchange.HKEX.value == "HKEX"
        assert KISExchange.TSE.value == "TSE"  # Tokyo Stock Exchange
        assert KISExchange.SSE.value == "SSE"  # Shanghai Stock Exchange
