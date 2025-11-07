"""
데이터베이스 마이그레이션 스크립트
TickPrice 테이블 추가
"""

import logging
from db.database import engine
from db.models import Base

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    try:
        logger.info("데이터베이스 마이그레이션 시작...")

        # 모든 테이블 생성 (이미 존재하는 테이블은 무시됨)
        Base.metadata.create_all(engine)

        logger.info("데이터베이스 마이그레이션 완료!")
        logger.info("새로 추가된 테이블: tick_prices")

        # 테이블 목록 출력
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"현재 데이터베이스 테이블 목록: {tables}")

    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    print("""
    ========================================
    데이터베이스 마이그레이션
    ========================================

    이 스크립트는 TickPrice 테이블을 추가합니다.
    기존 테이블은 영향을 받지 않습니다.

    계속하시겠습니까? (y/n): """, end="")

    choice = input().strip().lower()

    if choice == 'y':
        migrate_database()
    else:
        print("마이그레이션이 취소되었습니다.")
