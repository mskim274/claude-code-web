"""
KIS API client package.

Korean Investment & Securities OpenAPI integration.
"""

from .client import KISClient, KISAPIError, KISNetworkError, KISRateLimitError
from .mock_client import MockKISClient
from .auth import KISAuth, AuthenticationError, TokenExpiredError
from .schemas import (
    KISStockPrice,
    KISDailyPrice,
    KISOverseasStock,
    KISOverseasDaily,
    KISMarketType,
    KISExchange
)
from .rate_limiter import (
    RateLimiter,
    TokenBucketRateLimiter,
    RateLimitExceeded,
    AdaptiveRateLimiter
)

__version__ = "1.0.0"

__all__ = [
    # Client
    "KISClient",
    "MockKISClient",

    # Authentication
    "KISAuth",
    "AuthenticationError",
    "TokenExpiredError",

    # Schemas
    "KISStockPrice",
    "KISDailyPrice",
    "KISOverseasStock",
    "KISOverseasDaily",
    "KISMarketType",
    "KISExchange",

    # Rate limiting
    "RateLimiter",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
    "AdaptiveRateLimiter",

    # Errors
    "KISAPIError",
    "KISNetworkError",
    "KISRateLimitError",
]
