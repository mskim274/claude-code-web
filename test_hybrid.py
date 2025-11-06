"""
하이브리드 아키텍처 테스트
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kiwoom_client():
    """키움 API 클라이언트 테스트"""
    from collectors.kiwoom_api import KiwoomAPI

    logger.info("=== 키움 API 테스트 시작 ===")

    try:
        # API 초기화 (자동으로 32비트 서버 시작)
        api = KiwoomAPI()
        logger.info("✓ API 초기화 완료")

        # Ping 테스트
        if api.client.ping():
            logger.info("✓ Ping 테스트 성공")
        else:
            logger.error("✗ Ping 테스트 실패")
            return False

        # 로그인 테스트 (키움 로그인 창이 뜰 수 있음)
        logger.info("로그인 시도 중...")
        if api.login():
            logger.info("✓ 로그인 성공")

            # 종목 리스트 조회
            logger.info("코스피 종목 리스트 조회 중...")
            codes = api.get_code_list_by_market('0')
            logger.info(f"✓ 코스피 종목 {len(codes)}개 조회 성공")

            if codes:
                # 첫 번째 종목명 조회
                first_code = codes[0]
                name = api.get_master_code_name(first_code)
                logger.info(f"✓ 종목 조회 테스트: {first_code} = {name}")

                # 일봉 데이터 조회 테스트 (최근 100일)
                logger.info(f"\n일봉 데이터 조회 테스트: {first_code} ({name})")
                logger.info("최근 100일 데이터 조회 중...")
                daily_data = api.get_daily_price(first_code)
                if daily_data:
                    logger.info(f"✓ 일봉 데이터 {len(daily_data)}일 조회 성공")
                    logger.info(f"  최근 데이터: {daily_data[0]}")
                    logger.info(f"  가장 오래된 데이터: {daily_data[-1]}")
                else:
                    logger.error("✗ 일봉 데이터 조회 실패")

                # 분봉 데이터 조회 테스트 (5분봉 100개)
                logger.info(f"\n분봉 데이터 조회 테스트: {first_code} ({name})")
                logger.info("5분봉 100개 조회 중...")
                minute_data = api.get_minute_price(first_code, tick=5, count=100)
                if minute_data:
                    logger.info(f"✓ 분봉 데이터 {len(minute_data)}개 조회 성공")
                    logger.info(f"  최근 데이터: {minute_data[0]}")
                    logger.info(f"  가장 오래된 데이터: {minute_data[-1]}")
                else:
                    logger.error("✗ 분봉 데이터 조회 실패")

        else:
            logger.warning("! 로그인 실패 (키움 계정 없을 수 있음)")

        logger.info("=== 테스트 완료 ===")
        return True

    except Exception as e:
        logger.error(f"✗ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_kiwoom_client()
