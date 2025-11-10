"""
KIS API Client implementation.

Provides methods to interact with Korean Investment & Securities OpenAPI.
"""

import os
import time
import requests
from typing import List, Dict, Optional, Union
from datetime import date, datetime
import logging

from .auth import KISAuth, AuthenticationError
from .schemas import (
    KISStockPrice,
    KISDailyPrice,
    KISOverseasStock,
    KISOverseasDaily,
    KISExchange,
    KISMarketType
)
from .rate_limiter import TokenBucketRateLimiter

# Setup logging
logger = logging.getLogger(__name__)


class KISAPIError(Exception):
    """Base exception for KIS API errors."""
    pass


class KISNetworkError(KISAPIError):
    """Network-related errors."""
    pass


class KISRateLimitError(KISAPIError):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class KISClient:
    """
    KIS API client for Korean Investment & Securities OpenAPI.

    Handles authentication, rate limiting, and API requests.
    """

    BASE_URL = "https://openapi.koreainvestment.com:9443"

    # API endpoints
    ENDPOINTS = {
        "domestic_price": "/uapi/domestic-stock/v1/quotations/inquire-price",
        "domestic_daily": "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        "overseas_price": "/uapi/overseas-price/v1/quotations/price",
        "overseas_daily": "/uapi/overseas-price/v1/quotations/dailyprice",
    }

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        rate_limit: int = 5,
        max_retries: int = 3,
        timeout: int = 10
    ):
        """
        Initialize KIS API client.

        Args:
            app_key: KIS API application key (defaults to KIS_APP_KEY env var)
            app_secret: KIS API secret (defaults to KIS_APP_SECRET env var)
            rate_limit: Maximum requests per second
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds

        Raises:
            ValueError: If credentials are not provided
        """
        # Get credentials from args or environment
        self.app_key = app_key or os.getenv("KIS_APP_KEY")
        self.app_secret = app_secret or os.getenv("KIS_APP_SECRET")

        if not self.app_key or not self.app_secret:
            raise ValueError(
                "KIS API credentials not provided. "
                "Set KIS_APP_KEY and KIS_APP_SECRET environment variables "
                "or pass them as arguments."
            )

        # Initialize authentication
        self.auth = KISAuth(self.app_key, self.app_secret)

        # Initialize rate limiter
        self.rate_limiter = TokenBucketRateLimiter(rate=rate_limit, per_seconds=1.0)

        # Request settings
        self.max_retries = max_retries
        self.timeout = timeout

        # Session for connection pooling
        self.session = requests.Session()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        tr_id: Optional[str] = None
    ) -> Dict:
        """
        Make HTTP request to KIS API with rate limiting and retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body
            tr_id: Transaction ID for the request

        Returns:
            API response as dictionary

        Raises:
            KISAPIError: If API returns an error
            KISNetworkError: If network error occurs
            KISRateLimitError: If rate limit is exceeded
        """
        url = f"{self.BASE_URL}{endpoint}"

        # Acquire rate limit token
        self.rate_limiter.acquire()

        # Get authentication headers
        try:
            headers = self.auth.get_auth_headers()
        except AuthenticationError as e:
            raise KISAPIError(f"Authentication failed: {e}")

        # Add transaction ID if provided
        if tr_id:
            headers["tr_id"] = tr_id

        # Add content type
        headers["content-type"] = "application/json; charset=utf-8"

        # Retry loop
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = self.session.post(
                        url,
                        headers=headers,
                        json=data,
                        timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise KISRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds.",
                        retry_after=retry_after
                    )

                # Check for success
                if response.status_code == 200:
                    return response.json()

                # Handle error responses
                try:
                    error_data = response.json()
                    error_msg = error_data.get("msg", "Unknown error")
                    error_code = error_data.get("msg_cd", "")
                    raise KISAPIError(f"[{error_code}] {error_msg}")
                except ValueError:
                    # Response is not JSON
                    raise KISAPIError(
                        f"HTTP {response.status_code}: {response.text}"
                    )

            except requests.RequestException as e:
                last_exception = KISNetworkError(f"Network error: {str(e)}")
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}). "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

        # All retries exhausted
        raise last_exception

    def get_stock_price(self, code: str, market: str = "J") -> KISStockPrice:
        """
        Get current price for a domestic stock.

        Args:
            code: Stock code (6 digits, e.g., "005930" for Samsung)
            market: Market type (J=KOSPI, Q=KOSDAQ)

        Returns:
            Stock price information

        Raises:
            KISAPIError: If API request fails
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": code
        }

        response = self._make_request(
            "GET",
            self.ENDPOINTS["domestic_price"],
            params=params,
            tr_id="FHKST01010100"
        )

        # Parse response
        output = response.get("output", {})

        return KISStockPrice(
            code=code,
            name=output.get("prdt_name", ""),
            current_price=int(output.get("stck_prpr", 0)),
            open=int(output.get("stck_oprc", 0)),
            high=int(output.get("stck_hgpr", 0)),
            low=int(output.get("stck_lwpr", 0)),
            volume=int(output.get("acml_vol", 0)),
            change=int(output.get("prdy_vrss", 0)),
            change_rate=float(output.get("prdy_ctrt", 0))
        )

    def get_daily_price(
        self,
        code: str,
        start_date: Union[str, date],
        end_date: Union[str, date],
        market: str = "J"
    ) -> List[KISDailyPrice]:
        """
        Get daily price history for a domestic stock.

        Args:
            code: Stock code
            start_date: Start date (YYYYMMDD or date object)
            end_date: End date (YYYYMMDD or date object)
            market: Market type (J=KOSPI, Q=KOSDAQ)

        Returns:
            List of daily price data

        Raises:
            KISAPIError: If API request fails
        """
        # Convert dates to strings if needed
        if isinstance(start_date, date):
            start_date = start_date.strftime("%Y%m%d")
        if isinstance(end_date, date):
            end_date = end_date.strftime("%Y%m%d")

        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D"  # Daily
        }

        response = self._make_request(
            "GET",
            self.ENDPOINTS["domestic_daily"],
            params=params,
            tr_id="FHKST01010400"
        )

        # Parse response
        output_list = response.get("output2", [])

        results = []
        for item in output_list:
            results.append(KISDailyPrice(
                code=code,
                date=item.get("stck_bsop_date", ""),
                open=int(item.get("stck_oprc", 0)),
                high=int(item.get("stck_hgpr", 0)),
                low=int(item.get("stck_lwpr", 0)),
                close=int(item.get("stck_clpr", 0)),
                volume=int(item.get("acml_vol", 0)),
                change=int(item.get("prdy_vrss", 0)) if "prdy_vrss" in item else None,
                change_rate=float(item.get("prdy_ctrt", 0)) if "prdy_ctrt" in item else None
            ))

        return results

    def get_overseas_stock(
        self,
        symbol: str,
        exchange: Union[str, KISExchange]
    ) -> KISOverseasStock:
        """
        Get current price for an overseas stock.

        Args:
            symbol: Stock symbol (e.g., "AAPL" for Apple)
            exchange: Exchange code (NASDAQ, NYSE, etc.)

        Returns:
            Overseas stock price information

        Raises:
            KISAPIError: If API request fails
        """
        # Convert exchange to enum if string
        if isinstance(exchange, str):
            exchange = KISExchange(exchange.upper())

        # Map exchange to KIS exchange code
        exchange_code_map = {
            KISExchange.NASDAQ: "NAS",
            KISExchange.NYSE: "NYS",
            KISExchange.AMEX: "AMS",
            KISExchange.HKEX: "HKS",
            KISExchange.TSE: "TYO",
            KISExchange.SSE: "SHS",
            KISExchange.SZSE: "SZS"
        }

        exchange_code = exchange_code_map.get(exchange, "NAS")

        params = {
            "AUTH": "",
            "EXCD": exchange_code,
            "SYMB": symbol
        }

        response = self._make_request(
            "GET",
            self.ENDPOINTS["overseas_price"],
            params=params,
            tr_id="HHDFS00000300"
        )

        # Parse response
        output = response.get("output", {})

        # Determine currency based on exchange
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
            name=output.get("name", symbol),
            current_price=float(output.get("last", 0)),
            open=float(output.get("open", 0)),
            high=float(output.get("high", 0)),
            low=float(output.get("low", 0)),
            volume=int(output.get("tvol", 0)),
            currency=currency_map.get(exchange, "USD"),
            change=float(output.get("diff", 0)) if "diff" in output else None,
            change_rate=float(output.get("rate", 0)) if "rate" in output else None
        )

    def get_overseas_daily(
        self,
        symbol: str,
        exchange: Union[str, KISExchange],
        period: int = 30
    ) -> List[KISOverseasDaily]:
        """
        Get daily price history for an overseas stock.

        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Number of days to retrieve (default: 30)

        Returns:
            List of daily price data

        Raises:
            KISAPIError: If API request fails
        """
        # Convert exchange to enum if string
        if isinstance(exchange, str):
            exchange = KISExchange(exchange.upper())

        # Map exchange to KIS exchange code
        exchange_code_map = {
            KISExchange.NASDAQ: "NAS",
            KISExchange.NYSE: "NYS",
            KISExchange.AMEX: "AMS",
            KISExchange.HKEX: "HKS",
            KISExchange.TSE: "TYO",
            KISExchange.SSE: "SHS",
            KISExchange.SZSE: "SZS"
        }

        exchange_code = exchange_code_map.get(exchange, "NAS")

        params = {
            "AUTH": "",
            "EXCD": exchange_code,
            "SYMB": symbol,
            "GUBN": "0",  # Daily
            "BYMD": "",   # Empty for recent data
            "MODP": "1"   # Adjusted price
        }

        response = self._make_request(
            "GET",
            self.ENDPOINTS["overseas_daily"],
            params=params,
            tr_id="HHDFS76240000"
        )

        # Parse response
        output_list = response.get("output2", [])

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
        currency = currency_map.get(exchange, "USD")

        results = []
        for item in output_list[:period]:  # Limit to requested period
            results.append(KISOverseasDaily(
                symbol=symbol,
                exchange=exchange,
                date=item.get("xymd", ""),
                open=float(item.get("open", 0)),
                high=float(item.get("high", 0)),
                low=float(item.get("low", 0)),
                close=float(item.get("clos", 0)),
                volume=int(item.get("tvol", 0)),
                currency=currency
            ))

        return results

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
