"""
Mock API implementations for testing without external dependencies.

These mocks simulate KIS, DART, and Kiwoom APIs for testing purposes.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random


class MockKiwoomAPI:
    """Mock Kiwoom API for testing"""

    def __init__(self, fail: bool = False):
        """
        Args:
            fail: If True, simulate API failures
        """
        self.fail = fail
        self.connected = not fail
        self._call_count = 0

    def connect(self) -> bool:
        """Simulate connection"""
        if self.fail:
            return False
        self.connected = True
        return True

    def get_stock_price(self, code: str) -> Dict[str, Any]:
        """
        Get current stock price

        Args:
            code: Stock code (e.g., "005930" for Samsung)

        Returns:
            Stock price data in Kiwoom format
        """
        self._call_count += 1

        if self.fail:
            raise ConnectionError("Kiwoom API connection failed")

        # Generate realistic mock data based on stock code
        base_price = int(code) % 100000 + 10000

        return {
            "code": code,
            "name": self._get_stock_name(code),
            "current_price": base_price,
            "open_price": base_price - 500,
            "high_price": base_price + 1000,
            "low_price": base_price - 1000,
            "volume": random.randint(100000, 10000000),
            "trading_value": base_price * random.randint(100000, 10000000),
            "change_rate": round(random.uniform(-5.0, 5.0), 2),
            "change_price": random.randint(-2000, 2000),
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        }

    def get_stock_info(self, code: str) -> Dict[str, Any]:
        """Get stock information"""
        self._call_count += 1

        if self.fail:
            raise ConnectionError("Kiwoom API connection failed")

        return {
            "code": code,
            "name": self._get_stock_name(code),
            "market": "KOSPI" if code < "100000" else "KOSDAQ",
            "sector": "IT",
            "shares": random.randint(1000000, 1000000000),
            "market_cap": random.randint(1000000000, 100000000000),
        }

    def get_historical_price(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get historical price data"""
        self._call_count += 1

        if self.fail:
            raise ConnectionError("Kiwoom API connection failed")

        # Generate mock historical data
        base_price = int(code) % 100000 + 10000
        data = []

        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")

        current = start
        while current <= end:
            # Skip weekends
            if current.weekday() < 5:
                price_variation = random.randint(-1000, 1000)
                data.append({
                    "date": current.strftime("%Y%m%d"),
                    "open": base_price + price_variation,
                    "high": base_price + price_variation + 500,
                    "low": base_price + price_variation - 500,
                    "close": base_price + price_variation + 100,
                    "volume": random.randint(100000, 10000000),
                })
            current += timedelta(days=1)

        return data

    @staticmethod
    def _get_stock_name(code: str) -> str:
        """Get mock stock name based on code"""
        stock_names = {
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "035720": "카카오",
            "035420": "NAVER",
            "051910": "LG화학",
        }
        return stock_names.get(code, f"종목{code}")

    def get_call_count(self) -> int:
        """Get number of API calls made"""
        return self._call_count


