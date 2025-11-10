"""
Unified API Client for integrating Kiwoom, KIS, and DART APIs.

This module provides a single interface for accessing multiple data sources
with automatic fallback, caching, and data normalization.
"""
from typing import Optional, Dict, List, Any, Union
from enum import Enum
from datetime import datetime
import logging

from .cache import APICache, cache_response


logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source enumeration"""
    KIWOOM = "kiwoom"
    KIS = "kis"
    DART = "dart"
    AUTO = "auto"  # Automatic selection with fallback


class APIError(Exception):
    """Base exception for API errors"""
    pass


class UnifiedAPIClient:
    """
    Unified API client integrating Kiwoom, KIS, and DART APIs.

    Features:
    - Single interface for multiple data sources
    - Automatic fallback when primary source fails
    - Response caching to reduce API calls
    - Data normalization to unified format
    - Comprehensive error handling
    """

    def __init__(
        self,
        kiwoom_api=None,
        kis_api=None,
        dart_api=None,
        cache_ttl: int = 60,
        enable_cache: bool = True
    ):
        """
        Initialize unified API client

        Args:
            kiwoom_api: Kiwoom API instance
            kis_api: KIS API instance
            dart_api: DART API instance
            cache_ttl: Cache TTL in seconds
            enable_cache: Enable response caching
        """
        self.kiwoom = kiwoom_api
        self.kis = kis_api
        self.dart = dart_api

        self.enable_cache = enable_cache
        self.cache = APICache(ttl_seconds=cache_ttl) if enable_cache else None

        self._call_counts = {
            "kiwoom": 0,
            "kis": 0,
            "dart": 0,
        }

    def get_stock_price(
        self,
        code: str,
        source: DataSource = DataSource.AUTO
    ) -> Dict[str, Any]:
        """
        Get domestic stock price with unified format

        Args:
            code: Stock code (e.g., "005930")
            source: Data source (kiwoom, kis, auto)

        Returns:
            Unified stock price data:
            {
                'code': str,
                'name': str,
                'current_price': int,
                'open_price': int,
                'high_price': int,
                'low_price': int,
                'volume': int,
                'change_rate': float,
                'change_price': int,
                'timestamp': str,
                'source': str
            }

        Raises:
            APIError: If all sources fail
        """
        # Check cache first
        if self.enable_cache:
            cache_key = APICache.make_key("get_stock_price", code=code)
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for stock price: {code}")
                return cached

        result = None
        errors = []

        if source == DataSource.AUTO:
            # Try KIS first, then Kiwoom
            try:
                result = self._get_stock_price_kis(code)
            except Exception as e:
                errors.append(f"KIS failed: {e}")
                logger.warning(f"KIS API failed for {code}, trying Kiwoom: {e}")
                try:
                    result = self._get_stock_price_kiwoom(code)
                except Exception as e2:
                    errors.append(f"Kiwoom failed: {e2}")
                    logger.error(f"Both KIS and Kiwoom failed for {code}")

        elif source == DataSource.KIS:
            try:
                result = self._get_stock_price_kis(code)
            except Exception as e:
                errors.append(f"KIS failed: {e}")
                logger.error(f"KIS API failed for {code}: {e}")

        elif source == DataSource.KIWOOM:
            try:
                result = self._get_stock_price_kiwoom(code)
            except Exception as e:
                errors.append(f"Kiwoom failed: {e}")
                logger.error(f"Kiwoom API failed for {code}: {e}")

        if result is None:
            error_msg = f"All sources failed for {code}: {'; '.join(errors)}"
            raise APIError(error_msg)

        # Cache the result
        if self.enable_cache:
            self.cache.set(cache_key, result)

        return result

    def _get_stock_price_kiwoom(self, code: str) -> Dict[str, Any]:
        """Get stock price from Kiwoom API"""
        if self.kiwoom is None:
            raise APIError("Kiwoom API not initialized")

        self._call_counts["kiwoom"] += 1
        data = self.kiwoom.get_stock_price(code)

        # Normalize to unified format
        return {
            "code": data["code"],
            "name": data.get("name", ""),
            "current_price": int(data["current_price"]),
            "open_price": int(data["open_price"]),
            "high_price": int(data["high_price"]),
            "low_price": int(data["low_price"]),
            "volume": int(data["volume"]),
            "change_rate": float(data["change_rate"]),
            "change_price": int(data["change_price"]),
            "timestamp": data["timestamp"],
            "source": "kiwoom",
        }

    def _get_stock_price_kis(self, code: str) -> Dict[str, Any]:
        """Get stock price from KIS API"""
        if self.kis is None:
            raise APIError("KIS API not initialized")

        self._call_counts["kis"] += 1
        response = self.kis.get_stock_price(code)

        if response.get("rt_cd") != "0":
            raise APIError(f"KIS API error: {response.get('msg1')}")

        output = response["output"]

        # Normalize to unified format
        return {
            "code": code,
            "name": "",  # KIS doesn't provide name in price API
            "current_price": int(output["stck_prpr"]),
            "open_price": int(output["stck_oprc"]),
            "high_price": int(output["stck_hgpr"]),
            "low_price": int(output["stck_lwpr"]),
            "volume": int(output["acml_vol"]),
            "change_rate": float(output["prdy_ctrt"]),
            "change_price": int(output["prdy_vrss"]),
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
            "source": "kis",
        }

    def get_overseas_stock(
        self,
        symbol: str,
        exchange: str = "NASDAQ"
    ) -> Dict[str, Any]:
        """
        Get overseas stock price (KIS only)

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            exchange: Exchange code (NASDAQ, NYSE, etc.)

        Returns:
            Unified overseas stock price data:
            {
                'symbol': str,
                'exchange': str,
                'current_price': float,
                'open_price': float,
                'high_price': float,
                'low_price': float,
                'volume': int,
                'change_rate': float,
                'timestamp': str,
                'source': str
            }

        Raises:
            APIError: If KIS API is not available or fails
        """
        if self.kis is None:
            raise APIError("KIS API not initialized (required for overseas stocks)")

        # Check cache
        if self.enable_cache:
            cache_key = APICache.make_key(
                "get_overseas_stock",
                symbol=symbol,
                exchange=exchange
            )
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for overseas stock: {symbol}")
                return cached

        self._call_counts["kis"] += 1
        response = self.kis.get_overseas_stock_price(symbol, exchange)

        if response.get("rt_cd") != "0":
            raise APIError(f"KIS API error: {response.get('msg1')}")

        output = response["output"]

        result = {
            "symbol": symbol,
            "exchange": exchange,
            "current_price": float(output["last"]),
            "open_price": float(output["open"]),
            "high_price": float(output["high"]),
            "low_price": float(output["low"]),
            "volume": int(output["tvol"]),
            "change_rate": float(output["rate"]),
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
            "source": "kis",
        }

        # Cache the result
        if self.enable_cache:
            self.cache.set(cache_key, result)

        return result

    def get_financial_data(
        self,
        stock_code: str,
        year: int,
        quarter: int = 4
    ) -> Dict[str, Any]:
        """
        Get financial statement data (DART)

        Args:
            stock_code: Stock code
            year: Year
            quarter: Quarter (1-4)

        Returns:
            Unified financial data:
            {
                'corp_code': str,
                'year': int,
                'quarter': int,
                'total_assets': int,
                'total_liabilities': int,
                'total_equity': int,
                'revenue': int,
                'operating_profit': int,
                'net_income': int,
                'source': str
            }

        Raises:
            APIError: If DART API is not available or fails
        """
        if self.dart is None:
            raise APIError("DART API not initialized")

        # Check cache
        if self.enable_cache:
            cache_key = APICache.make_key(
                "get_financial_data",
                stock_code=stock_code,
                year=year,
                quarter=quarter
            )
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for financial data: {stock_code}")
                return cached

        # Convert stock code to corp code (simplified - may need mapping)
        corp_code = stock_code

        self._call_counts["dart"] += 1
        response = self.dart.get_financial_statement(corp_code, year, quarter)

        if response.get("status") != "000":
            raise APIError(f"DART API error: {response.get('message')}")

        # Parse financial data
        financial_data = {
            "corp_code": corp_code,
            "year": year,
            "quarter": quarter,
            "total_assets": 0,
            "total_liabilities": 0,
            "total_equity": 0,
            "revenue": 0,
            "operating_profit": 0,
            "net_income": 0,
            "source": "dart",
        }

        for item in response.get("list", []):
            account_name = item.get("account_nm", "")
            amount = int(item.get("thstrm_amount", "0"))

            if "자산총계" in account_name:
                financial_data["total_assets"] = amount
            elif "부채총계" in account_name:
                financial_data["total_liabilities"] = amount
            elif "자본총계" in account_name:
                financial_data["total_equity"] = amount
            elif "매출액" in account_name:
                financial_data["revenue"] = amount
            elif "영업이익" in account_name:
                financial_data["operating_profit"] = amount
            elif "당기순이익" in account_name:
                financial_data["net_income"] = amount

        # Cache the result
        if self.enable_cache:
            self.cache.set(cache_key, financial_data)

        return financial_data

    def get_comprehensive_data(
        self,
        stock_code: str,
        year: Optional[int] = None,
        quarter: int = 4
    ) -> Dict[str, Any]:
        """
        Get comprehensive data (price + financial + metrics)

        Args:
            stock_code: Stock code
            year: Year for financial data (default: current year)
            quarter: Quarter for financial data

        Returns:
            Comprehensive data:
            {
                'price': {...},  # Current price data
                'financial': {...},  # Financial statement
                'metrics': {  # Calculated metrics
                    'per': float,  # Price to Earnings Ratio
                    'pbr': float,  # Price to Book Ratio
                    'roe': float,  # Return on Equity
                    'debt_ratio': float,
                    'operating_margin': float,
                }
            }
        """
        if year is None:
            year = datetime.now().year - 1  # Use last year by default

        # Get price data
        try:
            price_data = self.get_stock_price(stock_code)
        except Exception as e:
            logger.error(f"Failed to get price data for {stock_code}: {e}")
            price_data = None

        # Get financial data
        try:
            financial_data = self.get_financial_data(stock_code, year, quarter)
        except Exception as e:
            logger.error(f"Failed to get financial data for {stock_code}: {e}")
            financial_data = None

        # Calculate metrics
        metrics = {}
        if price_data and financial_data:
            try:
                # PER = Price / EPS (Earnings Per Share)
                # Simplified: using market cap / net income
                if financial_data["net_income"] > 0:
                    # Rough estimation - need actual shares outstanding
                    metrics["per"] = round(
                        price_data["current_price"] * 1000000 /
                        financial_data["net_income"],
                        2
                    )

                # PBR = Price / BPS (Book Value Per Share)
                if financial_data["total_equity"] > 0:
                    metrics["pbr"] = round(
                        price_data["current_price"] * 1000000 /
                        financial_data["total_equity"],
                        2
                    )

                # ROE = Net Income / Equity
                if financial_data["total_equity"] > 0:
                    metrics["roe"] = round(
                        financial_data["net_income"] /
                        financial_data["total_equity"] * 100,
                        2
                    )

                # Debt Ratio = Liabilities / Equity
                if financial_data["total_equity"] > 0:
                    metrics["debt_ratio"] = round(
                        financial_data["total_liabilities"] /
                        financial_data["total_equity"] * 100,
                        2
                    )

                # Operating Margin = Operating Profit / Revenue
                if financial_data["revenue"] > 0:
                    metrics["operating_margin"] = round(
                        financial_data["operating_profit"] /
                        financial_data["revenue"] * 100,
                        2
                    )
            except Exception as e:
                logger.error(f"Failed to calculate metrics: {e}")

        return {
            "price": price_data,
            "financial": financial_data,
            "metrics": metrics,
        }

    def get_call_counts(self) -> Dict[str, int]:
        """Get API call counts for each source"""
        return self._call_counts.copy()

    def reset_call_counts(self) -> None:
        """Reset API call counts"""
        self._call_counts = {
            "kiwoom": 0,
            "kis": 0,
            "dart": 0,
        }

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """Clear all cached data"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")
