"""
Pytest configuration and fixtures for the entire test suite
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import List, Dict


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """테스트용 OHLCV 데이터 (30일치)"""
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')

    # 시드를 고정해서 재현 가능한 테스트 데이터 생성
    np.random.seed(42)

    base_price = 70000
    data = {
        'date': dates,
        'open': base_price + np.random.randint(-1000, 1000, 30),
        'high': base_price + np.random.randint(500, 2000, 30),
        'low': base_price + np.random.randint(-2000, -500, 30),
        'close': base_price + np.random.randint(-1000, 1000, 30),
        'volume': np.random.randint(1000000, 5000000, 30)
    }

    df = pd.DataFrame(data)

    # high >= close >= low, high >= open >= low 보장
    df['high'] = df[['open', 'high', 'close']].max(axis=1) + 100
    df['low'] = df[['open', 'low', 'close']].min(axis=1) - 100

    return df


@pytest.fixture
def sample_stock_data() -> Dict:
    """테스트용 종목 데이터"""
    return {
        'code': '005930',
        'name': '삼성전자',
        'market': 'KOSPI',
        'sector': '전기전자',
        'listing_date': date(1975, 6, 11)
    }


@pytest.fixture
def sample_daily_prices() -> List[Dict]:
    """테스트용 일봉 데이터 리스트"""
    base_date = date(2024, 1, 1)
    prices = []

    for i in range(30):
        prices.append({
            'stock_code': '005930',
            'date': base_date + timedelta(days=i),
            'open': 70000 + i * 100,
            'high': 71000 + i * 100,
            'low': 69000 + i * 100,
            'close': 70500 + i * 100,
            'volume': 10000000 + i * 50000,
            'trading_value': 700000000000 + i * 1000000000
        })

    return prices


@pytest.fixture
def sample_minute_prices() -> List[Dict]:
    """테스트용 분봉 데이터 리스트"""
    base_datetime = datetime(2024, 1, 2, 9, 0)  # 장 시작 시간
    prices = []

    for i in range(100):  # 5분봉 100개
        prices.append({
            'stock_code': '005930',
            'datetime': base_datetime + timedelta(minutes=i * 5),
            'interval': 5,
            'open': 70000 + i * 10,
            'high': 70100 + i * 10,
            'low': 69900 + i * 10,
            'close': 70050 + i * 10,
            'volume': 50000 + i * 100
        })

    return prices


@pytest.fixture
def sample_financial_data() -> Dict:
    """테스트용 재무 데이터"""
    return {
        'stock_code': '005930',
        'market_cap': 400000000000000,  # 400조원
        'shares_outstanding': 5969782550,
        'per': 15.5,
        'pbr': 1.2,
        'roe': 8.5,
        'eps': 5000,
        'bps': 45000,
        'dividend_yield': 2.5,
        'dividend_per_share': 1500
    }


@pytest.fixture
def mock_kiwoom_response():
    """Mock 키움 API 응답"""
    return {
        '종목코드': '005930',
        '종목명': '삼성전자',
        '현재가': 70000,
        '시가': 69500,
        '고가': 70500,
        '저가': 69000,
        '거래량': 10000000,
        '거래대금': 700000000000
    }


# ============================================================================
# Additional Helper Functions and Fixtures for Integration/E2E Tests
# ============================================================================

@pytest.fixture
def large_ohlcv() -> pd.DataFrame:
    """대량 테스트용 OHLCV 데이터 (1000일치)"""
    return generate_large_ohlcv_data(days=1000)


@pytest.fixture
def in_memory_db():
    """In-memory SQLite database for testing"""
    from sqlalchemy import create_engine
    from db.models import Base

    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(in_memory_db):
    """Database session fixture"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=in_memory_db)
    session = Session()
    yield session
    session.close()


def generate_large_ohlcv_data(days: int, base_price: int = 70000,
                               seed: int = 42) -> pd.DataFrame:
    """
    Generate large OHLCV dataset with realistic price movements

    Args:
        days: Number of days to generate
        base_price: Starting base price
        seed: Random seed for reproducibility

    Returns:
        pd.DataFrame: OHLCV data with date index
    """
    dates = pd.date_range(start='2020-01-01', periods=days, freq='D')

    np.random.seed(seed)

    data = {
        'date': dates,
        'open': base_price + np.random.randint(-1000, 1000, days),
        'high': base_price + np.random.randint(500, 2000, days),
        'low': base_price + np.random.randint(-2000, -500, days),
        'close': base_price + np.random.randint(-1000, 1000, days),
        'volume': np.random.randint(1000000, 5000000, days)
    }

    df = pd.DataFrame(data)

    # Ensure OHLC integrity
    df['high'] = df[['open', 'high', 'close']].max(axis=1) + 100
    df['low'] = df[['open', 'low', 'close']].min(axis=1) - 100

    return df