class MockKISAPI:
    """Mock KIS (Korea Investment & Securities) API for testing"""

    def __init__(self, fail: bool = False):
        """
        Args:
            fail: If True, simulate API failures
        """
        self.fail = fail
        self.access_token = None if fail else "mock_token_12345"
        self._call_count = 0

    def authenticate(self) -> bool:
        """Simulate authentication"""
        if self.fail:
            return False
        self.access_token = "mock_token_12345"
        return True

    def get_stock_price(self, code: str) -> Dict[str, Any]:
        """
        Get domestic stock price

        Args:
            code: Stock code

        Returns:
            Stock price data in KIS format
        """
        self._call_count += 1

        if self.fail or not self.access_token:
            raise ConnectionError("KIS API authentication failed")

        base_price = int(code) % 100000 + 10000

        return {
            "output": {
                "stck_prpr": str(base_price),  # 현재가
                "stck_oprc": str(base_price - 500),  # 시가
                "stck_hgpr": str(base_price + 1000),  # 고가
                "stck_lwpr": str(base_price - 1000),  # 저가
                "acml_vol": str(random.randint(100000, 10000000)),  # 거래량
                "prdy_vrss": str(random.randint(-2000, 2000)),  # 전일대비
                "prdy_ctrt": str(round(random.uniform(-5.0, 5.0), 2)),  # 전일대비율
            },
            "rt_cd": "0",  # Success code
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
        }

    def get_overseas_stock_price(
        self,
        symbol: str,
        exchange: str = "NASDAQ"
    ) -> Dict[str, Any]:
        """
        Get overseas stock price

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            exchange: Exchange code (NASDAQ, NYSE, etc.)

        Returns:
            Overseas stock price data
        """
        self._call_count += 1

        if self.fail or not self.access_token:
            raise ConnectionError("KIS API authentication failed")

        # Generate mock price based on symbol hash
        base_price = hash(symbol) % 500 + 50

        return {
            "output": {
                "last": str(base_price),  # 현재가
                "open": str(base_price - 2),  # 시가
                "high": str(base_price + 5),  # 고가
                "low": str(base_price - 5),  # 저가
                "tvol": str(random.randint(1000000, 100000000)),  # 거래량
                "tamt": str(random.randint(1000000000, 10000000000)),  # 거래대금
                "diff": str(round(random.uniform(-5.0, 5.0), 2)),  # 전일대비
                "rate": str(round(random.uniform(-3.0, 3.0), 2)),  # 등락률
            },
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
        }

    def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        self._call_count += 1

        if self.fail or not self.access_token:
            raise ConnectionError("KIS API authentication failed")

        return {
            "output1": [
                {
                    "pdno": "005930",  # 종목코드
                    "prdt_name": "삼성전자",  # 종목명
                    "hldg_qty": "100",  # 보유수량
                    "pchs_avg_pric": "70000",  # 매입평균가
                    "prpr": "75000",  # 현재가
                    "evlu_pfls_amt": "500000",  # 평가손익
                }
            ],
            "output2": {
                "tot_evlu_amt": "7500000",  # 총평가금액
                "pchs_amt_smtl": "7000000",  # 매입금액합계
                "evlu_pfls_smtl": "500000",  # 평가손익합계
            },
            "rt_cd": "0",
        }

    def get_call_count(self) -> int:
        """Get number of API calls made"""
        return self._call_count


