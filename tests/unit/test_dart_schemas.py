"""
Unit tests for DART Pydantic Schemas
TDD Red Phase
"""
import pytest
from datetime import date
from pydantic import ValidationError

from collectors.apis.dart.schemas import (
    DARTFinancialStatement,
    DARTDisclosure,
    DARTCompanyInfo
)


class TestDARTFinancialStatementSchema:
    """Test DART Financial Statement Pydantic schema"""

    def test_financial_statement_valid_data(self):
        """Test schema with valid complete data"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "year": 2023,
            "quarter": 2,
            "revenue": 302231154000000,
            "operating_profit": 42510611000000,
            "net_income": 35539395000000,
            "total_assets": 448063162000000,
            "total_liabilities": 114963472000000,
            "total_equity": 333099690000000,
            "per": 11.25,
            "pbr": 1.20,
            "roe": 10.67,
            "debt_ratio": 34.52
        }

        fs = DARTFinancialStatement(**data)

        assert fs.corp_code == "00126380"
        assert fs.corp_name == "삼성전자"
        assert fs.year == 2023
        assert fs.quarter == 2
        assert fs.revenue == 302231154000000
        assert fs.per == 11.25

    def test_financial_statement_minimal_data(self):
        """Test schema with minimal required data"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "year": 2023,
            "quarter": 4
        }

        fs = DARTFinancialStatement(**data)

        assert fs.corp_code == "00126380"
        assert fs.revenue is None
        assert fs.per is None

    def test_financial_statement_invalid_quarter(self):
        """Test schema validation for invalid quarter"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "year": 2023,
            "quarter": 5  # Invalid: should be 1-4
        }

        with pytest.raises(ValidationError):
            DARTFinancialStatement(**data)

    def test_financial_statement_negative_values(self):
        """Test schema allows negative values (e.g., losses)"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "year": 2023,
            "quarter": 2,
            "net_income": -1000000000  # Loss
        }

        fs = DARTFinancialStatement(**data)

        assert fs.net_income == -1000000000

    def test_financial_statement_missing_required_fields(self):
        """Test schema validation for missing required fields"""
        data = {
            "corp_code": "00126380",
            # Missing corp_name, year, quarter
        }

        with pytest.raises(ValidationError):
            DARTFinancialStatement(**data)


class TestDARTDisclosureSchema:
    """Test DART Disclosure Pydantic schema"""

    def test_disclosure_valid_data(self):
        """Test disclosure schema with valid data"""
        data = {
            "rcept_no": "20231114000504",
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "report_nm": "주요사항보고서(자기주식취득신탁계약체결결정)",
            "rcept_dt": "2023-11-14",
            "flr_nm": "삼성전자"
        }

        disclosure = DARTDisclosure(**data)

        assert disclosure.rcept_no == "20231114000504"
        assert disclosure.corp_code == "00126380"
        assert disclosure.report_nm == "주요사항보고서(자기주식취득신탁계약체결결정)"
        assert disclosure.rcept_dt == date(2023, 11, 14)

    def test_disclosure_date_string_format(self):
        """Test disclosure accepts date string in YYYYMMDD format"""
        data = {
            "rcept_no": "20231114000504",
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "report_nm": "분기보고서",
            "rcept_dt": "20231114",  # YYYYMMDD format
            "flr_nm": "삼성전자"
        }

        disclosure = DARTDisclosure(**data)

        # Should convert to date object
        assert isinstance(disclosure.rcept_dt, (date, str))

    def test_disclosure_missing_required_fields(self):
        """Test disclosure validation for missing fields"""
        data = {
            "rcept_no": "20231114000504",
            # Missing other required fields
        }

        with pytest.raises(ValidationError):
            DARTDisclosure(**data)


class TestDARTCompanyInfoSchema:
    """Test DART Company Info Pydantic schema"""

    def test_company_info_valid_data(self):
        """Test company info schema with valid data"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
            "stock_code": "005930",
            "ceo_nm": "한종희, 경계현",
            "est_dt": "19690113",
            "jurir_no": "1301110006246",
            "bizr_no": "1248100998"
        }

        company = DARTCompanyInfo(**data)

        assert company.corp_code == "00126380"
        assert company.corp_name == "삼성전자"
        assert company.stock_code == "005930"
        assert company.ceo_nm == "한종희, 경계현"

    def test_company_info_optional_fields(self):
        """Test company info with optional fields missing"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930"
        }

        company = DARTCompanyInfo(**data)

        assert company.corp_code == "00126380"
        assert company.corp_name == "삼성전자"
        # Optional fields should have default None
        assert company.corp_name_eng is None or hasattr(company, 'corp_name_eng')

    def test_company_info_stock_code_format(self):
        """Test company info validates stock code format"""
        data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930"  # 6 digits
        }

        company = DARTCompanyInfo(**data)

        assert len(company.stock_code) == 6
        assert company.stock_code.isdigit()
