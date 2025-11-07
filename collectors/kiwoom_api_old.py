"""
키움증권 OpenAPI 래퍼 클래스
PyQt5 기반 키움 OpenAPI+ 연동
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
import logging
from datetime import datetime, timedelta

from utils.rate_limiter import RateLimiter
from config.kiwoom_config import KiwoomConfig

logger = logging.getLogger(__name__)


class KiwoomAPI:
    """키움증권 OpenAPI 래퍼"""

    def __init__(self):
        """키움 API 초기화"""
        # QApplication 생성 (이미 있으면 기존 것 사용)
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        # OCX 생성
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        # 이벤트 루프
        self.login_event_loop = None
        self.request_event_loop = None

        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_calls=5,
            time_window=1.0,
            min_interval=KiwoomConfig.API_DELAY
        )

        # 데이터 저장
        self.tr_data = {}
        self.tr_remained = False

        # 시그널 연결
        self._connect_signals()

        # 로그인 상태
        self.is_connected = False

        logger.info("Kiwoom API initialized")

    def _connect_signals(self):
        """시그널 연결"""
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)

    def _on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            logger.info("Login successful")
            self.is_connected = True
        else:
            logger.error(f"Login failed: {err_code}")
            self.is_connected = False

        if self.login_event_loop:
            self.login_event_loop.exit()

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next):
        """TR 데이터 수신 이벤트"""
        logger.debug(f"Received TR: {rqname}, {trcode}, PrevNext: {prev_next}")

        self.tr_remained = (prev_next == '2')

        # TR에 따라 데이터 파싱
        if rqname == "주식기본정보":
            self.tr_data = self._parse_stock_info(trcode)
        elif rqname == "주식일봉조회":
            self.tr_data = self._parse_daily_price(trcode)
        elif rqname == "주식분봉조회":
            self.tr_data = self._parse_minute_price(trcode)
        elif rqname == "투자자별매매":
            self.tr_data = self._parse_investor_trading(trcode)
        elif rqname == "종목코드목록":
            self.tr_data = self._parse_stock_list(trcode)

        if self.request_event_loop:
            self.request_event_loop.exit()

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신 이벤트"""
        logger.debug(f"Message: {msg}")

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신 (실시간)"""
        pass

    def login(self):
        """로그인"""
        if self.is_connected:
            logger.info("Already logged in")
            return True

        self.login_event_loop = QEventLoop()
        self.ocx.dynamicCall("CommConnect()")

        # 로그인 대기
        self.login_event_loop.exec_()

        return self.is_connected

    def logout(self):
        """로그아웃"""
        self.ocx.dynamicCall("CommTerminate()")
        self.is_connected = False
        logger.info("Logged out")

    def get_login_info(self, tag):
        """
        로그인 정보 조회

        Args:
            tag: "ACCOUNT_CNT", "ACCNO", "USER_ID", "USER_NAME" 등

        Returns:
            str: 조회 결과
        """
        ret = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def _request(self, trcode, rqname, screen_no, input_data):
        """
        TR 요청 (내부 메서드)

        Args:
            trcode: TR 코드
            rqname: 요청 이름
            screen_no: 화면 번호
            input_data: 입력 데이터 dict

        Returns:
            dict: 응답 데이터
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()

        # 입력값 설정
        for key, value in input_data.items():
            self.ocx.dynamicCall("SetInputValue(QString, QString)", key, value)

        # 요청
        self.request_event_loop = QEventLoop()
        ret = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            rqname, trcode, 0, screen_no
        )

        if ret != 0:
            logger.error(f"Request failed: {ret}")
            return None

        # 응답 대기
        self.request_event_loop.exec_()

        return self.tr_data

    def get_code_list_by_market(self, market_code):
        """
        시장별 종목 코드 리스트 조회

        Args:
            market_code: '0' (코스피), '10' (코스닥)

        Returns:
            list: 종목 코드 리스트
        """
        ret = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = ret.split(';')[:-1]  # 마지막 빈 값 제거
        logger.info(f"Retrieved {len(code_list)} stocks from market {market_code}")
        return code_list

    def get_master_code_name(self, code):
        """종목명 조회"""
        return self.ocx.dynamicCall("GetMasterCodeName(QString)", code)

    def get_master_listed_stock_cnt(self, code):
        """상장주식수 조회"""
        return self.ocx.dynamicCall("GetMasterListedStockCnt(QString)", code)

    def get_master_construction(self, code):
        """감리구분 조회"""
        return self.ocx.dynamicCall("GetMasterConstruction(QString)", code)

    def get_master_listed_stock_date(self, code):
        """상장일 조회"""
        date_str = self.ocx.dynamicCall("GetMasterListedStockDate(QString)", code)
        if date_str:
            return datetime.strptime(date_str, '%Y%m%d').date()
        return None

    def _get_comm_data(self, trcode, rqname, index, item_name):
        """
        TR 데이터 조회

        Args:
            trcode: TR 코드
            rqname: 요청 이름
            index: 인덱스
            item_name: 항목명

        Returns:
            str: 데이터 (strip 처리됨)
        """
        ret = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode, rqname, index, item_name
        )
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        """반복 데이터 개수 조회"""
        return self.ocx.dynamicCall(
            "GetRepeatCnt(QString, QString)",
            trcode, rqname
        )

    def _parse_stock_list(self, trcode):
        """종목 리스트 파싱"""
        # GetCodeListByMarket 사용하므로 이 메서드는 사용하지 않음
        return {}

    def _parse_stock_info(self, trcode):
        """주식 기본 정보 파싱"""
        data = {}
        data['종목코드'] = self._get_comm_data(trcode, "주식기본정보", 0, "종목코드")
        data['종목명'] = self._get_comm_data(trcode, "주식기본정보", 0, "종목명")
        data['시가총액'] = self._get_comm_data(trcode, "주식기본정보", 0, "시가총액")
        data['상장주식수'] = self._get_comm_data(trcode, "주식기본정보", 0, "상장주식")
        data['PER'] = self._get_comm_data(trcode, "주식기본정보", 0, "PER")
        data['PBR'] = self._get_comm_data(trcode, "주식기본정보", 0, "PBR")
        data['EPS'] = self._get_comm_data(trcode, "주식기본정보", 0, "EPS")
        data['BPS'] = self._get_comm_data(trcode, "주식기본정보", 0, "BPS")
        return data

    def _parse_daily_price(self, trcode):
        """일봉 데이터 파싱"""
        data_list = []
        cnt = self._get_repeat_cnt(trcode, "주식일봉조회")

        for i in range(cnt):
            data = {
                '일자': self._get_comm_data(trcode, "주식일봉조회", i, "일자"),
                '현재가': self._get_comm_data(trcode, "주식일봉조회", i, "현재가"),
                '시가': self._get_comm_data(trcode, "주식일봉조회", i, "시가"),
                '고가': self._get_comm_data(trcode, "주식일봉조회", i, "고가"),
                '저가': self._get_comm_data(trcode, "주식일봉조회", i, "저가"),
                '거래량': self._get_comm_data(trcode, "주식일봉조회", i, "거래량"),
                '거래대금': self._get_comm_data(trcode, "주식일봉조회", i, "거래대금"),
            }
            data_list.append(data)

        return data_list

    def _parse_minute_price(self, trcode):
        """분봉 데이터 파싱"""
        data_list = []
        cnt = self._get_repeat_cnt(trcode, "주식분봉조회")

        for i in range(cnt):
            data = {
                '체결시간': self._get_comm_data(trcode, "주식분봉조회", i, "체결시간"),
                '현재가': self._get_comm_data(trcode, "주식분봉조회", i, "현재가"),
                '시가': self._get_comm_data(trcode, "주식분봉조회", i, "시가"),
                '고가': self._get_comm_data(trcode, "주식분봉조회", i, "고가"),
                '저가': self._get_comm_data(trcode, "주식분봉조회", i, "저가"),
                '거래량': self._get_comm_data(trcode, "주식분봉조회", i, "거래량"),
            }
            data_list.append(data)

        return data_list

    def _parse_investor_trading(self, trcode):
        """투자자별 매매 동향 파싱"""
        data_list = []
        cnt = self._get_repeat_cnt(trcode, "투자자별매매")

        for i in range(cnt):
            data = {
                '일자': self._get_comm_data(trcode, "투자자별매매", i, "일자"),
                '기관순매수': self._get_comm_data(trcode, "투자자별매매", i, "기관순매수"),
                '외국인순매수': self._get_comm_data(trcode, "투자자별매매", i, "외국인순매수"),
                '개인순매수': self._get_comm_data(trcode, "투자자별매매", i, "개인순매수"),
            }
            data_list.append(data)

        return data_list

    def get_daily_price(self, code, start_date=None, end_date=None):
        """
        일봉 데이터 조회

        Args:
            code: 종목 코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            list: 일봉 데이터 리스트
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        input_data = {
            '종목코드': code,
            '기준일자': end_date,
            '수정주가구분': '1'  # 1: 수정주가
        }

        all_data = []
        while True:
            data = self._request('OPT10081', '주식일봉조회', '0101', input_data)

            if not data:
                break

            all_data.extend(data)

            # 연속 조회 체크
            if not self.tr_remained:
                break

            # 시작일 체크
            if start_date and data[-1]['일자'] <= start_date:
                break

            # 다음 요청을 위해 기준일 업데이트
            input_data['기준일자'] = data[-1]['일자']

        return all_data

    def get_minute_price(self, code, tick=1, count=900):
        """
        분봉 데이터 조회

        Args:
            code: 종목 코드
            tick: 분봉 주기 (1, 5, 10, 30, 60)
            count: 조회 개수

        Returns:
            list: 분봉 데이터 리스트
        """
        input_data = {
            '종목코드': code,
            '틱범위': str(tick),
            '수정주가구분': '1'
        }

        data = self._request('OPT10080', '주식분봉조회', '0102', input_data)
        return data or []

    def get_stock_info(self, code):
        """
        종목 상세 정보 조회

        Args:
            code: 종목 코드

        Returns:
            dict: 종목 정보
        """
        input_data = {'종목코드': code}
        data = self._request('OPT10001', '주식기본정보', '0103', input_data)
        return data or {}

    def run(self):
        """이벤트 루프 실행"""
        self.app.exec_()

    def quit(self):
        """애플리케이션 종료"""
        self.app.quit()