class MockDARTAPI:
    """Mock DART (Data Analysis, Retrieval and Transfer) API for testing"""

    def __init__(self, fail: bool = False):
        """
        Args:
            fail: If True, simulate API failures
        """
        self.fail = fail
        self.api_key = None if fail else "mock_dart_key_12345"
        self._call_count = 0

    def get_financial_statement(
        self,
        corp_code: str,
        year: int,
        quarter: int = 4,
        report_type: str = "11011"
    ) -> Dict[str, Any]:
        """
        Get financial statement

        Args:
            corp_code: Corporation code
            year: Year
            quarter: Quarter (1-4)
            report_type: Report type code

        Returns:
            Financial statement data
        """
        self._call_count += 1

        if self.fail:
            raise ConnectionError("DART API connection failed")

        # Generate realistic financial data
        base_revenue = random.randint(1000000, 100000000)

        return {
            "status": "000",
            "message": "정상",
            "list": [
                {
                    "rcept_no": f"{year}{quarter}001",
                    "reprt_code": report_type,
                    "bsns_year": str(year),
                    "corp_code": corp_code,
                    "sj_div": "BS",  # 재무상태표
                    "account_nm": "자산총계",
                    "thstrm_amount": str(base_revenue * 3),
                },
                {
                    "rcept_no": f"{year}{quarter}001",
                    "reprt_code": report_type,
                    "bsns_year": str(year),
                    "corp_code": corp_code,
                    "sj_div": "BS",
                    "account_nm": "부채총계",
                    "thstrm_amount": str(base_revenue),
                },
                {
                    "rcept_no": f"{year}{quarter}001",
                    "reprt_code": report_type,
                    "bsns_year": str(year),
                    "corp_code": corp_code,
                    "sj_div": "BS",
                    "account_nm": "자본총계",
                    "thstrm_amount": str(base_revenue * 2),
                },
                {
                    "rcept_no": f"{year}{quarter}001",
                    "reprt_code": report_type,
                    "bsns_year": str(year),
                    "corp_code": corp_code,
                    "sj_div": "IS",  # 손익계산서
                    "account_nm": "매출액",
                    "thstrm_amount": str(base_revenue),
                },
                {
                    "rcept_no": f"{year}{quarter}001",
                    "reprt_code": report_type,
                    "bsns_year": str(year),
                    "corp_code": corp_code,
                    "sj_div": "IS",
                    "account_nm": "영업이익",
                    "thstrm_amount": str(int(base_revenue * 0.15)),
                },
                {
                    "rcept_no": f"{year}{quarter}001",
                    "reprt_code": report_type,
                    "bsns_year": str(year),
                    "corp_code": corp_code,
                    "sj_div": "IS",
                    "account_nm": "당기순이익",
                    "thstrm_amount": str(int(base_revenue * 0.1)),
                },
            ]
        }

    def get_company_info(self, corp_code: str) -> Dict[str, Any]:
        """Get company information"""
        self._call_count += 1

        if self.fail:
            raise ConnectionError("DART API connection failed")

        return {
            "status": "000",
            "message": "정상",
            "corp_code": corp_code,
            "corp_name": f"주식회사{corp_code[:3]}",
            "corp_name_eng": f"Company{corp_code[:3]}",
            "stock_name": f"종목{corp_code[:3]}",
            "stock_code": corp_code[:6],
            "ceo_nm": "홍길동",
            "corp_cls": "Y",  # 유가증권시장
            "jurir_no": "1234567890123",
            "bizr_no": "123-45-67890",
            "adres": "서울특별시 강남구",
            "hm_url": "http://www.example.com",
            "ir_url": "http://ir.example.com",
            "phn_no": "02-1234-5678",
            "fax_no": "02-1234-5679",
            "induty_code": "264",
            "est_dt": "19900101",
            "acc_mt": "12",
        }

    def search_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Search company by name"""
        self._call_count += 1

        if self.fail:
            raise ConnectionError("DART API connection failed")

        # Generate mock search results
        return [
            {
                "corp_code": f"{i:08d}",
                "corp_name": f"{company_name}{i}",
                "stock_code": f"{i:06d}",
                "modify_date": "20240101",
            }
            for i in range(1, 4)
        ]

    def get_call_count(self) -> int:
        """Get number of API calls made"""
        return self._call_count


class MockAPIFactory:
    """Factory for creating mock APIs with consistent configurations"""

    @staticmethod
    def create_kiwoom(fail: bool = False) -> MockKiwoomAPI:
        """Create mock Kiwoom API"""
        return MockKiwoomAPI(fail=fail)

    @staticmethod
    def create_kis(fail: bool = False) -> MockKISAPI:
        """Create mock KIS API"""
        api = MockKISAPI(fail=fail)
        if not fail:
            api.authenticate()
        return api

    @staticmethod
    def create_dart(fail: bool = False) -> MockDARTAPI:
        """Create mock DART API"""
        return MockDARTAPI(fail=fail)

    @staticmethod
    def create_all(
        kiwoom_fail: bool = False,
        kis_fail: bool = False,
        dart_fail: bool = False
    ) -> Dict[str, Any]:
        """Create all mock APIs"""
        return {
            "kiwoom": MockAPIFactory.create_kiwoom(kiwoom_fail),
            "kis": MockAPIFactory.create_kis(kis_fail),
            "dart": MockAPIFactory.create_dart(dart_fail),
        }
