"""
Integration tests for KIS API client.

Tests full workflow using mock client.
"""

import pytest
from datetime import date, timedelta

from collectors.apis.kis.mock_client import MockKISClient
from collectors.apis.kis.schemas import (
    KISStockPrice,
    KISDailyPrice,
    KISOverseasStock,
    KISOverseasDaily,
    KISExchange
)


class TestKISClientIntegration:
    """Integration tests for KIS API client."""

    @pytest.fixture
    def client(self):
        """Create mock KIS client for testing."""
        return MockKISClient(delay_ms=10)

    def test_domestic_stock_workflow(self, client):
        """Test complete domestic stock data retrieval workflow."""
        # Get current price
        price = client.get_stock_price("005930")

        assert isinstance(price, KISStockPrice)
        assert price.code == "005930"
        assert price.name == "삼성전자"
        assert price.current_price > 0
        assert price.volume > 0

        # Verify OHLC relationships
        assert price.high >= price.current_price
        assert price.low <= price.current_price

    def test_domestic_daily_history_workflow(self, client):
        """Test daily price history retrieval workflow."""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Get historical data
        history = client.get_daily_price(
            "005930",
            start_date=start_date,
            end_date=end_date
        )

        assert len(history) > 0
        assert all(isinstance(item, KISDailyPrice) for item in history)

        # Verify dates are in range
        for item in history:
            assert start_date <= item.date <= end_date

        # Verify data consistency
        for item in history:
            assert item.high >= item.close
            assert item.low <= item.close
            assert item.volume >= 0

    def test_overseas_stock_workflow(self, client):
        """Test complete overseas stock data retrieval workflow."""
        # Get NASDAQ stock
        price = client.get_overseas_stock("AAPL", KISExchange.NASDAQ)

        assert isinstance(price, KISOverseasStock)
        assert price.symbol == "AAPL"
        assert price.exchange == KISExchange.NASDAQ
        assert price.current_price > 0
        assert price.currency == "USD"

        # Verify OHLC relationships
        assert price.high >= price.current_price
        assert price.low <= price.current_price

    def test_overseas_daily_history_workflow(self, client):
        """Test overseas daily price history workflow."""
        # Get 30 days of data
        history = client.get_overseas_daily(
            "AAPL",
            KISExchange.NASDAQ,
            period=30
        )

        assert len(history) == 30
        assert all(isinstance(item, KISOverseasDaily) for item in history)

        # Verify data consistency
        for item in history:
            assert item.symbol == "AAPL"
            assert item.exchange == KISExchange.NASDAQ
            assert item.high >= item.close
            assert item.low <= item.close
            assert item.volume >= 0
            assert item.currency == "USD"

    def test_multiple_stocks_retrieval(self, client):
        """Test retrieving data for multiple stocks."""
        stock_codes = ["005930", "000660", "035420"]

        results = []
        for code in stock_codes:
            price = client.get_stock_price(code)
            results.append(price)

        assert len(results) == 3
        assert all(isinstance(item, KISStockPrice) for item in results)
        assert [item.code for item in results] == stock_codes

    def test_different_exchanges(self, client):
        """Test retrieving stocks from different exchanges."""
        test_cases = [
            ("AAPL", KISExchange.NASDAQ),
            ("00700", KISExchange.HKEX),
            ("9984", KISExchange.TSE),
        ]

        for symbol, exchange in test_cases:
            price = client.get_overseas_stock(symbol, exchange)

            assert price.symbol == symbol
            assert price.exchange == exchange
            assert price.current_price > 0

    def test_context_manager_usage(self):
        """Test using client as context manager."""
        with MockKISClient() as client:
            price = client.get_stock_price("005930")
            assert isinstance(price, KISStockPrice)

        # Client should be closed after context

    def test_date_range_filtering(self, client):
        """Test date range filtering in historical data."""
        end_date = date(2024, 1, 15)
        start_date = date(2024, 1, 1)

        history = client.get_daily_price(
            "005930",
            start_date=start_date,
            end_date=end_date
        )

        # All dates should be within range
        for item in history:
            assert start_date <= item.date <= end_date

        # Should have data (excluding weekends)
        assert len(history) > 0


class TestKISClientErrorHandling:
    """Test error handling in integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create mock KIS client."""
        return MockKISClient()

    def test_unknown_stock_code_returns_default(self, client):
        """Test that unknown stock codes return default data."""
        price = client.get_stock_price("999999")

        assert isinstance(price, KISStockPrice)
        assert price.code == "999999"
        # Should have some default price
        assert price.current_price > 0

    def test_unknown_overseas_symbol_returns_default(self, client):
        """Test that unknown overseas symbols return default data."""
        price = client.get_overseas_stock("UNKNOWN", KISExchange.NASDAQ)

        assert isinstance(price, KISOverseasStock)
        assert price.symbol == "UNKNOWN"
        assert price.current_price > 0


class TestKISClientPerformance:
    """Test performance characteristics."""

    def test_batch_requests_complete_reasonably(self):
        """Test that batch requests complete in reasonable time."""
        import time

        client = MockKISClient(delay_ms=10)
        stock_codes = ["005930", "000660", "035420", "051910", "006400"]

        start_time = time.time()

        for code in stock_codes:
            client.get_stock_price(code)

        elapsed = time.time() - start_time

        # With 10ms delay per request, 5 requests should take ~50ms + overhead
        assert elapsed < 1.0  # Should be well under 1 second

    def test_no_delay_mode_is_fast(self):
        """Test that no-delay mode is very fast."""
        import time

        client = MockKISClient(delay_ms=0)

        start_time = time.time()

        for _ in range(10):
            client.get_stock_price("005930")

        elapsed = time.time() - start_time

        # 10 requests should complete very quickly
        assert elapsed < 0.5  # Under 500ms


class TestKISClientDataQuality:
    """Test data quality and consistency."""

    @pytest.fixture
    def client(self):
        """Create mock KIS client."""
        return MockKISClient()

    def test_price_data_is_realistic(self, client):
        """Test that generated prices are realistic."""
        price = client.get_stock_price("005930")

        # Samsung Electronics typically trades in reasonable range
        assert 40000 <= price.current_price <= 100000

        # Intraday range should be reasonable
        daily_range = price.high - price.low
        price_range_percent = (daily_range / price.current_price) * 100

        # Daily range should be reasonable (typically < 10%)
        assert price_range_percent < 20

    def test_volume_is_positive(self, client):
        """Test that volume is always positive."""
        codes = ["005930", "000660", "035420"]

        for code in codes:
            price = client.get_stock_price(code)
            assert price.volume > 0

    def test_historical_prices_show_variation(self, client):
        """Test that historical prices show realistic variation."""
        history = client.get_daily_price(
            "005930",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        # Should have some variation in prices
        prices = [item.close for item in history]
        assert len(set(prices)) > 1  # Not all the same

        # Calculate price volatility
        if len(prices) > 1:
            price_changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            avg_change = sum(price_changes) / len(price_changes)

            # Should have some movement (not completely flat)
            assert avg_change > 0
