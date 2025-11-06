"""
키움증권 API 클라이언트 (64비트용)
32비트 키움 API 서버와 통신
"""

import socket
import json
import subprocess
import time
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class KiwoomAPIClient:
    """키움 API 클라이언트 (IPC 통신)"""

    def __init__(self, host='localhost', port=7777, auto_start_server=True):
        self.host = host
        self.port = port
        self.socket = None
        self.server_process = None

        if auto_start_server:
            self._start_server()

        self._connect()

    def _start_server(self):
        """32비트 키움 API 서버 시작"""
        # 32비트 Python 경로
        python32_path = r"C:\Python312-32\python.exe"

        if not os.path.exists(python32_path):
            logger.error(f"32비트 Python을 찾을 수 없습니다: {python32_path}")
            raise FileNotFoundError(
                "32비트 Python이 설치되지 않았습니다. "
                "C:\\Python312-32 경로에 Python 3.12 32비트를 설치하세요."
            )

        # 서버 스크립트 경로
        script_path = Path(__file__).parent / "kiwoom_api_server.py"

        logger.info(f"Starting Kiwoom API Server (32-bit)...")

        # 서버 프로세스 시작
        self.server_process = subprocess.Popen(
            [python32_path, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE  # 새 콘솔 창에서 실행
        )

        # 서버 시작 대기
        time.sleep(3)

        logger.info("Kiwoom API Server started")

    def _connect(self):
        """서버에 연결"""
        max_retries = 5
        retry_delay = 1

        for i in range(max_retries):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                logger.info(f"Connected to Kiwoom API Server at {self.host}:{self.port}")
                return
            except ConnectionRefusedError:
                if i < max_retries - 1:
                    logger.info(f"Connection refused, retrying... ({i+1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(
                        "키움 API 서버에 연결할 수 없습니다. "
                        "서버가 실행 중인지 확인하세요."
                    )

    def _send_request(self, request):
        """요청 전송 및 응답 수신"""
        try:
            # 요청 전송
            request_data = json.dumps(request).encode('utf-8')
            self.socket.send(request_data)

            # 응답 수신 (버퍼 크기 증가)
            response_data = self.socket.recv(1024 * 1024)  # 1MB
            response = json.loads(response_data.decode('utf-8'))

            return response

        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    def login(self):
        """키움 로그인"""
        logger.info("Requesting login...")
        response = self._send_request({'cmd': 'login'})

        if response.get('success'):
            logger.info("Login successful")
            return True
        else:
            logger.error(f"Login failed: {response.get('message')}")
            return False

    def logout(self):
        """로그아웃"""
        logger.info("Requesting logout...")
        response = self._send_request({'cmd': 'logout'})

        if response.get('success'):
            logger.info("Logout successful")
        else:
            logger.error(f"Logout failed: {response.get('message')}")

    def get_code_list_by_market(self, market_code):
        """
        시장별 종목 코드 리스트 조회

        Args:
            market_code: '0' (코스피), '10' (코스닥)

        Returns:
            list: 종목 코드 리스트
        """
        response = self._send_request({
            'cmd': 'get_code_list',
            'market_code': market_code
        })

        if response.get('success'):
            return response.get('data', [])
        else:
            logger.error(f"Failed to get code list: {response.get('message')}")
            return []

    def get_master_code_name(self, code):
        """종목명 조회"""
        response = self._send_request({
            'cmd': 'get_code_name',
            'code': code
        })

        if response.get('success'):
            return response.get('data', '')
        else:
            logger.error(f"Failed to get code name: {response.get('message')}")
            return ''

    def get_login_info(self, tag):
        """
        로그인 정보 조회

        Args:
            tag: "ACCOUNT_CNT", "ACCNO", "USER_ID", "USER_NAME" 등

        Returns:
            str: 조회 결과
        """
        response = self._send_request({
            'cmd': 'get_login_info',
            'tag': tag
        })

        if response.get('success'):
            return response.get('data', '')
        else:
            logger.error(f"Failed to get login info: {response.get('message')}")
            return ''

    def get_daily_price(self, code, start_date=None, end_date=None):
        """
        일봉 데이터 조회

        Args:
            code: 종목코드
            start_date: 시작일자 (YYYYMMDD)
            end_date: 종료일자 (YYYYMMDD)

        Returns:
            list: 일봉 데이터 리스트
        """
        response = self._send_request({
            'cmd': 'get_daily_price',
            'code': code,
            'start_date': start_date,
            'end_date': end_date
        })

        if response.get('success'):
            logger.info(f"Retrieved {len(response.get('data', []))} days for {code}")
            return response.get('data', [])
        else:
            logger.error(f"Failed to get daily price: {response.get('message')}")
            return []

    def get_minute_price(self, code, tick=1, count=900):
        """
        분봉 데이터 조회

        Args:
            code: 종목코드
            tick: 분봉 단위 (1, 3, 5, 10, 15, 30, 45, 60)
            count: 조회 개수

        Returns:
            list: 분봉 데이터 리스트
        """
        response = self._send_request({
            'cmd': 'get_minute_price',
            'code': code,
            'tick': tick,
            'count': count
        })

        if response.get('success'):
            logger.info(f"Retrieved {len(response.get('data', []))} minutes for {code}")
            return response.get('data', [])
        else:
            logger.error(f"Failed to get minute price: {response.get('message')}")
            return []

    def ping(self):
        """서버 연결 테스트"""
        response = self._send_request({'cmd': 'ping'})
        return response.get('success', False)

    def close(self):
        """연결 종료"""
        if self.socket:
            self.socket.close()
            logger.info("Connection closed")

        if self.server_process:
            self.server_process.terminate()
            logger.info("Server process terminated")

    def __del__(self):
        """소멸자"""
        self.close()
