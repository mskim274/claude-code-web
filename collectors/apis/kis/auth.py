"""
KIS API OAuth 2.0 Authentication Manager.

Handles token acquisition, validation, refresh, and persistence.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path


class TokenExpiredError(Exception):
    """Raised when access token has expired."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class KISAuth:
    """KIS API OAuth 2.0 authentication manager."""

    BASE_URL = "https://openapi.koreainvestment.com:9443"
    TOKEN_ENDPOINT = "/oauth2/tokenP"
    TOKEN_BUFFER_MINUTES = 5  # Refresh token 5 minutes before expiry

    def __init__(self, app_key: str, app_secret: str, token_file: Optional[str] = None):
        """
        Initialize KIS authentication manager.

        Args:
            app_key: KIS API application key
            app_secret: KIS API application secret
            token_file: Optional path to token cache file

        Raises:
            ValueError: If app_key or app_secret is empty
        """
        if not app_key:
            raise ValueError("app_key cannot be empty")
        if not app_secret:
            raise ValueError("app_secret cannot be empty")

        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Set token file path
        if token_file:
            self.token_file = Path(token_file)
        else:
            cache_dir = Path(__file__).parent / ".cache"
            cache_dir.mkdir(exist_ok=True)
            self.token_file = cache_dir / "kis_token.json"

        # Try to load existing token
        self.load_token()

    def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            AuthenticationError: If token acquisition fails
        """
        if self._is_token_valid():
            return self.access_token

        return self._refresh_token()

    def _is_token_valid(self) -> bool:
        """
        Check if current token is valid.

        Returns:
            True if token exists and hasn't expired (with buffer)
        """
        if not self.access_token or not self.token_expires_at:
            return False

        # Check if token expires within buffer time
        buffer_time = datetime.now() + timedelta(minutes=self.TOKEN_BUFFER_MINUTES)
        return self.token_expires_at > buffer_time

    def _refresh_token(self) -> str:
        """
        Refresh OAuth access token.

        Returns:
            New access token

        Raises:
            AuthenticationError: If token refresh fails
        """
        url = f"{self.BASE_URL}{self.TOKEN_ENDPOINT}"

        headers = {
            "content-type": "application/json; charset=utf-8"
        }

        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]

                # Calculate expiration time
                expires_in = data.get("expires_in", 86400)  # Default 24 hours
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                # Save token to file
                self.save_token()

                return self.access_token

            else:
                # Handle error response
                error_data = response.json()
                error_msg = error_data.get("error_description", "Unknown error")
                raise AuthenticationError(f"Invalid credentials: {error_msg}")

        except requests.RequestException as e:
            raise AuthenticationError(f"Network error: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def save_token(self) -> None:
        """Save current token to file for persistence."""
        if not self.access_token or not self.token_expires_at:
            return

        token_data = {
            "access_token": self.access_token,
            "token_expires_at": self.token_expires_at.isoformat()
        }

        try:
            # Ensure directory exists
            self.token_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=2)

        except Exception as e:
            # Log error but don't raise - token persistence is optional
            print(f"Warning: Failed to save token: {e}")

    def load_token(self) -> None:
        """Load token from file if it exists."""
        if not self.token_file.exists():
            return

        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            self.access_token = token_data.get("access_token")
            expires_at_str = token_data.get("token_expires_at")

            if expires_at_str:
                self.token_expires_at = datetime.fromisoformat(expires_at_str)

        except Exception as e:
            # Log error but don't raise - we'll just get a new token
            print(f"Warning: Failed to load token: {e}")
            self.access_token = None
            self.token_expires_at = None

    def invalidate_token(self) -> None:
        """Invalidate current token and remove from cache."""
        self.access_token = None
        self.token_expires_at = None

        if self.token_file.exists():
            try:
                self.token_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete token file: {e}")

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dictionary with authorization header

        Raises:
            AuthenticationError: If token acquisition fails
        """
        token = self.get_access_token()
        return {
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
