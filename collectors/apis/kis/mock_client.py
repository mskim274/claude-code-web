"""
Mock KIS API client for testing without real API calls.

Provides realistic fake data for development and testing.
"""

import random
from datetime import date, datetime, timedelta
from typing import List, Union, Optional

from .schemas import (
    KISStockPrice,
    KISDailyPrice,
    KISOverseasStock,
    KISOverseasDaily,
    KISExchange
)


class MockKISClient:
    """
    Mock KIS API client that returns fake data.

    Compatible with KISClient interface but doesn't make real API calls.
    """

    # Sample Korean stocks
    KOREAN_STOCKS = {
        "005930": {"name": "삼성전자", "base_price": 70000},
        "000660": {"name": "SK하이닉스", "base_price": 130000},
        "035420": {"name": "NAVER", "base_price": 220000},
        "051910": {"name": "LG화학", "base_price": 450000},
        "006400": {"name": "삼성SDI", "base_price": 540000},
        "035720": {"name": "카카오", "base_price": 55000},
        "207940": {"name": "삼성바이오로직스", "base_price": 850000},
        "068270": {"name": "셀트리온", "base_price": 180000},
    }

    # Sample overseas stocks
    OVERSEAS_STOCKS = {
        "AAPL": {"name": "Apple Inc.", "base_price": 175.50, "exchange": KISExchange.NASDAQ},
        "MSFT": {"name": "Microsoft Corp.", "base_price": 380.00, "exchange": KISExchange.NASDAQ},
        "GOOGL": {"name": "Alphabet Inc.", "base_price": 140.00, "exchange": KISExchange.NASDAQ},
        "TSLA": {"name": "Tesla Inc.", "base_price": 240.00, "exchange": KISExchange.NASDAQ},
        "AMZN": {"name": "Amazon.com Inc.", "base_price": 155.00, "exchange": KISExchange.NASDAQ},
        "00700": {"name": "Tencent Holdings", "base_price": 320.50, "exchange": KISExchange.HKEX},
        "9984": {"name": "SoftBank Group", "base_price": 5800.00, "exchange": KISExchange.TSE},
    }

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        rate_limit: int = 5,
        max_retries: int = 3,
        timeout: int = 10,
        delay_ms: int = 0
    ):
        """
        Initialize mock KIS client.

        Args:
            app_key: Ignored (for compatibility)
            app_secret: Ignored (for compatibility)
            rate_limit: Ignored (for compatibility)
            max_retries: Ignored (for compatibility)
            timeout: Ignored (for compatibility)
            delay_ms: Simulated API delay in milliseconds
        """
        self.app_key = app_key or "MOCK_KEY"
        self.app_secret = app_secret or "MOCK_SECRET"
        self.delay_ms = delay_ms

        # For simulating authentication
        self.auth = type('obj', (object,), {
            'get_access_token': lambda: "MOCK_TOKEN",
            'get_auth_headers': lambda: {"authorization": "Bearer MOCK_TOKEN"}
        })()

    def _simulate_delay(self):
        """Simulate API response delay."""
        if self.delay_ms > 0:
            import time
            time.sleep(self.delay_ms / 1000)

    def _generate_random_variation(self, base_value: float, variation: float = 0.02) -> float:
        """
        Generate random variation around a base value.

        Args:
            base_value: Base value
            variation: Variation percentage (default: 2%)

        Returns:
            Value with random variation
        """
        change = random.uniform(-variation, variation)
        return base_value * (1 + change)

    def get_stock_price(self, code: str, market: str = "J") -> KISStockPrice:
        """
        Get mock current price for a domestic stock.

        Args:
            code: Stock code
            market: Market type (ignored)

        Returns:
            Mock stock price data
        """
        self._simulate_delay()

        # Get stock info or use default
        stock_info = self.KOREAN_STOCKS.get(code, {
            "name": f"Stock_{code}",
            "base_price": 50000
        })

        base_price = stock_info["base_price"]

        # Generate realistic daily prices
        open_price = int(self._generate_random_variation(base_price, 0.01))
        high_price = int(self._generate_random_variation(base_price, 0.03))
        low_price = int(self._generate_random_variation(base_price, -0.02))
        current_price = int(self._generate_random_variation(base_price, 0.015))

        # Ensure high/low are correct
        high_price = max(high_price, current_price, open_price)
        low_price = min(low_price, current_price, open_price)

        # Calculate change
        change = current_price - base_price
        change_rate = (change / base_price) * 100

        return KISStockPrice(
            code=code,
            name=stock_info["name"],
            current_price=current_price,
            open=open_price,
            high=high_price,
            low=low_price,
            volume=random.randint(5000000, 20000000),
            change=change,
            change_rate=round(change_rate, 2)
        )

    def get_daily_price(
        self,
        code: str,
        start_date: Union[str, date],
        end_date: Union[str, date],
        market: str = "J"
    ) -> List[KISDailyPrice]:
        """
        Get mock daily price history for a domestic stock.

        Args:
            code: Stock code
            start_date: Start date
            end_date: End date
            market: Market type (ignored)

        Returns:
            List of mock daily price data
        """
        self._simulate_delay()

        # Convert dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y%m%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y%m%d").date()

        # Get base price
        stock_info = self.KOREAN_STOCKS.get(code, {"base_price": 50000})
        base_price = stock_info["base_price"]

        # Generate daily data
        results = []
        current_date = start_date
        current_price = base_price

        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Random walk for realistic price movement
                price_change = random.uniform(-0.03, 0.03)
                current_price = int(current_price * (1 + price_change))

                open_price = int(self._generate_random_variation(current_price, 0.01))
                high_price = int(self._generate_random_variation(current_price, 0.02))
                low_price = int(self._generate_random_variation(current_price, -0.015))
                close_price = current_price

                # Ensure high/low are correct
                high_price = max(high_price, close_price, open_price)
                low_price = min(low_price, close_price, open_price)

                change = close_price - open_price
                change_rate = (change / open_price) * 100 if open_price > 0 else 0

                results.append(KISDailyPrice(
                    code=code,
                    date=current_date,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=random.randint(5000000, 20000000),
                    change=change,
                    change_rate=round(change_rate, 2)
                ))

            current_date += timedelta(days=1)

        return results

    def get_overseas_stock(
        self,
        symbol: str,
        exchange: Union[str, KISExchange]
    ) -> KISOverseasStock:
        """
        Get mock current price for an overseas stock.

        Args:
            symbol: Stock symbol
            exchange: Exchange code

        Returns:
            Mock overseas stock price data
        """
        self._simulate_delay()

        # Convert exchange to enum if string
        if isinstance(exchange, str):
            exchange = KISExchange(exchange.upper())

        # Get stock info or use default
        stock_info = self.OVERSEAS_STOCKS.get(symbol, {
            "name": f"{symbol}",
            "base_price": 100.0,
            "exchange": exchange
        })

        base_price = stock_info["base_price"]

        # Generate realistic prices
        open_price = self._generate_random_variation(base_price, 0.01)
        high_price = self._generate_random_variation(base_price, 0.03)
        low_price = self._generate_random_variation(base_price, -0.02)
        current_price = self._generate_random_variation(base_price, 0.015)

        # Ensure high/low are correct
        high_price = max(high_price, current_price, open_price)
        low_price = min(low_price, current_price, open_price)

        # Calculate change
        change = current_price - base_price
        change_rate = (change / base_price) * 100

        # Determine currency
        currency_map = {
            KISExchange.NASDAQ: "USD",
            KISExchange.NYSE: "USD",
            KISExchange.AMEX: "USD",
            KISExchange.HKEX: "HKD",
            KISExchange.TSE: "JPY",
            KISExchange.SSE: "CNY",
            KISExchange.SZSE: "CNY"
        }

        return KISOverseasStock(
            symbol=symbol,
            exchange=exchange,
            name=stock_info["name"],
            current_price=round(current_price, 2),
            open=round(open_price, 2),
            high=round(high_price, 2),
            low=round(low_price, 2),
            volume=random.randint(10000000, 100000000),
            currency=currency_map.get(exchange, "USD"),
            change=round(change, 2),
            change_rate=round(change_rate, 2)
        )

    def get_overseas_daily(
        self,
        symbol: str,
        exchange: Union[str, KISExchange],
        period: int = 30
    ) -> List[KISOverseasDaily]:
        """
        Get mock daily price history for an overseas stock.

        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Number of days

        Returns:
            List of mock daily price data
        """
        self._simulate_delay()

        # Convert exchange to enum if string
        if isinstance(exchange, str):
            exchange = KISExchange(exchange.upper())

        # Get base price
        stock_info = self.OVERSEAS_STOCKS.get(symbol, {"base_price": 100.0})
        base_price = stock_info["base_price"]

        # Currency
        currency_map = {
            KISExchange.NASDAQ: "USD",
            KISExchange.NYSE: "USD",
            KISExchange.AMEX: "USD",
            KISExchange.HKEX: "HKD",
            KISExchange.TSE: "JPY",
            KISExchange.SSE: "CNY",
            KISExchange.SZSE: "CNY"
        }
        currency = currency_map.get(exchange, "USD")

        # Generate daily data
        results = []
        current_price = base_price
        current_date = date.today()

        for _ in range(period):
            # Skip weekends
            while current_date.weekday() >= 5:
                current_date -= timedelta(days=1)

            # Random walk
            price_change = random.uniform(-0.03, 0.03)
            current_price = current_price * (1 + price_change)

            open_price = self._generate_random_variation(current_price, 0.01)
            high_price = self._generate_random_variation(current_price, 0.02)
            low_price = self._generate_random_variation(current_price, -0.015)
            close_price = current_price

            # Ensure high/low are correct
            high_price = max(high_price, close_price, open_price)
            low_price = min(low_price, close_price, open_price)

            results.append(KISOverseasDaily(
                symbol=symbol,
                exchange=exchange,
                date=current_date,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=random.randint(10000000, 100000000),
                currency=currency
            ))

            current_date -= timedelta(days=1)

        return results

    def close(self):
        """Close the client (no-op for mock)."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
