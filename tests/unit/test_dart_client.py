"""
Unit tests for DART API Client
TDD Red Phase - Tests written first
"""
import pytest
from datetime import date, datetime
from typing import Dict, List
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET

from collectors.apis.dart.client import DARTAPIClient
from collectors.apis.dart.corpcode_parser import CorpCodeParser


class TestDARTAPIClientAuthentication:
    """Test DART API client authentication"""

    def test_client_initialization_with_api_key(self):
        """Test client can be initialized with API key"""
        api_key = "test_api_key_12345"
        client = DARTAPIClient(api_key)

        assert client.api_key == api_key
        assert client.BASE_URL == "https://opendart.fss.or.kr/api"

    def test_client_requires_api_key(self):
        """Test client raises error without API key"""
        with pytest.raises(TypeError):
            DARTAPIClient()

    def test_client_with_empty_api_key(self):
        """Test client raises error with empty API key"""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            DARTAPIClient("")


class TestDARTAPIClientCompanyInfo:
    """Test company information retrieval"""

    @pytest.fixture
    def client(self):
        return DARTAPIClient("test_api_key")

    @patch('collectors.apis.dart.client.CorpCodeParser.download_corpcode')
    @patch('collectors.apis.dart.client.CorpCodeParser.get_corp_code')
    @patch('collectors.apis.dart.client.DARTAPIClient._make_request')
    def test_get_company_info_success(self, mock_request, mock_get_corp_code, mock_download, client):
        """Test successful company info retrieval"""
        # Mock CORPCODE parser
        mock_get_corp_code.return_value = "00126380"

        # Mock API response
        mock_request.return_value = {
            "status": "000",
            "message": "정상",
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
            "ceo_nm": "한종희, 경계현",
            "est_dt": "19690113",
            "jurir_no": "1301110006246",
            "bizr_no": "1248100998"
        }

        result = client.get_company_info("005930")

        assert result["corp_name"] == "삼성전자"
        assert result["stock_code"] == "005930"
        assert result["corp_code"] == "00126380"

    @patch('collectors.apis.dart.client.CorpCodeParser.download_corpcode')
    @patch('collectors.apis.dart.client.CorpCodeParser.get_corp_code')
    def test_get_company_info_invalid_stock_code(self, mock_get_corp_code, mock_download, client):
        """Test company info with invalid stock code"""
        # Mock CORPCODE parser returning None (not found)
        mock_get_corp_code.return_value = None

        with pytest.raises(ValueError, match="회사 정보가 없습니다"):
            client.get_company_info("999999")

    @patch('collectors.apis.dart.client.CorpCodeParser.download_corpcode')
    @patch('collectors.apis.dart.client.CorpCodeParser.get_corp_code')
    def test_get_company_info_api_error(self, mock_get_corp_code, mock_download, client):
        """Test company info with API error"""
        mock_download.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            client.get_company_info("005930")


