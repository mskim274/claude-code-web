"""
Unit tests for Financial Metrics Calculation
TDD Red Phase
"""
import pytest
from collectors.apis.dart.financial_metrics import FinancialMetricsCalculator


class TestFinancialMetricsCalculator:
    """Test financial metrics calculation functions"""

    @pytest.fixture
    def calculator(self):
        return FinancialMetricsCalculator()

    def test_calculate_per(self, calculator):
        """Test PER (Price Earnings Ratio) calculation"""
        market_cap = 400000000000000  # 400 trillion
        net_income = 35539395000000   # 35.5 trillion

        per = calculator.calculate_per(market_cap, net_income)

        expected_per = market_cap / net_income
        assert abs(per - expected_per) < 0.01
        assert abs(per - 11.25) < 0.1

    def test_calculate_per_zero_net_income(self, calculator):
        """Test PER with zero net income"""
        market_cap = 400000000000000
        net_income = 0

        per = calculator.calculate_per(market_cap, net_income)

        assert per is None or per == float('inf')

    def test_calculate_per_negative_net_income(self, calculator):
        """Test PER with negative net income (loss)"""
        market_cap = 400000000000000
        net_income = -10000000000  # Loss

        per = calculator.calculate_per(market_cap, net_income)

        # PER with negative earnings should be negative or None
        assert per is None or per < 0

    def test_calculate_pbr(self, calculator):
        """Test PBR (Price to Book Ratio) calculation"""
        market_cap = 400000000000000   # 400 trillion
        total_equity = 333099690000000  # 333 trillion

        pbr = calculator.calculate_pbr(market_cap, total_equity)

        expected_pbr = market_cap / total_equity
        assert abs(pbr - expected_pbr) < 0.01
        assert abs(pbr - 1.20) < 0.1

    def test_calculate_pbr_zero_equity(self, calculator):
        """Test PBR with zero equity"""
        market_cap = 400000000000000
        total_equity = 0

        pbr = calculator.calculate_pbr(market_cap, total_equity)

        assert pbr is None or pbr == float('inf')

    def test_calculate_roe(self, calculator):
        """Test ROE (Return on Equity) calculation"""
        net_income = 35539395000000    # 35.5 trillion
        total_equity = 333099690000000  # 333 trillion

        roe = calculator.calculate_roe(net_income, total_equity)

        expected_roe = (net_income / total_equity) * 100
        assert abs(roe - expected_roe) < 0.01
        assert abs(roe - 10.67) < 0.1

    def test_calculate_roe_zero_equity(self, calculator):
        """Test ROE with zero equity"""
        net_income = 35539395000000
        total_equity = 0

        roe = calculator.calculate_roe(net_income, total_equity)

        assert roe is None or roe == float('inf')

    def test_calculate_debt_ratio(self, calculator):
        """Test debt ratio calculation"""
        total_liabilities = 114963472000000  # 115 trillion
        total_equity = 333099690000000       # 333 trillion

        debt_ratio = calculator.calculate_debt_ratio(total_liabilities, total_equity)

        expected_debt_ratio = (total_liabilities / total_equity) * 100
        assert abs(debt_ratio - expected_debt_ratio) < 0.01
        assert abs(debt_ratio - 34.52) < 0.1

    def test_calculate_debt_ratio_zero_equity(self, calculator):
        """Test debt ratio with zero equity"""
        total_liabilities = 114963472000000
        total_equity = 0

        debt_ratio = calculator.calculate_debt_ratio(total_liabilities, total_equity)

        assert debt_ratio is None or debt_ratio == float('inf')

    def test_calculate_operating_margin(self, calculator):
        """Test operating margin calculation"""
        operating_profit = 42510611000000  # 42.5 trillion
        revenue = 302231154000000          # 302 trillion

        operating_margin = calculator.calculate_operating_margin(operating_profit, revenue)

        expected_margin = (operating_profit / revenue) * 100
        assert abs(operating_margin - expected_margin) < 0.01
        assert abs(operating_margin - 14.07) < 0.1

    def test_calculate_net_margin(self, calculator):
        """Test net profit margin calculation"""
        net_income = 35539395000000   # 35.5 trillion
        revenue = 302231154000000     # 302 trillion

        net_margin = calculator.calculate_net_margin(net_income, revenue)

        expected_margin = (net_income / revenue) * 100
        assert abs(net_margin - expected_margin) < 0.01
        assert abs(net_margin - 11.76) < 0.1

    def test_calculate_all_metrics(self, calculator):
        """Test calculating all metrics at once"""
        financial_data = {
            "revenue": 302231154000000,
            "operating_profit": 42510611000000,
            "net_income": 35539395000000,
            "total_assets": 448063162000000,
            "total_liabilities": 114963472000000,
            "total_equity": 333099690000000
        }
        market_cap = 400000000000000

        metrics = calculator.calculate_all_metrics(financial_data, market_cap)

        assert "per" in metrics
        assert "pbr" in metrics
        assert "roe" in metrics
        assert "debt_ratio" in metrics
        assert "operating_margin" in metrics
        assert "net_margin" in metrics

        assert abs(metrics["per"] - 11.25) < 0.1
        assert abs(metrics["pbr"] - 1.20) < 0.1
        assert abs(metrics["roe"] - 10.67) < 0.1
        assert abs(metrics["debt_ratio"] - 34.52) < 0.1

    def test_calculate_all_metrics_missing_data(self, calculator):
        """Test calculating metrics with missing data"""
        financial_data = {
            "revenue": 302231154000000,
            # Missing other fields
        }
        market_cap = 400000000000000

        metrics = calculator.calculate_all_metrics(financial_data, market_cap)

        # Should handle missing data gracefully
        assert metrics["per"] is None
        assert metrics["pbr"] is None
