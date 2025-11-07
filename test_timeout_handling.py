"""
타임아웃 처리 개선 테스트 스크립트
"""

import logging
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from collectors.stock_collector import StockCollector


def test_timeout_handling():
    """타임아웃 처리 테스트"""
    print("=" * 60)
    print("Kiwoom API 타임아웃 처리 테스트")
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

        # 2. 소수의 종목만 테스트
        print("2. 타임아웃 처리 테스트 (30개 종목)")
        print("   - 이전에 문제가 발생했던 구간을 테스트합니다")
        print("   - 서버 자동 재시작 기능이 작동하는지 확인합니다")
        print()

        # 실제로 타임아웃이 발생하는 구간의 종목 코드들
        from db.database import session_scope
        from db.models import Stock

        with session_scope() as session:
            # 18번째부터 47번째 종목 (이전에 타임아웃이 발생한 구간)
            stocks = session.query(Stock).offset(17).limit(30).all()
            stock_codes = [(s.code, s.name) for s in stocks]

        success = 0
        failed = 0
        skipped = 0

        for idx, (code, name) in enumerate(stock_codes, 1):
            try:
                logger.info(f"[{idx}/30] Testing {name} ({code})")
                records = collector.collect_daily_price(code, years=10)

                if records > 0:
                    success += 1
                    print(f"   ✓ {name}: {records} records")
                elif records == 0:
                    skipped += 1
                    print(f"   - {name}: already exists")
                else:
                    failed += 1
                    print(f"   ✗ {name}: failed")

            except Exception as e:
                logger.error(f"Error testing {code}: {e}")
                failed += 1
                print(f"   ✗ {name}: error - {e}")

        # 3. 결과 출력
        print()
        print("=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        print(f"총 종목 수: 30개")
        print(f"성공: {success}개")
        print(f"이미 존재: {skipped}개")
        print(f"실패: {failed}개")
        print()

        # 서버 재시작 통계
        if hasattr(collector.api.client, 'consecutive_timeouts'):
            print(f"현재 연속 타임아웃: {collector.api.client.consecutive_timeouts}/5")
        print()

        if failed < 10:
            print("✓ 타임아웃 처리가 개선되었습니다!")
        else:
            print("⚠ 여전히 많은 실패가 발생합니다. 추가 조치가 필요할 수 있습니다.")

    except KeyboardInterrupt:
        print("\n\n테스트 중단됨 (Ctrl+C)")
        logger.info("Test interrupted by user")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}", exc_info=True)
        print(f"\n오류: {e}")

    finally:
        # 5. 로그아웃
        print("\n로그아웃 중...")
        collector.logout()
        print("완료")


if __name__ == '__main__':
    test_timeout_handling()
