"""
키움증권 OpenAPI 래퍼 클래스
하이브리드 아키텍처: 64비트 메인 프로그램 + 32비트 API 서버
"""

import logging
from datetime import datetime, timedelta

from collectors.kiwoom_api_client import KiwoomAPIClient

logger = logging.getLogger(__name__)


class KiwoomAPI:
    """키움증권 OpenAPI 래퍼"""

    def __init__(self):
        """키움 API 초기화 (IPC 클라이언트)"""
        # IPC 클라이언트 생성 (자동으로 32비트 서버 시작)
        self.client = KiwoomAPIClient()

        # 로그인 상태
        self.is_connected = False

        logger.info("Kiwoom API initialized (Hybrid Architecture)")

    def login(self):
        """로그인"""
        if self.is_connected:
            logger.info("Already logged in")
            return True

        self.is_connected = self.client.login()
        return self.is_connected

    def logout(self):
        """로그아웃"""
        if self.is_connected:
            self.client.logout()
            self.is_connected = False
            logger.info("Logged out")

    def get_code_list_by_market(self, market_code):
        """
        시장별 종목 코드 리스트 조회

        Args:
            market_code: '0' (코스피), '10' (코스닥)

        Returns:
            list: 종목 코드 리스트
        """
        code_list = self.client.get_code_list_by_market(market_code)
        logger.info(f"Retrieved {len(code_list)} stocks from market {market_code}")
        return code_list

    def get_master_code_name(self, code):
        """종목명 조회"""
        return self.client.get_master_code_name(code)

    def get_login_info(self, tag):
        """
        로그인 정보 조회

        Args:
            tag: "ACCOUNT_CNT", "ACCNO", "USER_ID", "USER_NAME" 등

        Returns:
            str: 조회 결과
        """
        return self.client.get_login_info(tag)

    def get_master_listed_stock_cnt(self, code):
        """상장주식수 조회"""
        # TODO: 서버에 구현 필요
        logger.warning("get_master_listed_stock_cnt not implemented yet")
        return 0

    def get_master_construction(self, code):
        """감리구분 조회"""
        # TODO: 서버에 구현 필요
        logger.warning("get_master_construction not implemented yet")
        return ''

    def get_master_listed_stock_date(self, code):
        """상장일 조회"""
        # TODO: 서버에 구현 필요
        logger.warning("get_master_listed_stock_date not implemented yet")
        return None

    def get_daily_price(self, code, start_date=None, end_date=None):
        """
        일봉 데이터 조회

        Args:
            code: 종목코드
            start_date: 시작일자 (YYYYMMDD)
            end_date: 종료일자 (YYYYMMDD)

        Returns:
            list: 일봉 데이터 리스트 [{'일자', '현재가', '시가', '고가', '저가', '거래량'}, ...]
        """
        data = self.client.get_daily_price(code, start_date, end_date)
        logger.info(f"Retrieved {len(data)} days for {code}")
        return data

    def get_minute_price(self, code, tick=1, count=900):
        """
        분봉 데이터 조회

        Args:
            code: 종목코드
            tick: 분봉 단위 (1, 3, 5, 10, 15, 30, 45, 60)
            count: 조회 개수

        Returns:
            list: 분봉 데이터 리스트 [{'체결시간', '현재가', '시가', '고가', '저가', '거래량'}, ...]
        """
        data = self.client.get_minute_price(code, tick, count)
        logger.info(f"Retrieved {len(data)} minutes for {code}")
        return data

    def get_stock_info(self, code):
        """종목 상세 정보 조회 (TODO: 서버에 구현 필요)"""
        logger.warning("get_stock_info not implemented yet")
        return {}