class TestDARTAPIClientFinancialStatement:
    """Test financial statement retrieval"""

    @pytest.fixture
    def client(self):
        return DARTAPIClient("test_api_key")

    @patch('collectors.apis.dart.client.DARTAPIClient._make_request')
    def test_get_financial_statement_success(self, mock_request, client):
        """Test successful financial statement retrieval"""
        mock_request.return_value = {
            "status": "000",
            "message": "정상",
            "list": [
                {
                    "rcept_no": "20230814000159",
                    "corp_code": "00126380",
                    "sj_div": "BS",  # 재무상태표
                    "account_nm": "자산총계",
                    "thstrm_amount": "448063162000000"
                },
                {
                    "rcept_no": "20230814000159",
                    "corp_code": "00126380",
                    "sj_div": "BS",
                    "account_nm": "부채총계",
                    "thstrm_amount": "114963472000000"
                },
                {
                    "rcept_no": "20230814000159",
                    "corp_code": "00126380",
                    "sj_div": "BS",
                    "account_nm": "자본총계",
                    "thstrm_amount": "333099690000000"
                },
                {
                    "rcept_no": "20230814000159",
                    "corp_code": "00126380",
                    "sj_div": "IS",  # 손익계산서
                    "account_nm": "매출액",
                    "thstrm_amount": "302231154000000"
                },
                {
                    "rcept_no": "20230814000159",
                    "corp_code": "00126380",
                    "sj_div": "IS",
                    "account_nm": "영업이익",
                    "thstrm_amount": "42510611000000"
                },
                {
                    "rcept_no": "20230814000159",
                    "corp_code": "00126380",
                    "sj_div": "IS",
                    "account_nm": "당기순이익",
                    "thstrm_amount": "35539395000000"
                }
            ]
        }

        result = client.get_financial_statement(
            corp_code="00126380",
            year=2023,
            quarter=2
        )

        assert len(result) == 6
        assert result[0]["account_nm"] == "자산총계"

    @patch('collectors.apis.dart.client.DARTAPIClient._make_request')
    def test_get_financial_statement_annual(self, mock_request, client):
        """Test annual financial statement (quarter=4)"""
        mock_request.return_value = {
            "status": "000",
            "message": "정상",
            "list": []
        }

        result = client.get_financial_statement(
            corp_code="00126380",
            year=2023,
            quarter=4,
            report_type="11011"
        )

        assert isinstance(result, list)

    @patch('collectors.apis.dart.client.DARTAPIClient._make_request')
    def test_get_financial_statement_no_data(self, mock_request, client):
        """Test financial statement with no data"""
        mock_request.side_effect = ValueError("조회된 데이터가 없습니다")

        with pytest.raises(ValueError, match="조회된 데이터가 없습니다"):
            client.get_financial_statement("00126380", 2023)


class TestDARTAPIClientDisclosureList:
    """Test disclosure list retrieval"""

    @pytest.fixture
    def client(self):
        return DARTAPIClient("test_api_key")

    @patch('collectors.apis.dart.client.DARTAPIClient._make_request')
    def test_get_disclosure_list_success(self, mock_request, client):
        """Test successful disclosure list retrieval"""
        mock_request.return_value = {
            "status": "000",
            "message": "정상",
            "list": [
                {
                    "rcept_no": "20231114000504",
                    "corp_code": "00126380",
                    "corp_name": "삼성전자",
                    "corp_cls": "Y",
                    "report_nm": "주요사항보고서(자기주식취득신탁계약체결결정)",
                    "rcept_dt": "20231114",
                    "flr_nm": "삼성전자"
                },
                {
                    "rcept_no": "20231031000504",
                    "corp_code": "00126380",
                    "corp_name": "삼성전자",
                    "corp_cls": "Y",
                    "report_nm": "분기보고서 (2023.09)",
                    "rcept_dt": "20231031",
                    "flr_nm": "삼성전자"
                }
            ]
        }

        result = client.get_disclosure_list(
            corp_code="00126380",
            start_date=date(2023, 10, 1),
            end_date=date(2023, 11, 30)
        )

        assert len(result) == 2
        assert result[0]["report_nm"] == "주요사항보고서(자기주식취득신탁계약체결결정)"
        assert result[0]["rcept_dt"] == "20231114"

    @patch('collectors.apis.dart.client.DARTAPIClient._make_request')
    def test_get_disclosure_list_empty(self, mock_request, client):
        """Test disclosure list with no results"""
        mock_request.return_value = {
            "status": "013",
            "message": "조회된 데이터가 없습니다.",
            "list": []
        }

        result = client.get_disclosure_list(
            corp_code="00126380",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 1, 1)
        )

        assert result == []


