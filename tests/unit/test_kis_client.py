"""
Unit tests for KIS API client.

TDD Red Phase: Write failing tests first.
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
import requests

# Import will fail initially - this is expected in TDD Red phase
try:
    from collectors.apis.kis.client import (
        KISClient,
        KISAPIError,
        KISNetworkError,
        KISRateLimitError
    )
    from collectors.apis.kis.schemas import KISStockPrice, KISOverseasStock, KISExchange
except ImportError:
    pytest.skip("KIS client not implemented yet", allow_module_level=True)


class TestKISClientInitialization:
    """Test KIS client initialization."""

    def test_init_with_credentials(self):
        """Test initialization with explicit credentials."""
        client = KISClient(app_key="test_key", app_secret="test_secret")

        assert client.app_key == "test_key"
        assert client.app_secret == "test_secret"
        assert client.auth is not None

    def test_init_with_env_variables(self):
        """Test initialization with environment variables."""
        with patch.dict('os.environ', {
            'KIS_APP_KEY': 'env_key',
            'KIS_APP_SECRET': 'env_secret'
        }):
            client = KISClient()

            assert client.app_key == "env_key"
            assert client.app_secret == "env_secret"

    def test_init_without_credentials_raises_error(self):
        """Test that missing credentials raise error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="KIS API credentials not provided"):
                KISClient()

    def test_init_with_custom_rate_limit(self):
        """Test initialization with custom rate limit."""
        client = KISClient(
            app_key="test_key",
            app_secret="test_secret",
            rate_limit=10
        )

        assert client.rate_limiter.rate == 10


class TestGetStockPrice:
    """Test get_stock_price method."""

    @patch('requests.get')
    def test_get_stock_price_success(self, mock_get):
        """Test successful stock price retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "stck_prpr": "70000",      # Current price
                "stck_oprc": "69000",      # Open
                "stck_hgpr": "71000",      # High
                "stck_lwpr": "68500",      # Low
                "acml_vol": "10000000",    # Volume
                "prdy_vrss": "1000",       # Change
                "prdy_ctrt": "1.45"        # Change rate
            }
        }
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            result = client.get_stock_price("005930")

        assert isinstance(result, KISStockPrice)
        assert result.code == "005930"
        assert result.current_price == 70000
        assert result.volume == 10000000

    @patch('requests.get')
    def test_get_stock_price_with_invalid_code(self, mock_get):
        """Test stock price retrieval with invalid code."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "msg_cd": "EGW00123",
            "msg": "Invalid stock code"
        }
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            with pytest.raises(KISAPIError, match="Invalid stock code"):
                client.get_stock_price("INVALID")

    @patch('requests.get')
    def test_get_stock_price_with_network_error(self, mock_get):
        """Test stock price retrieval with network error."""
        mock_get.side_effect = requests.RequestException("Connection timeout")

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            with pytest.raises(KISNetworkError, match="Connection timeout"):
                client.get_stock_price("005930")

    @patch('requests.get')
    def test_get_stock_price_with_rate_limit_error(self, mock_get):
        """Test stock price retrieval with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            with pytest.raises(KISRateLimitError) as exc_info:
                client.get_stock_price("005930")

            assert exc_info.value.retry_after == 60


class TestGetDailyPrice:
    """Test get_daily_price method."""

    @patch('requests.get')
    def test_get_daily_price_success(self, mock_get):
        """Test successful daily price retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output2": [
                {
                    "stck_bsop_date": "20240115",
                    "stck_oprc": "69000",
                    "stck_hgpr": "71000",
                    "stck_lwpr": "68500",
                    "stck_clpr": "70000",
                    "acml_vol": "15000000",
                    "prdy_vrss": "1000",
                    "prdy_ctrt": "1.45"
                },
                {
                    "stck_bsop_date": "20240112",
                    "stck_oprc": "68000",
                    "stck_hgpr": "69500",
                    "stck_lwpr": "67500",
                    "stck_clpr": "69000",
                    "acml_vol": "12000000"
                }
            ]
        }
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            results = client.get_daily_price("005930", start_date="20240112", end_date="20240115")

        assert len(results) == 2
        assert results[0].close == 70000
        assert results[1].close == 69000

    @patch('requests.get')
    def test_get_daily_price_with_date_objects(self, mock_get):
        """Test daily price with date objects instead of strings."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output2": []}
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            client.get_daily_price(
                "005930",
                start_date=date(2024, 1, 12),
                end_date=date(2024, 1, 15)
            )

        # Verify dates were converted to strings in API call
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert params['FID_INPUT_DATE_1'] == "20240112"
        assert params['FID_INPUT_DATE_2'] == "20240115"


class TestGetOverseasStock:
    """Test get_overseas_stock method."""

    @patch('requests.get')
    def test_get_overseas_stock_nasdaq_success(self, mock_get):
        """Test successful overseas stock retrieval (NASDAQ)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "last": "175.50",
                "open": "174.00",
                "high": "176.00",
                "low": "173.50",
                "tvol": "50000000",
                "diff": "1.50",
                "rate": "0.86"
            }
        }
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            result = client.get_overseas_stock("AAPL", KISExchange.NASDAQ)

        assert isinstance(result, KISOverseasStock)
        assert result.symbol == "AAPL"
        assert result.exchange == KISExchange.NASDAQ
        assert result.current_price == 175.50
        assert result.currency == "USD"

    @patch('requests.get')
    def test_get_overseas_stock_with_string_exchange(self, mock_get):
        """Test overseas stock with string exchange parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "last": "175.50",
                "open": "174.00",
                "high": "176.00",
                "low": "173.50",
                "tvol": "50000000"
            }
        }
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            result = client.get_overseas_stock("AAPL", "NASDAQ")

        assert result.exchange == KISExchange.NASDAQ


class TestGetOverseasDaily:
    """Test get_overseas_daily method."""

    @patch('requests.get')
    def test_get_overseas_daily_success(self, mock_get):
        """Test successful overseas daily price retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output2": [
                {
                    "xymd": "20240115",
                    "open": "174.00",
                    "high": "176.00",
                    "low": "173.50",
                    "clos": "175.50",
                    "tvol": "50000000"
                },
                {
                    "xymd": "20240112",
                    "open": "172.00",
                    "high": "174.50",
                    "low": "171.00",
                    "clos": "174.00",
                    "tvol": "45000000"
                }
            ]
        }
        mock_get.return_value = mock_response

        client = KISClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            results = client.get_overseas_daily("AAPL", KISExchange.NASDAQ)

        assert len(results) == 2
        assert results[0].close == 175.50
        assert results[1].close == 174.00


