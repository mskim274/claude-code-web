"""
Integration tests for UnifiedAPIClient.

Tests the complete workflow of the unified API client including:
- Data source selection and fallback
- Caching behavior
- Data normalization
- Error handling
"""
import pytest
from datetime import datetime
import time

from collectors.apis.unified import UnifiedAPIClient, DataSource, APIError
from collectors.apis.cache import APICache
from tests.fixtures.mock_apis import MockKiwoomAPI, MockKISAPI, MockDARTAPI


class TestUnifiedAPIClientInitialization:
    """Test UnifiedAPIClient initialization"""

    def test_init_with_all_apis(self):
        """Test initialization with all APIs"""
        kiwoom = MockKiwoomAPI()
        kis = MockKISAPI()
        dart = MockDARTAPI()

        client = UnifiedAPIClient(
            kiwoom_api=kiwoom,
            kis_api=kis,
            dart_api=dart
        )

        assert client.kiwoom is not None
        assert client.kis is not None
        assert client.dart is not None
        assert client.cache is not None
        assert client.enable_cache is True

    def test_init_without_cache(self):
        """Test initialization with caching disabled"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(),
            enable_cache=False
        )

        assert client.cache is None
        assert client.enable_cache is False

    def test_init_with_custom_ttl(self):
        """Test initialization with custom cache TTL"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(),
            cache_ttl=300
        )

        assert client.cache.ttl_seconds == 300


class TestStockPriceRetrieval:
    """Test stock price retrieval from different sources"""

    def test_get_stock_price_from_kis(self):
        """Test getting stock price from KIS"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI()
        )

        result = client.get_stock_price("005930", source=DataSource.KIS)

        assert result["code"] == "005930"
        assert result["source"] == "kis"
        assert "current_price" in result
        assert "open_price" in result
        assert isinstance(result["current_price"], int)
        assert isinstance(result["volume"], int)

    def test_get_stock_price_from_kiwoom(self):
        """Test getting stock price from Kiwoom"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI()
        )

        result = client.get_stock_price("005930", source=DataSource.KIWOOM)

        assert result["code"] == "005930"
        assert result["source"] == "kiwoom"
        assert result["name"] == "삼성전자"
        assert "current_price" in result
        assert isinstance(result["current_price"], int)

    def test_get_stock_price_auto_fallback_kis_to_kiwoom(self):
        """Test automatic fallback from KIS to Kiwoom when KIS fails"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(fail=False),
            kis_api=MockKISAPI(fail=True)
        )

        result = client.get_stock_price("005930", source=DataSource.AUTO)

        # Should fallback to Kiwoom
        assert result["source"] == "kiwoom"
        assert result["code"] == "005930"

    def test_get_stock_price_auto_prefers_kis(self):
        """Test AUTO mode prefers KIS when available"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(),
            kis_api=MockKISAPI()
        )

        result = client.get_stock_price("005930", source=DataSource.AUTO)

        # Should prefer KIS
        assert result["source"] == "kis"

    def test_get_stock_price_all_sources_fail(self):
        """Test error when all sources fail"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(fail=True),
            kis_api=MockKISAPI(fail=True)
        )

        with pytest.raises(APIError) as exc_info:
            client.get_stock_price("005930", source=DataSource.AUTO)

        assert "All sources failed" in str(exc_info.value)

    def test_get_stock_price_kis_only_fails(self):
        """Test error when only KIS is requested but fails"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(fail=True)
        )

        with pytest.raises(APIError) as exc_info:
            client.get_stock_price("005930", source=DataSource.KIS)

        assert "KIS failed" in str(exc_info.value)


class TestCachingBehavior:
    """Test caching behavior"""

    def test_cache_hit_reduces_api_calls(self):
        """Test cache hit reduces actual API calls"""
        kis = MockKISAPI()
        client = UnifiedAPIClient(kis_api=kis, cache_ttl=60)

        # First call - cache miss
        result1 = client.get_stock_price("005930", source=DataSource.KIS)
        assert kis.get_call_count() == 1

        # Second call - cache hit
        result2 = client.get_stock_price("005930", source=DataSource.KIS)
        assert kis.get_call_count() == 1  # No additional API call

        # Results should be identical
        assert result1 == result2

    def test_cache_stats(self):
        """Test cache statistics tracking"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        # Make some calls
        client.get_stock_price("005930", source=DataSource.KIS)
        client.get_stock_price("005930", source=DataSource.KIS)  # Cache hit
        client.get_stock_price("000660", source=DataSource.KIS)

        stats = client.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["sets"] == 2

    def test_cache_disabled(self):
        """Test behavior when caching is disabled"""
        kis = MockKISAPI()
        client = UnifiedAPIClient(kis_api=kis, enable_cache=False)

        # Multiple calls should all hit API
        client.get_stock_price("005930", source=DataSource.KIS)
        client.get_stock_price("005930", source=DataSource.KIS)

        assert kis.get_call_count() == 2

    def test_clear_cache(self):
        """Test clearing cache"""
        kis = MockKISAPI()
        client = UnifiedAPIClient(kis_api=kis)

        # First call
        client.get_stock_price("005930", source=DataSource.KIS)
        assert kis.get_call_count() == 1

        # Clear cache
        client.clear_cache()

        # Next call should hit API again
        client.get_stock_price("005930", source=DataSource.KIS)
        assert kis.get_call_count() == 2


class TestOverseasStock:
    """Test overseas stock functionality"""

    def test_get_overseas_stock_success(self):
        """Test getting overseas stock price"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        result = client.get_overseas_stock("AAPL", "NASDAQ")

        assert result["symbol"] == "AAPL"
        assert result["exchange"] == "NASDAQ"
        assert result["source"] == "kis"
        assert "current_price" in result
        assert isinstance(result["current_price"], float)

    def test_get_overseas_stock_without_kis(self):
        """Test error when KIS API not available"""
        client = UnifiedAPIClient(kiwoom_api=MockKiwoomAPI())

        with pytest.raises(APIError) as exc_info:
            client.get_overseas_stock("AAPL", "NASDAQ")

        assert "KIS API not initialized" in str(exc_info.value)

    def test_get_overseas_stock_cached(self):
        """Test overseas stock caching"""
        kis = MockKISAPI()
        client = UnifiedAPIClient(kis_api=kis)

        # First call
        result1 = client.get_overseas_stock("AAPL", "NASDAQ")
        assert kis.get_call_count() == 1

        # Second call - should be cached
        result2 = client.get_overseas_stock("AAPL", "NASDAQ")
        assert kis.get_call_count() == 1

        assert result1 == result2


