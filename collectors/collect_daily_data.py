"""
전체 종목 일봉 데이터 수집 스크립트
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from collectors.stock_collector import StockCollector


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("키움증권 주식 데이터 수집 시스템")
    print("=" * 60)
    print()

    collector = StockCollector()

    try:
        # 1. 로그인
        print("1. 키움 API 로그인 중...")
        if not collector.login():
            logger.error("로그인 실패")
            return

        user_id = collector.api.get_login_info("USER_ID")
        user_name = collector.api.get_login_info("USER_NAME")
        print(f"   ✓ 로그인 성공: {user_name} ({user_id})")
        print()

        # 2. 수집 설정
        years = 10  # 수집 기간
        print(f"2. 수집 설정")
        print(f"   - 수집 기간: {years}년")
        print()

        # 3. 전체 종목 일봉 데이터 수집
        print(f"3. 전체 종목 일봉 데이터 수집 시작...")
        print(f"   경고: 이 작업은 2-3일이 소요될 수 있습니다!")
        print()

        stats = collector.collect_all_daily_prices(years=years)

        # 4. 결과 출력
        print()
        print("=" * 60)
        print("수집 완료!")
        print("=" * 60)
        print(f"총 종목 수: {stats.get('total', 0):,}개")
        print(f"새로 수집: {stats.get('success', 0):,}개")
        print(f"이미 있음: {stats.get('skipped', 0):,}개")
        print(f"수집 실패: {stats.get('failed', 0):,}개")
        print(f"총 데이터: {stats.get('total_records', 0):,}개")
        print()

    except KeyboardInterrupt:
        print("\n\n수집 중단됨 (Ctrl+C)")
        logger.info("Collection interrupted by user")

    except Exception as e:
        logger.error(f"수집 중 오류 발생: {e}", exc_info=True)
        print(f"\n오류: {e}")

    finally:
        # 5. 로그아웃
        print("로그아웃 중...")
        collector.logout()
        print("완료")


if __name__ == '__main__':
    main()