class TestRetryLogic:
    """Test retry logic for failed requests."""

    @patch('requests.get')
    def test_retry_on_temporary_failure(self, mock_get):
        """Test that temporary failures are retried."""
        # First call fails, second succeeds
        mock_get.side_effect = [
            requests.RequestException("Temporary error"),
            Mock(status_code=200, json=lambda: {"output": {}})
        ]

        client = KISClient(app_key="test_key", app_secret="test_secret", max_retries=2)

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            # Should succeed on retry
            client.get_stock_price("005930")

        assert mock_get.call_count == 2

    @patch('requests.get')
    def test_max_retries_exceeded(self, mock_get):
        """Test that max retries is respected."""
        mock_get.side_effect = requests.RequestException("Persistent error")

        client = KISClient(app_key="test_key", app_secret="test_secret", max_retries=3)

        with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
            with pytest.raises(KISNetworkError):
                client.get_stock_price("005930")

        assert mock_get.call_count == 3


class TestRateLimiterIntegration:
    """Test rate limiter integration with client."""

    def test_rate_limiter_enforced_on_requests(self):
        """Test that rate limiter is enforced on API requests."""
        client = KISClient(
            app_key="test_key",
            app_secret="test_secret",
            rate_limit=2  # Very low limit for testing
        )

        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(status_code=200, json=lambda: {"output": {}})

            with patch.object(client.auth, 'get_access_token', return_value="mock_token"):
                import time
                start = time.time()

                # Make 3 requests (should block on 3rd)
                for _ in range(3):
                    client.get_stock_price("005930")

                elapsed = time.time() - start

                # Should have been rate limited
                assert elapsed >= 0.4  # Allow tolerance
