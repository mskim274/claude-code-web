"""
Unit tests for KIS API OAuth 2.0 authentication.

TDD Red Phase: Write failing tests first.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# Import will fail initially - this is expected in TDD Red phase
try:
    from collectors.apis.kis.auth import KISAuth, TokenExpiredError, AuthenticationError
except ImportError:
    pytest.skip("KISAuth not implemented yet", allow_module_level=True)


class TestKISAuthInitialization:
    """Test KISAuth initialization."""

    def test_init_with_valid_credentials(self):
        """Test initialization with valid app_key and app_secret."""
        auth = KISAuth(app_key="test_key", app_secret="test_secret")

        assert auth.app_key == "test_key"
        assert auth.app_secret == "test_secret"
        assert auth.access_token is None
        assert auth.token_expires_at is None

    def test_init_with_empty_app_key_raises_error(self):
        """Test that empty app_key raises ValueError."""
        with pytest.raises(ValueError, match="app_key cannot be empty"):
            KISAuth(app_key="", app_secret="test_secret")

    def test_init_with_empty_app_secret_raises_error(self):
        """Test that empty app_secret raises ValueError."""
        with pytest.raises(ValueError, match="app_secret cannot be empty"):
            KISAuth(app_key="test_key", app_secret="")


class TestTokenValidation:
    """Test token validation logic."""

    def test_is_token_valid_when_no_token(self):
        """Test token validation when no token exists."""
        auth = KISAuth(app_key="test_key", app_secret="test_secret")

        assert auth._is_token_valid() is False

    def test_is_token_valid_when_token_expired(self):
        """Test token validation when token is expired."""
        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.access_token = "expired_token"
        auth.token_expires_at = datetime.now() - timedelta(hours=1)

        assert auth._is_token_valid() is False

    def test_is_token_valid_when_token_about_to_expire(self):
        """Test token validation when token expires in less than 5 minutes."""
        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.access_token = "about_to_expire_token"
        auth.token_expires_at = datetime.now() + timedelta(minutes=3)

        # Token should be considered invalid to trigger refresh
        assert auth._is_token_valid() is False

    def test_is_token_valid_when_token_is_valid(self):
        """Test token validation when token is valid."""
        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        assert auth._is_token_valid() is True


class TestTokenRefresh:
    """Test token refresh functionality."""

    @patch('requests.post')
    def test_refresh_token_success(self, mock_post):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "token_type": "Bearer",
            "expires_in": 86400  # 24 hours
        }
        mock_post.return_value = mock_response

        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        token = auth._refresh_token()

        assert token == "new_access_token"
        assert auth.access_token == "new_access_token"
        assert auth.token_expires_at is not None

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "oauth2/tokenP" in call_args[0][0]

    @patch('requests.post')
    def test_refresh_token_with_invalid_response(self, mock_post):
        """Test token refresh with invalid response."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid credentials"
        }
        mock_post.return_value = mock_response

        auth = KISAuth(app_key="test_key", app_secret="test_secret")

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth._refresh_token()

    @patch('requests.post')
    def test_refresh_token_with_network_error(self, mock_post):
        """Test token refresh with network error."""
        mock_post.side_effect = Exception("Network error")

        auth = KISAuth(app_key="test_key", app_secret="test_secret")

        with pytest.raises(AuthenticationError, match="Network error"):
            auth._refresh_token()


class TestGetAccessToken:
    """Test get_access_token method."""

    def test_get_access_token_returns_existing_valid_token(self):
        """Test that existing valid token is returned without refresh."""
        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.access_token = "valid_token"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        with patch.object(auth, '_refresh_token') as mock_refresh:
            token = auth.get_access_token()

            assert token == "valid_token"
            mock_refresh.assert_not_called()

    @patch('requests.post')
    def test_get_access_token_refreshes_expired_token(self, mock_post):
        """Test that expired token triggers refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed_token",
            "token_type": "Bearer",
            "expires_in": 86400
        }
        mock_post.return_value = mock_response

        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.access_token = "expired_token"
        auth.token_expires_at = datetime.now() - timedelta(hours=1)

        token = auth.get_access_token()

        assert token == "refreshed_token"
        assert auth.access_token == "refreshed_token"

    @patch('requests.post')
    def test_get_access_token_when_no_token_exists(self, mock_post):
        """Test token acquisition when no token exists."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "token_type": "Bearer",
            "expires_in": 86400
        }
        mock_post.return_value = mock_response

        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        token = auth.get_access_token()

        assert token == "new_token"
        assert auth.access_token == "new_token"


class TestTokenPersistence:
    """Test token persistence (save/load from file)."""

    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_save_token_to_file(self, mock_exists, mock_open):
        """Test saving token to file."""
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.access_token = "token_to_save"
        auth.token_expires_at = datetime.now() + timedelta(hours=1)

        auth.save_token()

        mock_open.assert_called_once()
        mock_file.write.assert_called_once()

    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_load_token_from_file(self, mock_exists, mock_open):
        """Test loading token from file."""
        token_data = {
            "access_token": "saved_token",
            "token_expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }

        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(token_data)
        mock_open.return_value.__enter__.return_value = mock_file

        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.load_token()

        assert auth.access_token == "saved_token"
        assert auth.token_expires_at is not None

    @patch('os.path.exists')
    def test_load_token_when_file_not_exists(self, mock_exists):
        """Test loading token when file doesn't exist."""
        mock_exists.return_value = False

        auth = KISAuth(app_key="test_key", app_secret="test_secret")
        auth.load_token()

        # Should not raise error, token should remain None
        assert auth.access_token is None
        assert auth.token_expires_at is None
