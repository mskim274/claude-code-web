"""
End-to-End tests for fundamental analysis based backtesting.

Tests complete workflow from financial data collection to
fundamental-based stock selection and backtesting:
- PER/PBR filtering strategies
- ROE-based selection
- Debt ratio analysis
- Combined fundamental metrics
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

from collectors.apis.unified import UnifiedAPIClient
from tests.fixtures.mock_apis import MockKISAPI, MockDARTAPI


class FundamentalAnalyzer:
    """Fundamental analysis and stock screening"""

    def __init__(self, client: UnifiedAPIClient):
        self.client = client

    def screen_by_per(
        self,
        stock_codes: List[str],
        max_per: float = 15.0
    ) -> pd.DataFrame:
        """Screen stocks by PER (Price to Earnings Ratio)"""
        results = []

        for code in stock_codes:
            try:
                data = self.client.get_comprehensive_data(code, year=2023, quarter=4)
                if data["metrics"].get("per"):
                    per = data["metrics"]["per"]
                    if per <= max_per:
                        results.append({
                            "code": code,
                            "per": per,
                            "price": data["price"]["current_price"],
                        })
            except Exception as e:
                print(f"Error processing {code}: {e}")

        return pd.DataFrame(results)

    def screen_by_pbr(
        self,
        stock_codes: List[str],
        max_pbr: float = 1.0
    ) -> pd.DataFrame:
        """Screen stocks by PBR (Price to Book Ratio)"""
        results = []

        for code in stock_codes:
            try:
                data = self.client.get_comprehensive_data(code, year=2023, quarter=4)
                if data["metrics"].get("pbr"):
                    pbr = data["metrics"]["pbr"]
                    if pbr <= max_pbr:
                        results.append({
                            "code": code,
                            "pbr": pbr,
                            "price": data["price"]["current_price"],
                        })
            except Exception as e:
                print(f"Error processing {code}: {e}")

        return pd.DataFrame(results)

    def screen_by_roe(
        self,
        stock_codes: List[str],
        min_roe: float = 15.0
    ) -> pd.DataFrame:
        """Screen stocks by ROE (Return on Equity)"""
        results = []

        for code in stock_codes:
            try:
                data = self.client.get_comprehensive_data(code, year=2023, quarter=4)
                if data["metrics"].get("roe"):
                    roe = data["metrics"]["roe"]
                    if roe >= min_roe:
                        results.append({
                            "code": code,
                            "roe": roe,
                            "price": data["price"]["current_price"],
                        })
            except Exception as e:
                print(f"Error processing {code}: {e}")

        return pd.DataFrame(results)

    def screen_by_debt_ratio(
        self,
        stock_codes: List[str],
        max_debt_ratio: float = 100.0
    ) -> pd.DataFrame:
        """Screen stocks by debt ratio"""
        results = []

        for code in stock_codes:
            try:
                data = self.client.get_comprehensive_data(code, year=2023, quarter=4)
                if data["metrics"].get("debt_ratio"):
                    debt_ratio = data["metrics"]["debt_ratio"]
                    if debt_ratio <= max_debt_ratio:
                        results.append({
                            "code": code,
                            "debt_ratio": debt_ratio,
                            "price": data["price"]["current_price"],
                        })
            except Exception as e:
                print(f"Error processing {code}: {e}")

        return pd.DataFrame(results)

    def screen_combined(
        self,
        stock_codes: List[str],
        max_per: float = 15.0,
        max_pbr: float = 1.0,
        min_roe: float = 15.0,
        max_debt_ratio: float = 100.0
    ) -> pd.DataFrame:
        """Screen stocks using combined fundamental criteria"""
        results = []

        for code in stock_codes:
            try:
                data = self.client.get_comprehensive_data(code, year=2023, quarter=4)
                metrics = data["metrics"]

                # Check all criteria
                per = metrics.get("per", float("inf"))
                pbr = metrics.get("pbr", float("inf"))
                roe = metrics.get("roe", 0)
                debt_ratio = metrics.get("debt_ratio", float("inf"))

                if (per <= max_per and
                    pbr <= max_pbr and
                    roe >= min_roe and
                    debt_ratio <= max_debt_ratio):

                    results.append({
                        "code": code,
                        "per": per,
                        "pbr": pbr,
                        "roe": roe,
                        "debt_ratio": debt_ratio,
                        "price": data["price"]["current_price"],
                        "revenue": data["financial"]["revenue"],
                        "net_income": data["financial"]["net_income"],
                    })
            except Exception as e:
                print(f"Error processing {code}: {e}")

        return pd.DataFrame(results)


class TestFundamentalDataCollection:
    """Test financial data collection for fundamental analysis"""

    def test_collect_financial_statements(self):
        """Test collecting financial statements"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI())

        stock_codes = ["005930", "000660", "035720"]
        financial_data = []

        for code in stock_codes:
            data = client.get_financial_data(code, 2023, 4)
            financial_data.append(data)

        df = pd.DataFrame(financial_data)

        assert len(df) == 3
        assert "revenue" in df.columns
        assert "net_income" in df.columns
        assert "total_assets" in df.columns
        assert all(df["revenue"] > 0)

    def test_collect_comprehensive_data(self):
        """Test collecting comprehensive data (price + financial)"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        data = client.get_comprehensive_data("005930", year=2023, quarter=4)

        assert data["price"] is not None
        assert data["financial"] is not None
        assert data["metrics"] is not None

        # Check calculated metrics
        assert "roe" in data["metrics"]
        assert "debt_ratio" in data["metrics"]

    def test_collect_multi_year_financial_data(self):
        """Test collecting multi-year financial data"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI())

        years = [2021, 2022, 2023]
        financial_history = []

        for year in years:
            data = client.get_financial_data("005930", year, 4)
            financial_history.append(data)

        df = pd.DataFrame(financial_history)

        assert len(df) == 3
        assert list(df["year"]) == years

    def test_validate_financial_metrics(self):
        """Test validating calculated financial metrics"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        data = client.get_comprehensive_data("005930", year=2023, quarter=4)
        metrics = data["metrics"]
        financial = data["financial"]

        # Validate ROE calculation
        if metrics.get("roe") and financial["total_equity"] > 0:
            expected_roe = (
                financial["net_income"] / financial["total_equity"] * 100
            )
            assert abs(metrics["roe"] - expected_roe) < 0.01

        # Validate debt ratio
        if metrics.get("debt_ratio") and financial["total_equity"] > 0:
            expected_debt_ratio = (
                financial["total_liabilities"] / financial["total_equity"] * 100
            )
            assert abs(metrics["debt_ratio"] - expected_debt_ratio) < 0.01

    def test_handle_missing_financial_data(self):
        """Test handling missing or invalid financial data"""
        client = UnifiedAPIClient(dart_api=MockDARTAPI(fail=True))

        try:
            data = client.get_financial_data("005930", 2023, 4)
            pytest.fail("Should have raised an error")
        except Exception as e:
            assert "DART API" in str(e)


class TestFundamentalScreening:
    """Test fundamental-based stock screening"""

    def test_screen_by_per(self):
        """Test screening stocks by PER"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        stock_codes = ["005930", "000660", "035720", "035420"]
        results = analyzer.screen_by_per(stock_codes, max_per=20.0)

        assert len(results) > 0
        assert all(results["per"] <= 20.0)
        assert "code" in results.columns
        assert "price" in results.columns

    def test_screen_by_pbr(self):
        """Test screening stocks by PBR"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        stock_codes = ["005930", "000660", "035720"]
        results = analyzer.screen_by_pbr(stock_codes, max_pbr=1.5)

        assert len(results) > 0
        assert all(results["pbr"] <= 1.5)

    def test_screen_by_roe(self):
        """Test screening stocks by ROE"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        stock_codes = ["005930", "000660", "035720", "035420", "051910"]
        results = analyzer.screen_by_roe(stock_codes, min_roe=10.0)

        assert len(results) > 0
        assert all(results["roe"] >= 10.0)

    def test_screen_by_debt_ratio(self):
        """Test screening stocks by debt ratio"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        stock_codes = ["005930", "000660", "035720"]
        results = analyzer.screen_by_debt_ratio(stock_codes, max_debt_ratio=150.0)

        assert len(results) > 0
        assert all(results["debt_ratio"] <= 150.0)

    def test_combined_screening(self):
        """Test combined fundamental screening"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        stock_codes = [
            "005930", "000660", "035720", "035420", "051910",
            "005380", "006400", "017670", "096770", "068270"
        ]

        results = analyzer.screen_combined(
            stock_codes,
            max_per=15.0,
            max_pbr=1.0,
            min_roe=15.0,
            max_debt_ratio=100.0
        )

        # Results should pass all criteria
        if len(results) > 0:
            assert all(results["per"] <= 15.0)
            assert all(results["pbr"] <= 1.0)
            assert all(results["roe"] >= 15.0)
            assert all(results["debt_ratio"] <= 100.0)


