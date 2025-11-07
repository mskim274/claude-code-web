"""
분봉/틱 데이터 수집 테스트 스크립트
"""

import logging
from collectors.stock_collector import StockCollector
from config.kiwoom_config import KiwoomConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_minute_price_single_stock():
    """단일 종목 분봉 데이터 수집 테스트"""
    logger.info("=== 단일 종목 분봉 데이터 수집 테스트 ===")

    collector = StockCollector()

    try:
        # 로그인
        if not collector.login():
            logger.error("로그인 실패")
            return

        # 테스트 종목: 삼성전자 (005930)
        test_code = "005930"

        # 60분봉 데이터 수집 (100개)
        logger.info(f"60분봉 데이터 수집 시작: {test_code}")
        result = collector.collect_minute_price(test_code, interval=60, count=100)
        logger.info(f"60분봉 수집 완료: {result}개 레코드")

        # 10분봉 데이터 수집 (100개)
        logger.info(f"10분봉 데이터 수집 시작: {test_code}")
        result = collector.collect_minute_price(test_code, interval=10, count=100)
        logger.info(f"10분봉 수집 완료: {result}개 레코드")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
    finally:
        collector.logout()
        logger.info("로그아웃 완료")


def test_tick_data_single_stock():
    """단일 종목 틱 데이터 수집 테스트"""
    logger.info("=== 단일 종목 틱 데이터 수집 테스트 ===")

    collector = StockCollector()

    try:
        # 로그인
        if not collector.login():
            logger.error("로그인 실패")
            return

        # 테스트 종목: 삼성전자 (005930)
        test_code = "005930"

        # 틱 데이터 수집 (최대 600틱)
        logger.info(f"틱 데이터 수집 시작: {test_code}")
        result = collector.collect_tick_data(test_code, count=600)
        logger.info(f"틱 데이터 수집 완료: {result}개 레코드")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
    finally:
        collector.logout()
        logger.info("로그아웃 완료")


def test_minute_price_multiple_stocks():
    """다중 종목 분봉 데이터 수집 테스트"""
    logger.info("=== 다중 종목 분봉 데이터 수집 테스트 ===")

    collector = StockCollector()

    try:
        # 로그인
        if not collector.login():
            logger.error("로그인 실패")
            return

        # 테스트 종목 (코스피 대표 5개)
        test_stocks = ["005930", "000660", "035420", "005380", "051910"]  # 삼성전자, SK하이닉스, 네이버, 현대차, LG화학

        # 60분봉, 30분봉, 10분봉만 수집 (각 100개)
        logger.info(f"다중 종목 분봉 수집 시작 (60, 30, 10분)")
        result = collector.collect_all_minute_prices(
            intervals=[60, 30, 10],
            count=100,
            stock_codes=test_stocks
        )
        logger.info(f"수집 통계: {result}")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
    finally:
        collector.logout()
        logger.info("로그아웃 완료")


def test_tick_data_multiple_stocks():
    """다중 종목 틱 데이터 수집 테스트"""
    logger.info("=== 다중 종목 틱 데이터 수집 테스트 ===")

    collector = StockCollector()

    try:
        # 로그인
        if not collector.login():
            logger.error("로그인 실패")
            return

        # 테스트 종목 (코스피 대표 5개)
        test_stocks = ["005930", "000660", "035420", "005380", "051910"]

        # 틱 데이터 수집
        logger.info(f"다중 종목 틱 데이터 수집 시작")
        result = collector.collect_all_tick_data(
            count=600,
            stock_codes=test_stocks
        )
        logger.info(f"수집 통계: {result}")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
    finally:
        collector.logout()
        logger.info("로그아웃 완료")


def main():
    """메인 실행 함수"""
    print("""
    ========================================
    분봉/틱 데이터 수집 테스트
    ========================================

    테스트 메뉴:
    1. 단일 종목 분봉 데이터 수집 (삼성전자)
    2. 단일 종목 틱 데이터 수집 (삼성전자)
    3. 다중 종목 분봉 데이터 수집 (대표 5개 종목)
    4. 다중 종목 틱 데이터 수집 (대표 5개 종목)
    5. 전체 테스트 실행
    0. 종료

    ========================================
    """)

    while True:
        choice = input("선택: ").strip()

        if choice == "1":
            test_minute_price_single_stock()
        elif choice == "2":
            test_tick_data_single_stock()
        elif choice == "3":
            test_minute_price_multiple_stocks()
        elif choice == "4":
            test_tick_data_multiple_stocks()
        elif choice == "5":
            logger.info("전체 테스트 시작...")
            test_minute_price_single_stock()
            test_tick_data_single_stock()
            test_minute_price_multiple_stocks()
            test_tick_data_multiple_stocks()
            logger.info("전체 테스트 완료")
        elif choice == "0":
            logger.info("프로그램 종료")
            break
        else:
            print("잘못된 선택입니다. 다시 선택해주세요.")


if __name__ == "__main__":
    main()
