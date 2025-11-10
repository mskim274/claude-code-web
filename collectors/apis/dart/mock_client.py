"""
Mock DART API Client
테스트용 Mock 클라이언트
"""
from datetime import date
from typing import Dict, List, Optional


class MockDARTAPIClient:
    """
    테스트용 Mock DART API 클라이언트
    실제 API 호출 없이 테스트 데이터 반환
    """

    BASE_URL = "https://opendart.fss.or.kr/api"

    # Mock 데이터
    MOCK_COMPANIES = {
        "005930": {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
            "stock_code": "005930",
            "ceo_nm": "한종희, 경계현",
            "est_dt": "19690113",
            "jurir_no": "1301110006246",
            "bizr_no": "1248100998"
        },
        "000660": {
            "corp_code": "00164779",
            "corp_name": "SK하이닉스",
            "corp_name_eng": "SK hynix Inc.",
            "stock_code": "000660",
            "ceo_nm": "곽노정",
            "est_dt": "19830211",
            "jurir_no": "1301110067246",
            "bizr_no": "1248100111"
        }
    }

    MOCK_FINANCIAL_STATEMENTS = {
        "00126380": {
            2023: {
                2: [
                    {"account_nm": "자산총계", "thstrm_amount": "448063162000000", "sj_div": "BS"},
                    {"account_nm": "부채총계", "thstrm_amount": "114963472000000", "sj_div": "BS"},
                    {"account_nm": "자본총계", "thstrm_amount": "333099690000000", "sj_div": "BS"},
                    {"account_nm": "매출액", "thstrm_amount": "302231154000000", "sj_div": "IS"},
                    {"account_nm": "영업이익", "thstrm_amount": "42510611000000", "sj_div": "IS"},
                    {"account_nm": "당기순이익", "thstrm_amount": "35539395000000", "sj_div": "IS"}
                ],
                4: [
                    {"account_nm": "자산총계", "thstrm_amount": "426793908000000", "sj_div": "BS"},
                    {"account_nm": "부채총계", "thstrm_amount": "102088234000000", "sj_div": "BS"},
                    {"account_nm": "자본총계", "thstrm_amount": "324705674000000", "sj_div": "BS"},
                    {"account_nm": "매출액", "thstrm_amount": "302231000000000", "sj_div": "IS"},
                    {"account_nm": "영업이익", "thstrm_amount": "43376000000000", "sj_div": "IS"},
                    {"account_nm": "당기순이익", "thstrm_amount": "55338000000000", "sj_div": "IS"}
                ]
            }
        }
    }

    MOCK_DISCLOSURES = {
        "00126380": [
            {
                "rcept_no": "20231114000504",
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "report_nm": "주요사항보고서(자기주식취득신탁계약체결결정)",
                "rcept_dt": "20231114",
                "flr_nm": "삼성전자"
            },
            {
                "rcept_no": "20231031000504",
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "report_nm": "분기보고서 (2023.09)",
                "rcept_dt": "20231031",
                "flr_nm": "삼성전자"
            }
        ]
    }

    def __init__(self, api_key: str):
        """
        Args:
            api_key: DART API 인증키 (Mock에서는 검증만)
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        self.api_key = api_key
        self.corp_code_map = {
            "005930": "00126380",
            "000660": "00164779"
        }

    def get_company_info(self, stock_code: str) -> Dict:
        """
        기업 기본정보 조회 (Mock)

        Args:
            stock_code: 종목코드

        Returns:
            기업 정보

        Raises:
            ValueError: 종목코드가 없을 때
        """
        if stock_code not in self.MOCK_COMPANIES:
            raise ValueError(f"회사 정보가 없습니다 (종목코드: {stock_code})")

        return self.MOCK_COMPANIES[stock_code].copy()

    def get_financial_statement(
        self,
        corp_code: str,
        year: int,
        quarter: int = 4,
        report_type: str = "11011"
    ) -> List[Dict]:
        """
        재무제표 조회 (Mock)

        Args:
            corp_code: 고유번호
            year: 사업연도
            quarter: 분기
            report_type: 보고서 코드

        Returns:
            재무제표 항목 리스트

        Raises:
            ValueError: 데이터가 없을 때
        """
        if corp_code not in self.MOCK_FINANCIAL_STATEMENTS:
            raise ValueError("조회된 데이터가 없습니다")

        corp_data = self.MOCK_FINANCIAL_STATEMENTS[corp_code]

        if year not in corp_data:
            raise ValueError("조회된 데이터가 없습니다")

        if quarter not in corp_data[year]:
            raise ValueError("조회된 데이터가 없습니다")

        return [item.copy() for item in corp_data[year][quarter]]

    def get_disclosure_list(
        self,
        corp_code: str,
        start_date: date,
        end_date: date,
        page_count: int = 100
    ) -> List[Dict]:
        """
        공시 목록 조회 (Mock)

        Args:
            corp_code: 고유번호
            start_date: 시작일
            end_date: 종료일
            page_count: 페이지당 건수

        Returns:
            공시 목록
        """
        if corp_code not in self.MOCK_DISCLOSURES:
            return []

        disclosures = self.MOCK_DISCLOSURES[corp_code]

        # 날짜 필터링
        filtered = []
        for disclosure in disclosures:
            disclosure_date_str = disclosure["rcept_dt"]
            disclosure_date = date(
                int(disclosure_date_str[:4]),
                int(disclosure_date_str[4:6]),
                int(disclosure_date_str[6:8])
            )

            if start_date <= disclosure_date <= end_date:
                filtered.append(disclosure.copy())

        return filtered

    def calculate_financial_metrics(
        self,
        financial_data: List[Dict],
        market_cap: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        재무 지표 계산 (Mock)

        Args:
            financial_data: 재무제표 항목 리스트
            market_cap: 시가총액

        Returns:
            계산된 재무 지표
        """
        from collectors.apis.dart.financial_metrics import (
            FinancialMetricsCalculator,
            extract_financial_values
        )

        calculator = FinancialMetricsCalculator()
        financial_values = extract_financial_values(financial_data)

        if market_cap:
            return calculator.calculate_all_metrics(financial_values, market_cap)
        else:
            return {
                "per": None,
                "pbr": None,
                "roe": calculator.calculate_roe(
                    financial_values.get("net_income"),
                    financial_values.get("total_equity")
                ),
                "debt_ratio": calculator.calculate_debt_ratio(
                    financial_values.get("total_liabilities"),
                    financial_values.get("total_equity")
                ),
                "operating_margin": calculator.calculate_operating_margin(
                    financial_values.get("operating_profit"),
                    financial_values.get("revenue")
                ),
                "net_margin": calculator.calculate_net_margin(
                    financial_values.get("net_income"),
                    financial_values.get("revenue")
                )
            }

    def get_financial_statement_with_metrics(
        self,
        stock_code: str,
        year: int,
        quarter: int = 4,
        market_cap: Optional[float] = None
    ) -> Dict:
        """
        재무제표 조회 및 지표 계산 (Mock)

        Args:
            stock_code: 종목코드
            year: 사업연도
            quarter: 분기
            market_cap: 시가총액

        Returns:
            재무제표 + 지표
        """
        # 종목코드 → 고유번호
        corp_code = self.corp_code_map.get(stock_code)
        if not corp_code:
            raise ValueError(f"회사 정보가 없습니다 (종목코드: {stock_code})")

        company_info = self.get_company_info(stock_code)
        corp_name = company_info["corp_name"]

        # 재무제표 조회
        financial_data = self.get_financial_statement(
            corp_code=corp_code,
            year=year,
            quarter=quarter
        )

        # 재무 지표 계산
        metrics = self.calculate_financial_metrics(financial_data, market_cap)

        # 재무 수치 추출
        from collectors.apis.dart.financial_metrics import extract_financial_values
        financial_values = extract_financial_values(financial_data)

        return {
            "corp_code": corp_code,
            "corp_name": corp_name,
            "stock_code": stock_code,
            "year": year,
            "quarter": quarter,
            **financial_values,
            **metrics
        }

    def close(self):
        """세션 종료 (Mock에서는 무동작)"""
        pass

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()