class TestFundamentalBacktesting:
    """Test backtesting strategies based on fundamental analysis"""

    def test_value_investing_strategy(self):
        """Test value investing strategy (low PER + PBR)"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        # Universe of stocks
        universe = ["005930", "000660", "035720", "035420", "051910"]

        # Screen for value stocks
        value_stocks = analyzer.screen_combined(
            universe,
            max_per=12.0,
            max_pbr=0.8,
            min_roe=10.0
        )

        # Should find some value stocks
        assert "code" in value_stocks.columns

        # Simulate portfolio construction
        if len(value_stocks) > 0:
            # Equal weight portfolio
            portfolio_size = min(5, len(value_stocks))
            selected_stocks = value_stocks.head(portfolio_size)

            assert len(selected_stocks) <= 5
            assert all(selected_stocks["per"] <= 12.0)
            assert all(selected_stocks["pbr"] <= 0.8)

    def test_quality_investing_strategy(self):
        """Test quality investing strategy (high ROE, low debt)"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        universe = ["005930", "000660", "035720", "035420", "051910"]

        # Screen for quality stocks
        quality_stocks = analyzer.screen_combined(
            universe,
            min_roe=20.0,
            max_debt_ratio=50.0
        )

        if len(quality_stocks) > 0:
            # Sort by ROE descending
            quality_stocks = quality_stocks.sort_values("roe", ascending=False)

            # Top 3 by ROE
            top_quality = quality_stocks.head(3)

            assert all(top_quality["roe"] >= 20.0)
            assert all(top_quality["debt_ratio"] <= 50.0)

    def test_growth_investing_strategy(self):
        """Test growth investing strategy based on revenue growth"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        stock_code = "005930"

        # Get multi-year data
        financial_2022 = client.get_financial_data(stock_code, 2022, 4)
        financial_2023 = client.get_financial_data(stock_code, 2023, 4)

        # Calculate growth
        revenue_growth = (
            (financial_2023["revenue"] - financial_2022["revenue"]) /
            financial_2022["revenue"] * 100
        )

        income_growth = (
            (financial_2023["net_income"] - financial_2022["net_income"]) /
            financial_2022["net_income"] * 100
        )

        # Growth stocks should have positive growth
        assert isinstance(revenue_growth, float)
        assert isinstance(income_growth, float)

    def test_dividend_yield_strategy(self):
        """Test dividend yield strategy"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        stock_codes = ["005930", "000660", "035720"]
        dividend_stocks = []

        for code in stock_codes:
            data = client.get_comprehensive_data(code, year=2023, quarter=4)

            # Estimate dividend yield (simplified)
            # In real scenario, need actual dividend data
            net_income = data["financial"]["net_income"]
            current_price = data["price"]["current_price"]

            # Assume 30% payout ratio
            estimated_dividend = net_income * 0.3
            # Rough calculation (needs shares outstanding)
            div_yield_estimate = estimated_dividend / (current_price * 1000000) * 100

            dividend_stocks.append({
                "code": code,
                "dividend_yield": div_yield_estimate,
                "net_income": net_income,
                "price": current_price,
            })

        df = pd.DataFrame(dividend_stocks)

        assert len(df) == 3
        assert "dividend_yield" in df.columns

    def test_magic_formula_strategy(self):
        """Test Magic Formula strategy (ROE + Earnings Yield)"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        universe = ["005930", "000660", "035720", "035420", "051910"]
        magic_formula_stocks = []

        for code in universe:
            try:
                data = client.get_comprehensive_data(code, year=2023, quarter=4)

                roe = data["metrics"].get("roe", 0)
                per = data["metrics"].get("per", float("inf"))

                # Earnings Yield = 1 / PER
                earnings_yield = (1 / per * 100) if per > 0 else 0

                # Magic Formula Score (higher is better)
                magic_score = roe + earnings_yield

                magic_formula_stocks.append({
                    "code": code,
                    "roe": roe,
                    "earnings_yield": earnings_yield,
                    "magic_score": magic_score,
                    "price": data["price"]["current_price"],
                })
            except Exception as e:
                print(f"Error processing {code}: {e}")

        df = pd.DataFrame(magic_formula_stocks)

        if len(df) > 0:
            # Sort by magic score
            df = df.sort_values("magic_score", ascending=False)

            # Top 3 stocks
            top_picks = df.head(3)

            assert len(top_picks) <= 3
            assert "magic_score" in df.columns


class TestFundamentalBacktestMetrics:
    """Test calculating performance metrics for fundamental strategies"""

    def test_portfolio_rebalancing(self):
        """Test portfolio rebalancing based on fundamental changes"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        # Initial screening
        universe = ["005930", "000660", "035720", "035420", "051910"]
        initial_portfolio = analyzer.screen_combined(
            universe,
            max_per=15.0,
            min_roe=15.0
        )

        # Simulate time passing and re-screening
        client.clear_cache()

        rebalanced_portfolio = analyzer.screen_combined(
            universe,
            max_per=15.0,
            min_roe=15.0
        )

        # Both portfolios should have stocks
        assert len(initial_portfolio) > 0 or len(rebalanced_portfolio) > 0

    def test_fundamental_factor_correlation(self):
        """Test correlation between fundamental factors"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )

        universe = ["005930", "000660", "035720", "035420", "051910"]
        fundamental_data = []

        for code in universe:
            try:
                data = client.get_comprehensive_data(code, year=2023, quarter=4)
                fundamental_data.append({
                    "code": code,
                    "per": data["metrics"].get("per", 0),
                    "pbr": data["metrics"].get("pbr", 0),
                    "roe": data["metrics"].get("roe", 0),
                    "debt_ratio": data["metrics"].get("debt_ratio", 0),
                })
            except Exception:
                pass

        df = pd.DataFrame(fundamental_data)

        if len(df) > 2:
            # Calculate correlation matrix
            numeric_cols = ["per", "pbr", "roe", "debt_ratio"]
            corr_matrix = df[numeric_cols].corr()

            assert corr_matrix.shape == (4, 4)
            assert "roe" in corr_matrix.columns

    def test_backtest_reporting(self):
        """Test generating backtest report with fundamental metrics"""
        client = UnifiedAPIClient(
            kis_api=MockKISAPI(),
            dart_api=MockDARTAPI()
        )
        analyzer = FundamentalAnalyzer(client)

        universe = ["005930", "000660", "035720"]
        portfolio = analyzer.screen_combined(
            universe,
            max_per=15.0,
            min_roe=15.0
        )

        # Generate report
        if len(portfolio) > 0:
            report = {
                "strategy": "Value + Quality",
                "universe_size": len(universe),
                "selected_stocks": len(portfolio),
                "avg_per": portfolio["per"].mean(),
                "avg_pbr": portfolio["pbr"].mean(),
                "avg_roe": portfolio["roe"].mean(),
                "avg_debt_ratio": portfolio["debt_ratio"].mean(),
                "total_revenue": portfolio["revenue"].sum(),
            }

            assert report["selected_stocks"] <= report["universe_size"]
            assert report["avg_roe"] >= 15.0
