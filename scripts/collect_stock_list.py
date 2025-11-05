"""
전체 종목 리스트 수집 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.stock_collector import StockCollector
from db.database import init_db
from utils.logger import setup_logger
from config.kiwoom_config import KiwoomConfig

logger = setup_logger('collect_stock_list')


def main():
    """종목 리스트 수집 메인"""
    logger.info("=" * 60)
    logger.info("Starting Stock List Collection")
    logger.info("=" * 60)

    # 디렉토리 생성
    KiwoomConfig.ensure_directories()

    # DB 초기화
    logger.info("Initializing database...")
    init_db()

    # 수집기 생성
    collector = StockCollector()

    try:
        # 로그인
        logger.info("Logging in to Kiwoom API...")
        if not collector.login():
            logger.error("Login failed!")
            return 1

        # 종목 리스트 수집
        logger.info("Collecting stock list...")
        count = collector.collect_all_stock_list()

        logger.info(f"Successfully collected {count} stocks")
        logger.info("=" * 60)
        logger.info("Stock List Collection Completed!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    finally:
        # 로그아웃
        collector.logout()


if __name__ == '__main__':
    sys.exit(main())
