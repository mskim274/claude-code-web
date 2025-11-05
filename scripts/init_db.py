"""
데이터베이스 초기화 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db
from config.kiwoom_config import KiwoomConfig
from utils.logger import setup_logger

logger = setup_logger('init_db')


def main():
    """데이터베이스 초기화 메인"""
    logger.info("=" * 60)
    logger.info("Initializing Database")
    logger.info("=" * 60)

    # 디렉토리 생성
    KiwoomConfig.ensure_directories()

    try:
        # DB 초기화
        db_manager = init_db()

        logger.info(f"Database URL: {db_manager.db_url}")
        logger.info("All tables created successfully!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
