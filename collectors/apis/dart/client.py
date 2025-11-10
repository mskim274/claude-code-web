"""
DART OpenAPI Client
전자공시시스템 OpenAPI 클라이언트
"""
import requests
from datetime import date
from typing import Dict, List, Optional
import logging

from collectors.apis.dart.corpcode_parser import CorpCodeParser
from collectors.apis.dart.financial_metrics import FinancialMetricsCalculator, extract_financial_values

logger = logging.getLogger(__name__)


class DARTAPIClient:
    """
    DART OpenAPI 클라이언트
    https://opendart.fss.or.kr/
    """

    BASE_URL = "https://opendart.fss.or.kr/api"

    def __init__(self, api_key: str):
        """
        Args:
            api_key: DART API 인증키

        Raises:
            ValueError: API key가 비어있을 때
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        self.api_key = api_key
        self.session = requests.Session()
        self.corpcode_parser = CorpCodeParser(api_key)
        self.metrics_calculator = FinancialMetricsCalculator()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        DART API 요청 실행

        Args:
            endpoint: API 엔드포인트
            params: 요청 파라미터

        Returns:
            API 응답 (JSON)

        Raises:
            Exception: API 요청 실패 시
            ValueError: API 응답에 오류가 있을 때
        """
        if params is None:
            params = {}

        # API Key 추가
        params["crtfc_key"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # API 상태 코드 확인
            status = data.get("status")
            message = data.get("message", "")

            if status != "000":
                # 013: 조회된 데이터가 없습니다 (빈 결과)
                if status == "013":
                    if "list" in endpoint or "disclosure" in endpoint.lower():
                        return {"status": status, "message": message, "list": []}
                    else:
                        raise ValueError(message)
                else:
                    raise ValueError(f"{message} (status: {status})")

            return data

        except requests.RequestException as e:
            logger.error(f"DART API 요청 실패: {e}")
            raise

    def get_company_info(self, stock_code: str) -> Dict:
        """
        기업 기본정보 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            기업 정보 딕셔너리

        Raises:
            ValueError: 기업 정보가 없을 때
        """
        # 종목코드 → 고유번호 변환
        if not self.corpcode_parser.is_loaded():
            self.corpcode_parser.download_corpcode()

        corp_code = self.corpcode_parser.get_corp_code(stock_code)
        if not corp_code:
            raise ValueError(f"회사 정보가 없습니다 (종목코드: {stock_code})")

        params = {"corp_code": corp_code}
        data = self._make_request("company.json", params)

        # stock_code 추가
        data["stock_code"] = stock_code

        return data

    def get_financial_statement(
        self,
        corp_code: str,
        year: int,
        quarter: int = 4,
        report_type: str = "11011"
    ) -> List[Dict]:
        """
        재무제표 조회

        Args:
            corp_code: 고유번호 (8자리)
            year: 사업연도 (4자리)
            quarter: 분기 (1~4), 4=연간
            report_type: 보고서 코드
                - 11011: 사업보고서
                - 11012: 반기보고서
                - 11013: 1분기보고서
                - 11014: 3분기보고서

        Returns:
            재무제표 항목 리스트

        Raises:
            ValueError: 조회된 데이터가 없을 때
        """
        # 분기별 보고서 코드 매핑
        if report_type == "11011":
            if quarter == 1:
                report_code = "11013"
            elif quarter == 2:
                report_code = "11012"
            elif quarter == 3:
                report_code = "11014"
            else:  # quarter == 4
                report_code = "11011"
        else:
            report_code = report_type

        params = {
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": report_code
        }

        data = self._make_request("fnlttSinglAcntAll.json", params)

        return data.get("list", [])

    def get_disclosure_list(
        self,
        corp_code: str,
        start_date: date,
        end_date: date,
        page_count: int = 100
    ) -> List[Dict]:
        """
        공시 목록 조회

        Args:
            corp_code: 고유번호 (8자리)
            start_date: 시작일
            end_date: 종료일
            page_count: 페이지당 건수 (최대 100)

        Returns:
            공시 목록 리스트
        """
        params = {
            "corp_code": corp_code,
            "bgn_de": start_date.strftime("%Y%m%d"),
            "end_de": end_date.strftime("%Y%m%d"),
            "page_count": str(page_count)
        }

        data = self._make_request("list.json", params)

        return data.get("list", [])

    def calculate_financial_metrics(
        self,
        financial_data: List[Dict],
        market_cap: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        재무 지표 계산

        Args:
            financial_data: DART API 재무제표 항목 리스트
            market_cap: 시가총액 (선택)

        Returns:
            계산된 재무 지표 딕셔너리
                - per: PER (주가수익비율)
                - pbr: PBR (주가순자산비율)
                - roe: ROE (자기자본이익률)
                - debt_ratio: 부채비율
                - operating_margin: 영업이익률
                - net_margin: 순이익률
        """
        # 재무 수치 추출
        financial_values = extract_financial_values(financial_data)

        # 재무 지표 계산
        if market_cap:
            metrics = self.metrics_calculator.calculate_all_metrics(
                financial_values,
                market_cap
            )
        else:
            # 시가총액 없이 계산 가능한 지표만
            metrics = {
                "per": None,
                "pbr": None,
                "roe": self.metrics_calculator.calculate_roe(
                    financial_values.get("net_income"),
                    financial_values.get("total_equity")
                ),
                "debt_ratio": self.metrics_calculator.calculate_debt_ratio(
                    financial_values.get("total_liabilities"),
                    financial_values.get("total_equity")
                ),
                "operating_margin": self.metrics_calculator.calculate_operating_margin(
                    financial_values.get("operating_profit"),
                    financial_values.get("revenue")
                ),
                "net_margin": self.metrics_calculator.calculate_net_margin(
                    financial_values.get("net_income"),
                    financial_values.get("revenue")
                )
            }

        return metrics

    def get_financial_statement_with_metrics(
        self,
        stock_code: str,
        year: int,
        quarter: int = 4,
        market_cap: Optional[float] = None
    ) -> Dict:
        """
        재무제표 조회 및 지표 계산 (통합 메서드)

        Args:
            stock_code: 종목코드 (6자리)
            year: 사업연도
            quarter: 분기 (1~4)
            market_cap: 시가총액 (선택)

        Returns:
            재무제표 데이터 + 계산된 지표
        """
        # 종목코드 → 고유번호
        if not self.corpcode_parser.is_loaded():
            self.corpcode_parser.download_corpcode()

        corp_code = self.corpcode_parser.get_corp_code(stock_code)
        if not corp_code:
            raise ValueError(f"회사 정보가 없습니다 (종목코드: {stock_code})")

        corp_name = self.corpcode_parser.get_corp_name(stock_code)

        # 재무제표 조회
        financial_data = self.get_financial_statement(
            corp_code=corp_code,
            year=year,
            quarter=quarter
        )

        # 재무 지표 계산
        metrics = self.calculate_financial_metrics(financial_data, market_cap)

        # 재무 수치 추출
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
        """세션 종료"""
        self.session.close()

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()
