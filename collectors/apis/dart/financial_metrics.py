"""
Financial Metrics Calculator
재무 지표 계산 모듈
"""
from typing import Dict, Optional


class FinancialMetricsCalculator:
    """
    재무 지표 계산 클래스
    Calculates financial metrics like PER, PBR, ROE, etc.
    """

    @staticmethod
    def calculate_per(market_cap: float, net_income: float) -> Optional[float]:
        """
        PER (Price Earnings Ratio) 계산
        주가수익비율 = 시가총액 / 당기순이익

        Args:
            market_cap: 시가총액
            net_income: 당기순이익

        Returns:
            PER 값, 계산 불가능하면 None
        """
        if net_income is None or net_income == 0:
            return None
        if net_income < 0:  # 적자인 경우
            return None

        try:
            per = market_cap / net_income
            return round(per, 2)
        except (ZeroDivisionError, TypeError):
            return None

    @staticmethod
    def calculate_pbr(market_cap: float, total_equity: float) -> Optional[float]:
        """
        PBR (Price to Book Ratio) 계산
        주가순자산비율 = 시가총액 / 자본총계

        Args:
            market_cap: 시가총액
            total_equity: 자본총계

        Returns:
            PBR 값, 계산 불가능하면 None
        """
        if total_equity is None or total_equity == 0:
            return None

        try:
            pbr = market_cap / total_equity
            return round(pbr, 2)
        except (ZeroDivisionError, TypeError):
            return None

    @staticmethod
    def calculate_roe(net_income: float, total_equity: float) -> Optional[float]:
        """
        ROE (Return on Equity) 계산
        자기자본이익률 = (당기순이익 / 자본총계) * 100

        Args:
            net_income: 당기순이익
            total_equity: 자본총계

        Returns:
            ROE (%), 계산 불가능하면 None
        """
        if total_equity is None or total_equity == 0:
            return None
        if net_income is None:
            return None

        try:
            roe = (net_income / total_equity) * 100
            return round(roe, 2)
        except (ZeroDivisionError, TypeError):
            return None

    @staticmethod
    def calculate_debt_ratio(total_liabilities: float, total_equity: float) -> Optional[float]:
        """
        부채비율 계산
        부채비율 = (부채총계 / 자본총계) * 100

        Args:
            total_liabilities: 부채총계
            total_equity: 자본총계

        Returns:
            부채비율 (%), 계산 불가능하면 None
        """
        if total_equity is None or total_equity == 0:
            return None
        if total_liabilities is None:
            return None

        try:
            debt_ratio = (total_liabilities / total_equity) * 100
            return round(debt_ratio, 2)
        except (ZeroDivisionError, TypeError):
            return None

    @staticmethod
    def calculate_operating_margin(operating_profit: float, revenue: float) -> Optional[float]:
        """
        영업이익률 계산
        영업이익률 = (영업이익 / 매출액) * 100

        Args:
            operating_profit: 영업이익
            revenue: 매출액

        Returns:
            영업이익률 (%), 계산 불가능하면 None
        """
        if revenue is None or revenue == 0:
            return None
        if operating_profit is None:
            return None

        try:
            operating_margin = (operating_profit / revenue) * 100
            return round(operating_margin, 2)
        except (ZeroDivisionError, TypeError):
            return None

    @staticmethod
    def calculate_net_margin(net_income: float, revenue: float) -> Optional[float]:
        """
        순이익률 계산
        순이익률 = (당기순이익 / 매출액) * 100

        Args:
            net_income: 당기순이익
            revenue: 매출액

        Returns:
            순이익률 (%), 계산 불가능하면 None
        """
        if revenue is None or revenue == 0:
            return None
        if net_income is None:
            return None

        try:
            net_margin = (net_income / revenue) * 100
            return round(net_margin, 2)
        except (ZeroDivisionError, TypeError):
            return None

    def calculate_all_metrics(
        self,
        financial_data: Dict[str, float],
        market_cap: float
    ) -> Dict[str, Optional[float]]:
        """
        모든 재무 지표를 한 번에 계산

        Args:
            financial_data: 재무 데이터 딕셔너리
                - revenue: 매출액
                - operating_profit: 영업이익
                - net_income: 당기순이익
                - total_assets: 자산총계
                - total_liabilities: 부채총계
                - total_equity: 자본총계
            market_cap: 시가총액

        Returns:
            계산된 모든 지표를 포함한 딕셔너리
        """
        revenue = financial_data.get("revenue")
        operating_profit = financial_data.get("operating_profit")
        net_income = financial_data.get("net_income")
        total_assets = financial_data.get("total_assets")
        total_liabilities = financial_data.get("total_liabilities")
        total_equity = financial_data.get("total_equity")

        return {
            "per": self.calculate_per(market_cap, net_income),
            "pbr": self.calculate_pbr(market_cap, total_equity),
            "roe": self.calculate_roe(net_income, total_equity),
            "debt_ratio": self.calculate_debt_ratio(total_liabilities, total_equity),
            "operating_margin": self.calculate_operating_margin(operating_profit, revenue),
            "net_margin": self.calculate_net_margin(net_income, revenue)
        }


def extract_financial_values(financial_items: list) -> Dict[str, Optional[int]]:
    """
    DART API 응답에서 재무 수치 추출

    Args:
        financial_items: DART API 재무제표 항목 리스트

    Returns:
        추출된 재무 수치 딕셔너리
    """
    result = {
        "revenue": None,
        "operating_profit": None,
        "net_income": None,
        "total_assets": None,
        "total_liabilities": None,
        "total_equity": None
    }

    # 계정명 매핑
    account_mapping = {
        "매출액": "revenue",
        "수익(매출액)": "revenue",
        "영업이익": "operating_profit",
        "영업이익(손실)": "operating_profit",
        "당기순이익": "net_income",
        "당기순이익(손실)": "net_income",
        "자산총계": "total_assets",
        "부채총계": "total_liabilities",
        "자본총계": "total_equity"
    }

    for item in financial_items:
        account_nm = item.get("account_nm", "")
        thstrm_amount = item.get("thstrm_amount")

        if account_nm in account_mapping:
            key = account_mapping[account_nm]
            try:
                # 문자열을 정수로 변환 (천원 단위)
                if thstrm_amount:
                    result[key] = int(thstrm_amount.replace(",", ""))
            except (ValueError, AttributeError):
                pass

    return result