class TestFinancialData:
    """Test financial data retrieval"""

    def test_get_financial_data_success(self):
        """Test getting financial statement data"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI())

        result = client.get_financial_data("005930", 2023, 4)

        assert result["year"] == 2023
        assert result["quarter"] == 4
        assert result["source"] == "dart"
        assert "total_assets" in result
        assert "revenue" in result
        assert "net_income" in result
        assert isinstance(result["total_assets"], int)

    def test_get_financial_data_without_dart(self):
        """Test error when DART API not available"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        with pytest.raises(APIError) as exc_info:
            client.get_financial_data("005930", 2023, 4)

        assert "DART API not initialized" in str(exc_info.value)

    def test_get_financial_data_cached(self):
        """Test financial data caching"""
        dart = MockDARTAPI()
        client = UnifiedAPIClient(dart_api=dart)

        # First call
        result1 = client.get_financial_data("005930", 2023, 4)
        assert dart.get_call_count() == 1

        # Second call - should be cached
        result2 = client.get_financial_data("005930", 2023, 4)
        assert dart.get_call_count() == 1

        assert result1 == result2


class TestComprehensiveData:
    """Test comprehensive data retrieval"""

    def test_get_comprehensive_data_success(self):
        """Test getting comprehensive data (price + financial + metrics)"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        result = client.get_comprehensive_data("005930", year=2023, quarter=4)

        assert "price" in result
        assert "financial" in result
        assert "metrics" in result

        # Check price data
        assert result["price"] is not None
        assert result["price"]["code"] == "005930"

        # Check financial data
        assert result["financial"] is not None
        assert result["financial"]["year"] == 2023

        # Check metrics
        metrics = result["metrics"]
        assert "roe" in metrics
        assert "debt_ratio" in metrics
        assert "operating_margin" in metrics

    def test_get_comprehensive_data_partial_failure(self):
        """Test comprehensive data when one source fails"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI(fail=True)
        )

        result = client.get_comprehensive_data("005930", year=2023)

        # Price should succeed
        assert result["price"] is not None

        # Financial should fail gracefully
        assert result["financial"] is None

        # Metrics should be empty
        assert result["metrics"] == {}


class TestCallCounting:
    """Test API call counting"""

    def test_call_count_tracking(self):
        """Test tracking of API calls to each source"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(),
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI(),
            enable_cache=False  # Disable cache to count all calls
        )

        # Make various calls
        client.get_stock_price("005930", source=DataSource.KIS)
        client.get_stock_price("000660", source=DataSource.KIWOOM)
        client.get_overseas_stock("AAPL", "NASDAQ")
        client.get_financial_data("005930", 2023, 4)

        counts = client.get_call_counts()
        assert counts["kis"] == 2  # stock price + overseas
        assert counts["kiwoom"] == 1
        assert counts["dart"] == 1

    def test_reset_call_counts(self):
        """Test resetting call counts"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        client.get_stock_price("005930", source=DataSource.KIS)
        assert client.get_call_counts()["kis"] == 1

        client.reset_call_counts()
        assert client.get_call_counts()["kis"] == 0


class TestDataNormalization:
    """Test data format normalization across sources"""

    def test_normalized_price_format_kis_vs_kiwoom(self):
        """Test that KIS and Kiwoom data are normalized to same format"""
        client = UnifiedAPIClient(
            kiwoom_api=MockKiwoomAPI(),
            kis_api=MockKISAPI()
        )

        kis_result = client.get_stock_price("005930", source=DataSource.KIS)
        kiwoom_result = client.get_stock_price("005930", source=DataSource.KIWOOM)

        # Both should have same fields
        assert set(kis_result.keys()) == set(kiwoom_result.keys())

        # Check field types
        for key in ["current_price", "open_price", "high_price", "low_price", "volume"]:
            assert isinstance(kis_result[key], int)
            assert isinstance(kiwoom_result[key], int)

        assert isinstance(kis_result["change_rate"], float)
        assert isinstance(kiwoom_result["change_rate"], float)
