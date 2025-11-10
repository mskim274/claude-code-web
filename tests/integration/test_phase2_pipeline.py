"""
Integration tests for Phase 2 pipeline.

Tests the complete data pipeline:
- API → Pydantic models → DataFrame
- API → Database storage
- Database → Backtesting
"""
import pytest
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any
from pydantic import BaseModel, Field

from collectors.apis.unified import UnifiedAPIClient, DataSource
from tests.fixtures.mock_apis import MockKiwoomAPI, MockKISAPI, MockDARTAPI


# Pydantic models for data validation
class StockPriceModel(BaseModel):
    """Pydantic model for stock price data"""
    code: str
    name: str
    current_price: int
    open_price: int
    high_price: int
    low_price: int
    volume: int
    change_rate: float
    change_price: int
    timestamp: str
    source: str


class FinancialDataModel(BaseModel):
    """Pydantic model for financial data"""
    corp_code: str
    year: int
    quarter: int
    total_assets: int
    total_liabilities: int
    total_equity: int
    revenue: int
    operating_profit: int
    net_income: int
    source: str


class OverseasStockModel(BaseModel):
    """Pydantic model for overseas stock"""
    symbol: str
    exchange: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    change_rate: float
    timestamp: str
    source: str


class TestAPItoPydantic:
    """Test API data conversion to Pydantic models"""

    def test_stock_price_to_pydantic(self):
        """Test converting stock price API response to Pydantic model"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        data = client.get_stock_price("005930", source=DataSource.KIS)

        # Validate with Pydantic
        model = StockPriceModel(**data)

        assert model.code == "005930"
        assert model.source == "kis"
        assert isinstance(model.current_price, int)
        assert isinstance(model.change_rate, float)

    def test_financial_data_to_pydantic(self):
        """Test converting financial data API response to Pydantic model"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI())
        data = client.get_financial_data("005930", 2023, 4)

        # Validate with Pydantic
        model = FinancialDataModel(**data)

        assert model.year == 2023
        assert model.quarter == 4
        assert isinstance(model.total_assets, int)
        assert isinstance(model.revenue, int)

    def test_overseas_stock_to_pydantic(self):
        """Test converting overseas stock API response to Pydantic model"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        data = client.get_overseas_stock("AAPL", "NASDAQ")

        # Validate with Pydantic
        model = OverseasStockModel(**data)

        assert model.symbol == "AAPL"
        assert model.exchange == "NASDAQ"
        assert isinstance(model.current_price, float)

    def test_pydantic_validation_error(self):
        """Test Pydantic validation catches invalid data"""
        invalid_data = {
            "code": "005930",
            "current_price": "invalid",  # Should be int
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            StockPriceModel(**invalid_data)


class TestPydanticToDataFrame:
    """Test converting Pydantic models to pandas DataFrame"""

    def test_single_stock_to_dataframe(self):
        """Test converting single stock price to DataFrame"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        data = client.get_stock_price("005930", source=DataSource.KIS)

        model = StockPriceModel(**data)
        df = pd.DataFrame([model.dict()])

        assert len(df) == 1
        assert "code" in df.columns
        assert "current_price" in df.columns
        assert df.iloc[0]["code"] == "005930"

    def test_multiple_stocks_to_dataframe(self):
        """Test converting multiple stocks to DataFrame"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        stock_codes = ["005930", "000660", "035720"]
        models = []

        for code in stock_codes:
            data = client.get_stock_price(code, source=DataSource.KIS)
            models.append(StockPriceModel(**data))

        df = pd.DataFrame([m.dict() for m in models])

        assert len(df) == 3
        assert list(df["code"]) == stock_codes
        assert df["current_price"].dtype in [int, 'int64']

    def test_financial_data_to_dataframe(self):
        """Test converting financial data to DataFrame"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI())

        # Get multiple quarters
        models = []
        for quarter in [1, 2, 3, 4]:
            data = client.get_financial_data("005930", 2023, quarter)
            models.append(FinancialDataModel(**data))

        df = pd.DataFrame([m.dict() for m in models])

        assert len(df) == 4
        assert "revenue" in df.columns
        assert "net_income" in df.columns
        assert df["quarter"].tolist() == [1, 2, 3, 4]

    def test_dataframe_column_types(self):
        """Test DataFrame has correct column types"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        data = client.get_stock_price("005930", source=DataSource.KIS)

        model = StockPriceModel(**data)
        df = pd.DataFrame([model.dict()])

        # Check numeric columns
        assert df["current_price"].dtype in [int, 'int64']
        assert df["volume"].dtype in [int, 'int64']
        assert df["change_rate"].dtype in [float, 'float64']


class TestAPItoDatabase:
    """Test API data storage to database (simulated)"""

    def test_store_stock_price_data(self):
        """Test storing stock price data in database format"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        data = client.get_stock_price("005930", source=DataSource.KIS)

        # Simulate database storage
        db_record = {
            "code": data["code"],
            "price": data["current_price"],
            "volume": data["volume"],
            "timestamp": datetime.now(),
            "source": data["source"],
        }

        assert db_record["code"] == "005930"
        assert isinstance(db_record["price"], int)
        assert isinstance(db_record["timestamp"], datetime)

    def test_bulk_insert_stock_data(self):
        """Test bulk inserting multiple stock records"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        stock_codes = ["005930", "000660", "035720", "035420", "051910"]
        records = []

        for code in stock_codes:
            data = client.get_stock_price(code, source=DataSource.KIS)
            records.append({
                "code": data["code"],
                "price": data["current_price"],
                "volume": data["volume"],
                "timestamp": datetime.now(),
            })

        # Simulate bulk insert
        assert len(records) == 5
        assert all("code" in r for r in records)
        assert all("price" in r for r in records)

    def test_store_financial_data(self):
        """Test storing financial data in database format"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI())
        data = client.get_financial_data("005930", 2023, 4)

        # Simulate database storage
        db_record = {
            "corp_code": data["corp_code"],
            "year": data["year"],
            "quarter": data["quarter"],
            "revenue": data["revenue"],
            "net_income": data["net_income"],
            "stored_at": datetime.now(),
        }

        assert db_record["year"] == 2023
        assert db_record["quarter"] == 4
        assert isinstance(db_record["revenue"], int)

    def test_upsert_behavior(self):
        """Test upsert (insert or update) behavior"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        # First insert
        data1 = client.get_stock_price("005930", source=DataSource.KIS)
        record1 = {
            "code": data1["code"],
            "price": data1["current_price"],
            "timestamp": datetime.now(),
        }

        # Simulate clearing cache to get "updated" data
        client.clear_cache()

        # Second insert (same code)
        data2 = client.get_stock_price("005930", source=DataSource.KIS)
        record2 = {
            "code": data2["code"],
            "price": data2["current_price"],
            "timestamp": datetime.now(),
        }

        # In real DB, this would update the existing record
        assert record1["code"] == record2["code"]
        assert record2["timestamp"] >= record1["timestamp"]


class TestDatabaseToBacktesting:
    """Test loading data from database for backtesting"""

    def test_load_historical_prices_for_backtest(self):
        """Test loading historical price data for backtesting"""
        # Simulate loading from database
        historical_data = []

        for i in range(30):  # 30 days of data
            historical_data.append({
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "code": "005930",
                "open": 70000 + (i * 100),
                "high": 71000 + (i * 100),
                "low": 69000 + (i * 100),
                "close": 70500 + (i * 100),
                "volume": 1000000 + (i * 10000),
            })

        df = pd.DataFrame(historical_data)

        assert len(df) == 30
        assert "date" in df.columns
        assert "close" in df.columns
        assert df["code"].unique()[0] == "005930"

    def test_prepare_backtest_data(self):
        """Test preparing data for backtesting"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        # Get current data (in real scenario, this would be historical)
        stocks = ["005930", "000660", "035720"]
        data = []

        for code in stocks:
            price = client.get_stock_price(code, source=DataSource.KIS)
            data.append({
                "code": code,
                "close": price["current_price"],
                "volume": price["volume"],
            })

        df = pd.DataFrame(data)

        # Prepare for backtest
        df["returns"] = df["close"].pct_change()

        assert len(df) == 3
        assert "returns" in df.columns

    def test_merge_price_and_financial_data(self):
        """Test merging price and financial data for fundamental analysis"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        # Get price data
        price_data = client.get_stock_price("005930", source=DataSource.KIS)

        # Get financial data
        financial_data = client.get_financial_data("005930", 2023, 4)

        # Merge for analysis
        merged = {
            "code": price_data["code"],
            "price": price_data["current_price"],
            "revenue": financial_data["revenue"],
            "net_income": financial_data["net_income"],
            "roe": (
                financial_data["net_income"] /
                financial_data["total_equity"] * 100
                if financial_data["total_equity"] > 0 else 0
            ),
        }

        assert "price" in merged
        assert "revenue" in merged
        assert "roe" in merged


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline"""

    def test_complete_pipeline_stock_analysis(self):
        """Test complete pipeline: API → Validation → DataFrame → Analysis"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        # Step 1: Get comprehensive data
        comprehensive = client.get_comprehensive_data("005930", year=2023, quarter=4)

        # Step 2: Validate with Pydantic
        price_model = StockPriceModel(**comprehensive["price"])
        financial_model = FinancialDataModel(**comprehensive["financial"])

        # Step 3: Convert to DataFrame
        df = pd.DataFrame([{
            **price_model.dict(),
            **financial_model.dict(),
            **comprehensive["metrics"]
        }])

        # Step 4: Perform analysis
        df["price_to_revenue"] = df["current_price"] / (df["revenue"] / 1000000)

        assert len(df) == 1
        assert "roe" in df.columns
        assert "price_to_revenue" in df.columns

    def test_multi_stock_screening_pipeline(self):
        """Test pipeline for screening multiple stocks"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        stock_codes = ["005930", "000660", "035720"]
        results = []

        for code in stock_codes:
            try:
                data = client.get_comprehensive_data(code, year=2023, quarter=4)
                if data["price"] and data["financial"]:
                    results.append({
                        "code": code,
                        "price": data["price"]["current_price"],
                        "roe": data["metrics"].get("roe", 0),
                        "debt_ratio": data["metrics"].get("debt_ratio", 0),
                    })
            except Exception as e:
                print(f"Failed to get data for {code}: {e}")

        df = pd.DataFrame(results)

        # Screen: ROE > 10%
        high_roe_stocks = df[df["roe"] > 10]

        assert len(df) == 3
        assert "roe" in df.columns

    def test_time_series_data_collection(self):
        """Test collecting time series data"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        # Simulate collecting data over time
        time_series = []

        for i in range(5):
            # Clear cache to simulate new data
            client.clear_cache()

            data = client.get_stock_price("005930", source=DataSource.KIS)
            time_series.append({
                "timestamp": datetime.now() - timedelta(minutes=i),
                "price": data["current_price"],
                "volume": data["volume"],
            })

        df = pd.DataFrame(time_series)
        df = df.sort_values("timestamp")

        assert len(df) == 5
        assert "timestamp" in df.columns
        assert df["timestamp"].is_monotonic_increasing
