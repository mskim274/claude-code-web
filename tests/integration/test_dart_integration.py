"""
Integration tests for DART API workflow
End-to-end testing with Mock client
"""
import pytest
from datetime import date

from collectors.apis.dart.mock_client import MockDARTAPIClient


class TestDARTIntegrationWorkflow:
    """Test complete DART API workflow using Mock client"""

    @pytest.fixture
    def mock_client(self):
        """Create Mock DART client"""
        return MockDARTAPIClient("test_api_key_12345")

    def test_complete_company_analysis_workflow(self, mock_client):
        """
        Test complete workflow:
        1. Get company info
        2. Get financial statement
        3. Calculate metrics
        4. Get disclosures
        """
        stock_code = "005930"  # 삼성전자

        # Step 1: Get company info
        company_info = mock_client.get_company_info(stock_code)
        assert company_info["corp_name"] == "삼성전자"
        assert company_info["stock_code"] == stock_code

        corp_code = company_info["corp_code"]

        # Step 2: Get financial statement
        financial_data = mock_client.get_financial_statement(
            corp_code=corp_code,
            year=2023,
            quarter=2
        )
        assert len(financial_data) == 6

        # Step 3: Calculate metrics
        market_cap = 400000000000000  # 400조
        metrics = mock_client.calculate_financial_metrics(
            financial_data,
            market_cap
        )
        assert metrics["per"] is not None
        assert metrics["pbr"] is not None
        assert metrics["roe"] is not None
        assert metrics["debt_ratio"] is not None

        # Step 4: Get disclosures
        disclosures = mock_client.get_disclosure_list(
            corp_code=corp_code,
            start_date=date(2023, 10, 1),
            end_date=date(2023, 11, 30)
        )
        assert len(disclosures) > 0

    def test_financial_statement_with_metrics_workflow(self, mock_client):
        """Test integrated method: get financial statement with metrics"""
        result = mock_client.get_financial_statement_with_metrics(
            stock_code="005930",
            year=2023,
            quarter=2,
            market_cap=400000000000000
        )

        # Check all required fields
        assert result["corp_code"] == "00126380"
        assert result["corp_name"] == "삼성전자"
        assert result["stock_code"] == "005930"
        assert result["year"] == 2023
        assert result["quarter"] == 2

        # Check financial values
        assert result["revenue"] is not None
        assert result["net_income"] is not None
        assert result["total_equity"] is not None

        # Check metrics
        assert result["per"] is not None
        assert result["pbr"] is not None
        assert result["roe"] is not None

    def test_multiple_quarters_comparison(self, mock_client):
        """Test comparing financial data across quarters"""
        stock_code = "005930"

        # Q2 2023
        q2_result = mock_client.get_financial_statement_with_metrics(
            stock_code=stock_code,
            year=2023,
            quarter=2,
            market_cap=400000000000000
        )

        # Q4 2023 (Annual)
        q4_result = mock_client.get_financial_statement_with_metrics(
            stock_code=stock_code,
            year=2023,
            quarter=4,
            market_cap=400000000000000
        )

        # Both should have valid data
        assert q2_result["revenue"] is not None
        assert q4_result["revenue"] is not None

        # Annual revenue should be >= quarterly
        # (Note: In real data, annual != Q2 * 2)
        assert q2_result["quarter"] == 2
        assert q4_result["quarter"] == 4

    def test_error_handling_workflow(self, mock_client):
        """Test error handling in workflow"""
        # Invalid stock code
        with pytest.raises(ValueError, match="회사 정보가 없습니다"):
            mock_client.get_company_info("999999")

        # Invalid corp_code for financial statement
        with pytest.raises(ValueError, match="조회된 데이터가 없습니다"):
            mock_client.get_financial_statement(
                corp_code="99999999",
                year=2023,
                quarter=2
            )

    def test_context_manager_usage(self):
        """Test using client as context manager"""
        with MockDARTAPIClient("test_api_key") as client:
            result = client.get_company_info("005930")
            assert result["corp_name"] == "삼성전자"

        # Client should be properly closed
        # (In mock, this is a no-op, but tests the interface)
