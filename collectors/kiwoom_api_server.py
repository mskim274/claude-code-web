"""
키움증권 API 서버 (32비트 전용)
IPC를 통해 메인 프로그램(64비트)과 통신
"""

import sys
import json
import socket
import threading
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KiwoomAPIServer:
    """키움 API 32비트 서버"""

    def __init__(self, host='localhost', port=7777):
        self.host = host
        self.port = port
        self.server_socket = None

        # PyQt5 애플리케이션
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        # 키움 OCX
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        # 이벤트 루프
        self.login_event_loop = None
        self.request_event_loop = None

        # 데이터 저장
        self.tr_data = {}
        self.tr_remained = False
        self.is_connected = False

        # Rate limiting (키움 API 제한: 초당 5회)
        self.last_request_time = 0
        self.request_delay = 0.2  # 200ms (초당 5회)

        # 시그널 연결
        self._connect_signals()

        logger.info("Kiwoom API Server initialized")

    def _connect_signals(self):
        """OCX 시그널 연결"""
        try:
            self.ocx.OnEventConnect.connect(self._on_event_connect)
            self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
            self.ocx.OnReceiveMsg.connect(self._on_receive_msg)
            logger.info("Signals connected successfully")
        except AttributeError as e:
            logger.error(f"Failed to connect signals: {e}")
            logger.error("키움 OpenAPI가 제대로 설치되지 않았을 수 있습니다.")
            raise

    def _on_event_connect(self, err_code):
        """로그인 이벤트"""
        if err_code == 0:
            logger.info("Login successful")
            self.is_connected = True
        else:
            logger.error(f"Login failed: {err_code}")
            self.is_connected = False

        if self.login_event_loop:
            self.login_event_loop.exit()

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next):
        """TR 데이터 수신"""
        logger.debug(f"Received TR: {rqname}")

        self.tr_remained = (prev_next == '2')

        # TR에 따라 데이터 파싱
        if rqname == "주식일봉조회":
            self.tr_data = self._parse_daily_price(trcode)
        elif rqname == "주식분봉조회":
            self.tr_data = self._parse_minute_price(trcode)

        if self.request_event_loop:
            self.request_event_loop.exit()

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신"""
        logger.debug(f"Message: {msg}")

    def _get_comm_data(self, trcode, rqname, index, item_name):
        """TR 데이터 조회"""
        ret = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode, rqname, index, item_name
        )
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        """반복 데이터 개수"""
        return self.ocx.dynamicCall(
            "GetRepeatCnt(QString, QString)",
            trcode, rqname
        )

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

    def login(self):
        """키움 로그인"""
        if self.is_connected:
            return {'success': True, 'message': 'Already logged in'}

        self.login_event_loop = QEventLoop()
        self.ocx.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

        if self.is_connected:
            return {'success': True, 'message': 'Login successful'}
        else:
            return {'success': False, 'message': 'Login failed'}

    def logout(self):
        """로그아웃"""
        try:
            self.ocx.dynamicCall("CommTerminate()")
            self.is_connected = False
            logger.info("Logged out")
            return {'success': True, 'message': 'Logout successful'}
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {'success': False, 'message': str(e)}

    def get_code_list_by_market(self, market_code):
        """시장별 종목 코드 리스트"""
        ret = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = ret.split(';')[:-1]
        return {'success': True, 'data': code_list}

    def get_master_code_name(self, code):
        """종목명 조회"""
        name = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return {'success': True, 'data': name}

    def get_login_info(self, tag):
        """
        로그인 정보 조회

        Args:
            tag: "ACCOUNT_CNT", "ACCNO", "USER_ID", "USER_NAME" 등

        Returns:
            dict: {'success': bool, 'data': str}
        """
        try:
            ret = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
            return {'success': True, 'data': ret}
        except Exception as e:
            logger.error(f"Failed to get login info: {e}")
            return {'success': False, 'data': '', 'message': str(e)}

    def _wait_for_rate_limit(self):
        """Rate limiting 대기"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.request_delay:
            wait_time = self.request_delay - elapsed
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _set_input_value(self, item_name, item_value):
        """TR 입력값 설정"""
        self.ocx.dynamicCall("SetInputValue(QString, QString)", item_name, item_value)

    def _comm_rq_data(self, rqname, trcode, prev_next, screen_no):
        """TR 요청"""
        self._wait_for_rate_limit()

        ret = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            rqname, trcode, prev_next, screen_no
        )

        if ret == 0:
            self.request_event_loop = QEventLoop()
            self.request_event_loop.exec_()
            return True
        else:
            logger.error(f"CommRqData failed: {ret}")
            return False

    def get_daily_price(self, code, start_date=None, end_date=None):
        """
        일봉 데이터 조회

        Args:
            code: 종목코드
            start_date: 시작일자 (YYYYMMDD)
            end_date: 종료일자 (YYYYMMDD)

        Returns:
            dict: {'success': bool, 'data': list, 'message': str}
        """
        try:
            all_data = []
            prev_next = 0

            # 입력값 설정
            self._set_input_value("종목코드", code)
            if end_date:
                self._set_input_value("기준일자", end_date)
            else:
                self._set_input_value("기준일자", "")
            self._set_input_value("수정주가구분", "1")  # 수정주가

            while True:
                # TR 요청
                if not self._comm_rq_data("주식일봉조회", "OPT10081", prev_next, "0101"):
                    break

                # 데이터 수집
                if self.tr_data:
                    all_data.extend(self.tr_data)

                    # 시작일자 조건 확인
                    if start_date and len(all_data) > 0:
                        last_date = all_data[-1].get('일자', '').replace('-', '')
                        if last_date <= start_date:
                            # 시작일자 이전 데이터는 제외
                            all_data = [d for d in all_data if d.get('일자', '').replace('-', '') >= start_date]
                            break

                # 연속 조회 여부 확인
                if not self.tr_remained:
                    break

                prev_next = 2

                # 최대 10년치 데이터 (약 2500일)
                if len(all_data) >= 2500:
                    logger.warning(f"Maximum data limit reached: {len(all_data)} days")
                    break

            logger.info(f"Retrieved {len(all_data)} days of data for {code}")
            return {'success': True, 'data': all_data, 'message': f'{len(all_data)} days retrieved'}

        except Exception as e:
            logger.error(f"Failed to get daily price: {e}")
            return {'success': False, 'data': [], 'message': str(e)}

    def get_minute_price(self, code, tick=1, count=900):
        """
        분봉 데이터 조회

        Args:
            code: 종목코드
            tick: 분봉 단위 (1, 3, 5, 10, 15, 30, 45, 60)
            count: 조회 개수

        Returns:
            dict: {'success': bool, 'data': list, 'message': str}
        """
        try:
            all_data = []
            prev_next = 0

            # 입력값 설정
            self._set_input_value("종목코드", code)
            self._set_input_value("틱범위", str(tick))
            self._set_input_value("수정주가구분", "1")  # 수정주가

            while True:
                # TR 요청
                if not self._comm_rq_data("주식분봉조회", "OPT10080", prev_next, "0102"):
                    break

                # 데이터 수집
                if self.tr_data:
                    all_data.extend(self.tr_data)

                # 요청 개수 도달 여부 확인
                if len(all_data) >= count:
                    all_data = all_data[:count]
                    break

                # 연속 조회 여부 확인
                if not self.tr_remained:
                    break

                prev_next = 2

            logger.info(f"Retrieved {len(all_data)} minutes of data for {code}")
            return {'success': True, 'data': all_data, 'message': f'{len(all_data)} minutes retrieved'}

        except Exception as e:
            logger.error(f"Failed to get minute price: {e}")
            return {'success': False, 'data': [], 'message': str(e)}

    def handle_request(self, request):
        """요청 처리"""
        cmd = request.get('cmd')

        try:
            if cmd == 'login':
                return self.login()
            elif cmd == 'logout':
                return self.logout()
            elif cmd == 'get_code_list':
                market_code = request.get('market_code', '0')
                return self.get_code_list_by_market(market_code)
            elif cmd == 'get_code_name':
                code = request.get('code')
                return self.get_master_code_name(code)
            elif cmd == 'get_login_info':
                tag = request.get('tag')
                return self.get_login_info(tag)
            elif cmd == 'get_daily_price':
                code = request.get('code')
                start_date = request.get('start_date')
                end_date = request.get('end_date')
                return self.get_daily_price(code, start_date, end_date)
            elif cmd == 'get_minute_price':
                code = request.get('code')
                tick = request.get('tick', 1)
                count = request.get('count', 900)
                return self.get_minute_price(code, tick, count)
            elif cmd == 'ping':
                return {'success': True, 'message': 'pong'}
            else:
                return {'success': False, 'message': f'Unknown command: {cmd}'}
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {'success': False, 'message': str(e)}

    def handle_client(self, client_socket):
        """클라이언트 연결 처리"""
        try:
            while True:
                # 요청 수신 (버퍼 크기 증가)
                data = client_socket.recv(1024 * 1024)  # 1MB
                if not data:
                    break

                request = json.loads(data.decode('utf-8'))
                logger.info(f"Request: {request}")

                # 요청 처리
                response = self.handle_request(request)

                # 응답 전송
                response_data = json.dumps(response).encode('utf-8')
                client_socket.send(response_data)

        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            client_socket.close()

    def start_server(self):
        """서버 시작"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        logger.info(f"Kiwoom API Server listening on {self.host}:{self.port}")

        def accept_clients():
            while True:
                try:
                    client_socket, addr = self.server_socket.accept()
                    logger.info(f"Client connected: {addr}")

                    # 각 클라이언트를 별도 스레드에서 처리
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except Exception as e:
                    logger.error(f"Accept error: {e}")
                    break

        # 클라이언트 수락을 별도 스레드에서 실행
        accept_thread = threading.Thread(target=accept_clients)
        accept_thread.daemon = True
        accept_thread.start()

        # PyQt5 이벤트 루프 실행
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    server = KiwoomAPIServer()
    server.start_server()
