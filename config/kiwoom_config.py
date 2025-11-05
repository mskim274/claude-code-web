"""
키움증권 API 및 프로젝트 설정
"""

import os
from pathlib import Path

class KiwoomConfig:
    """키움증권 API 및 데이터 수집 설정"""

    # 프로젝트 루트 경로
    BASE_DIR = Path(__file__).parent.parent

    # 데이터베이스 설정
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # sqlite, postgresql
    DB_PATH = BASE_DIR / 'data' / 'stock_data.db'  # SQLite 경로

    # PostgreSQL 설정 (사용시)
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'stock_backtest')

    @classmethod
    def get_db_url(cls):
        """데이터베이스 연결 URL 반환"""
        if cls.DB_TYPE == 'sqlite':
            cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            return f'sqlite:///{cls.DB_PATH}'
        elif cls.DB_TYPE == 'postgresql':
            return (f'postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}'
                   f'@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}')
        else:
            raise ValueError(f"Unsupported DB_TYPE: {cls.DB_TYPE}")

    # 키움 API 설정
    API_DELAY = 0.2  # API 호출 간 지연 시간 (초) - 초당 5회 제한
    REQUEST_TIMEOUT = 30  # 요청 타임아웃 (초)

    # 데이터 수집 설정
    YEARS_TO_COLLECT = 5  # 수집할 과거 데이터 연수
    BATCH_SIZE = 100  # 배치 커밋 크기
    MAX_RETRIES = 3  # 실패시 재시도 횟수

    # 시장 구분
    MARKETS = {
        '0': 'KOSPI',
        '10': 'KOSDAQ',
        '3': 'ELW',
        '8': 'ETF',
        '50': 'KONEX'
    }

    # 수집할 시장 (기본: 코스피, 코스닥)
    TARGET_MARKETS = ['0', '10']

    # 로그 설정
    LOG_DIR = BASE_DIR / 'logs'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # 데이터 저장 경로
    DATA_DIR = BASE_DIR / 'data'
    BACKUP_DIR = DATA_DIR / 'backup'

    # TR 코드 정의
    TR_CODES = {
        'stock_list': 'OPT10001',  # 주식기본정보요청
        'daily_price': 'OPT10081',  # 주식일봉차트조회요청
        'minute_price': 'OPT10080',  # 주식분봉차트조회요청
        'investor_trading': 'OPT10059',  # 투자자별매매동향요청
        'stock_info': 'OPT10001',  # 주식기본정보
    }

    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
