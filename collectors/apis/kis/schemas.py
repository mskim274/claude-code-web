"""
Pydantic schemas for KIS API responses.

Provides type-safe data validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date as date_type, datetime
from enum import Enum
from typing import Optional


class KISMarketType(str, Enum):
    """Korean stock market types."""
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KONEX = "KONEX"


class KISExchange(str, Enum):
    """Overseas stock exchanges."""
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    AMEX = "AMEX"
    HKEX = "HKEX"  # Hong Kong
    TSE = "TSE"    # Tokyo
    SSE = "SSE"    # Shanghai
    SZSE = "SZSE"  # Shenzhen


class KISStockPrice(BaseModel):
    """KIS API domestic stock price schema."""

    code: str = Field(..., description="Stock code (6 digits)")
    name: str = Field(..., description="Stock name")
    current_price: int = Field(..., ge=0, description="Current price")
    open: int = Field(..., ge=0, description="Opening price")
    high: int = Field(..., ge=0, description="Highest price")
    low: int = Field(..., ge=0, description="Lowest price")
    volume: int = Field(..., ge=0, description="Trading volume")
    change: Optional[int] = Field(None, description="Price change")
    change_rate: Optional[float] = Field(None, description="Price change rate (%)")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "code": "005930",
                "name": "삼성전자",
                "current_price": 70000,
                "open": 69000,
                "high": 71000,
                "low": 68500,
                "volume": 10000000,
                "change": 1000,
                "change_rate": 1.45
            }
        }


class KISDailyPrice(BaseModel):
    """KIS API domestic stock daily price schema."""

    code: str = Field(..., description="Stock code")
    date: date_type = Field(..., description="Trading date")
    open: int = Field(..., ge=0, description="Opening price")
    high: int = Field(..., ge=0, description="Highest price")
    low: int = Field(..., ge=0, description="Lowest price")
    close: int = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")
    change: Optional[int] = Field(None, description="Price change")
    change_rate: Optional[float] = Field(None, description="Price change rate (%)")

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Convert string date to date object."""
        if isinstance(v, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y%m%d']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {v}")
        return v

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "code": "005930",
                "date": "2024-01-15",
                "open": 69000,
                "high": 71000,
                "low": 68500,
                "close": 70000,
                "volume": 15000000,
                "change": 1000,
                "change_rate": 1.45
            }
        }


class KISOverseasStock(BaseModel):
    """KIS API overseas stock price schema."""

    symbol: str = Field(..., description="Stock symbol")
    exchange: KISExchange = Field(..., description="Stock exchange")
    name: str = Field(..., description="Stock name")
    current_price: float = Field(..., ge=0, description="Current price")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Highest price")
    low: float = Field(..., ge=0, description="Lowest price")
    volume: int = Field(..., ge=0, description="Trading volume")
    currency: str = Field(default="USD", description="Currency code")
    change: Optional[float] = Field(None, description="Price change")
    change_rate: Optional[float] = Field(None, description="Price change rate (%)")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "name": "Apple Inc.",
                "current_price": 175.50,
                "open": 174.00,
                "high": 176.00,
                "low": 173.50,
                "volume": 50000000,
                "currency": "USD",
                "change": 1.50,
                "change_rate": 0.86
            }
        }


class KISOverseasDaily(BaseModel):
    """KIS API overseas stock daily price schema."""

    symbol: str = Field(..., description="Stock symbol")
    exchange: KISExchange = Field(..., description="Stock exchange")
    date: date_type = Field(..., description="Trading date")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Highest price")
    low: float = Field(..., ge=0, description="Lowest price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")
    currency: str = Field(default="USD", description="Currency code")
    change: Optional[float] = Field(None, description="Price change")
    change_rate: Optional[float] = Field(None, description="Price change rate (%)")

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Convert string date to date object."""
        if isinstance(v, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y%m%d']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {v}")
        return v

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "date": "2024-01-15",
                "open": 174.00,
                "high": 176.00,
                "low": 173.50,
                "close": 175.50,
                "volume": 50000000,
                "currency": "USD"
            }
        }