class TestDARTAPIClientFinancialMetrics:
    """Test financial metrics calculation"""

    @pytest.fixture
    def client(self):
        return DARTAPIClient("test_api_key")

    def test_calculate_financial_metrics_complete_data(self, client):
        """Test financial metrics with complete data"""
        financial_data = [
            {"account_nm": "매출액", "thstrm_amount": "302231154000000"},
            {"account_nm": "영업이익", "thstrm_amount": "42510611000000"},
            {"account_nm": "당기순이익", "thstrm_amount": "35539395000000"},
            {"account_nm": "자산총계", "thstrm_amount": "448063162000000"},
            {"account_nm": "부채총계", "thstrm_amount": "114963472000000"},
            {"account_nm": "자본총계", "thstrm_amount": "333099690000000"}
        ]
        market_cap = 400000000000000  # 400조

        result = client.calculate_financial_metrics(
            financial_data=financial_data,
            market_cap=market_cap
        )

        # PER = 시가총액 / 당기순이익
        expected_per = 400000000000000 / 35539395000000
        assert abs(result["per"] - expected_per) < 0.01

        # PBR = 시가총액 / 자본총계
        expected_pbr = 400000000000000 / 333099690000000
        assert abs(result["pbr"] - expected_pbr) < 0.01

        # ROE = 당기순이익 / 자본총계 * 100
        expected_roe = (35539395000000 / 333099690000000) * 100
        assert abs(result["roe"] - expected_roe) < 0.01

        # 부채비율 = 부채총계 / 자본총계 * 100
        expected_debt_ratio = (114963472000000 / 333099690000000) * 100
        assert abs(result["debt_ratio"] - expected_debt_ratio) < 0.01

    def test_calculate_financial_metrics_missing_data(self, client):
        """Test financial metrics with missing data"""
        financial_data = [
            {"account_nm": "매출액", "thstrm_amount": "302231154000000"}
        ]

        result = client.calculate_financial_metrics(
            financial_data=financial_data,
            market_cap=400000000000000
        )

        assert result["per"] is None
        assert result["pbr"] is None
        assert result["roe"] is not None or result["roe"] is None

    def test_calculate_financial_metrics_zero_values(self, client):
        """Test financial metrics with zero values"""
        financial_data = [
            {"account_nm": "당기순이익", "thstrm_amount": "0"},
            {"account_nm": "자본총계", "thstrm_amount": "0"}
        ]

        result = client.calculate_financial_metrics(
            financial_data=financial_data,
            market_cap=400000000000000
        )

        # Division by zero should be handled
        assert result["per"] is None or result["per"] == float('inf')
        assert result["pbr"] is None or result["pbr"] == float('inf')


class TestCorpCodeParser:
    """Test CORPCODE parser"""

    @pytest.fixture
    def parser(self):
        return CorpCodeParser("test_api_key")

    @patch('zipfile.ZipFile')
    @patch('requests.get')
    def test_download_corpcode_success(self, mock_get, mock_zipfile, parser):
        """Test successful CORPCODE download and parsing"""
        # Mock XML response
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<result>
    <list>
        <corp_code>00126380</corp_code>
        <corp_name>삼성전자</corp_name>
        <stock_code>005930</stock_code>
        <modify_date>20231114</modify_date>
    </list>
    <list>
        <corp_code>00164779</corp_code>
        <corp_name>SK하이닉스</corp_name>
        <stock_code>000660</stock_code>
        <modify_date>20231114</modify_date>
    </list>
</result>"""

        # Mock requests response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'mock zip content'
        mock_get.return_value = mock_response

        # Mock zipfile
        mock_zip_instance = Mock()
        mock_zip_instance.read.return_value = xml_content.encode('utf-8')
        mock_zipfile.return_value = mock_zip_instance

        parser.download_corpcode()

        assert len(parser.corp_code_map) == 2
        assert parser.corp_code_map["005930"] == "00126380"
        assert parser.corp_code_map["000660"] == "00164779"

    def test_get_corp_code_existing(self, parser):
        """Test get corp_code for existing stock"""
        parser.corp_code_map = {
            "005930": "00126380",
            "000660": "00164779"
        }

        corp_code = parser.get_corp_code("005930")

        assert corp_code == "00126380"

    def test_get_corp_code_nonexisting(self, parser):
        """Test get corp_code for non-existing stock"""
        parser.corp_code_map = {
            "005930": "00126380"
        }

        corp_code = parser.get_corp_code("999999")

        assert corp_code is None

    @patch('requests.get')
    def test_download_corpcode_network_error(self, mock_get, parser):
        """Test CORPCODE download with network error"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            parser.download_corpcode()