def generate_price_dict_list(count: int, stock_code: str = '005930',
                             start_date: date = None) -> List[Dict]:
    """
    Generate list of price dictionaries for testing

    Args:
        count: Number of records to generate
        stock_code: Stock code
        start_date: Starting date (default: 2024-01-01)

    Returns:
        List[Dict]: List of price dictionaries
    """
    if start_date is None:
        start_date = date(2024, 1, 1)

    return [
        {
            'stock_code': stock_code,
            'date': start_date + timedelta(days=i),
            'open': 70000 + i * 10,
            'high': 71000 + i * 10,
            'low': 69000 + i * 10,
            'close': 70500 + i * 10,
            'volume': 10000000 + i * 1000
        }
        for i in range(count)
    ]


def create_test_stock_with_prices(session, stock_code: str = '005930',
                                  num_days: int = 100):
    """
    Create test stock with price data in database

    Args:
        session: SQLAlchemy session
        stock_code: Stock code
        num_days: Number of days of price data
    """
    from db.models import Stock, DailyPrice

    # Create stock
    stock = Stock(
        code=stock_code,
        name='테스트종목',
        market='KOSPI'
    )
    session.add(stock)
    session.commit()

    # Create prices
    base_date = date(2024, 1, 1)
    for i in range(num_days):
        price = DailyPrice(
            stock_code=stock_code,
            date=base_date + timedelta(days=i),
            open=70000 + i * 10,
            high=71000 + i * 10,
            low=69000 + i * 10,
            close=70500 + i * 10,
            volume=10000000
        )
        session.add(price)

    session.commit()


def assert_ohlcv_integrity(df: pd.DataFrame):
    """
    Assert OHLCV data integrity

    Args:
        df: DataFrame with OHLCV data
    """
    assert 'open' in df.columns
    assert 'high' in df.columns
    assert 'low' in df.columns
    assert 'close' in df.columns
    assert 'volume' in df.columns

    assert (df['high'] >= df['close']).all(), "High must be >= close"
    assert (df['high'] >= df['low']).all(), "High must be >= low"
    assert (df['high'] >= df['open']).all(), "High must be >= open"
    assert (df['close'] >= df['low']).all(), "Close must be >= low"
    assert (df['open'] >= df['low']).all(), "Open must be >= low"
    assert (df['volume'] > 0).all(), "Volume must be positive"


@pytest.fixture
def mock_technical_indicators():
    """Mock TechnicalIndicators class for testing without TA-Lib"""
    from unittest.mock import Mock

    mock_indicators = Mock()

    def mock_calculate_sma(df, period=20):
        result = df.copy()
        result[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        return result

    def mock_calculate_rsi(df, period=14):
        result = df.copy()
        # Simplified RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        result[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        return result

    def mock_calculate_all(df):
        result = df.copy()
        result['sma_20'] = df['close'].rolling(window=20).mean()
        result['sma_60'] = df['close'].rolling(window=60).mean()

        # Simplified RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['rsi_14'] = 100 - (100 / (1 + rs))

        # Simplified MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        result['macd'] = ema12 - ema26
        result['macd_signal'] = result['macd'].ewm(span=9).mean()

        return result

    mock_indicators.calculate_sma = mock_calculate_sma
    mock_indicators.calculate_rsi = mock_calculate_rsi
    mock_indicators.calculate_all = mock_calculate_all

    return mock_indicators


# Performance measurement utilities
def measure_execution_time(func, *args, **kwargs):
    """
    Measure function execution time

    Args:
        func: Function to measure
        *args, **kwargs: Function arguments

    Returns:
        tuple: (result, elapsed_time)
    """
    import time
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time
    return result, elapsed_time


def measure_memory_usage():
    """
    Get current process memory usage in MB

    Returns:
        float: Memory usage in MB
    """
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


# Pytest configuration
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )


# Test data validation helpers
def validate_schema_dict(data: Dict, required_fields: List[str]) -> bool:
    """
    Validate that dictionary has required fields

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        bool: True if all fields present
    """
    return all(field in data for field in required_fields)


def generate_realistic_price_series(days: int, start_price: float = 70000,
                                    volatility: float = 0.02,
                                    trend: float = 0.0001) -> np.ndarray:
    """
    Generate realistic price series using geometric Brownian motion

    Args:
        days: Number of days
        start_price: Starting price
        volatility: Daily volatility (e.g., 0.02 = 2%)
        trend: Daily trend (e.g., 0.0001 = 0.01%)

    Returns:
        np.ndarray: Price series
    """
    np.random.seed(42)
    returns = np.random.normal(trend, volatility, days)
    price_series = start_price * np.exp(np.cumsum(returns))
    return price_series
