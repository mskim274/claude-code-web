"""
전체 종목 일봉 데이터 수집 스크립트
"""

import sys
import os
import argparse

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.stock_collector import StockCollector
from db.database import init_db
from utils.logger import setup_logger
from config.kiwoom_config import KiwoomConfig

logger = setup_logger('collect_daily_prices')


def main():
    """일봉 데이터 수집 메인"""
    parser = argparse.ArgumentParser(description='Collect daily price data for all stocks')
    parser.add_argument('--years', type=int, default=5, help='Years of historical data to collect (default: 5)')
    parser.add_argument('--code', type=str, help='Specific stock code to collect (optional)')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting Daily Price Collection")
    logger.info(f"Years: {args.years}")
    if args.code:
        logger.info(f"Target: Single stock ({args.code})")
    else:
        logger.info("Target: All stocks")
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

        if args.code:
            # 특정 종목만 수집
            logger.info(f"Collecting data for {args.code}...")
            records = collector.collect_daily_price(args.code, years=args.years)
            logger.info(f"Collected {records} records for {args.code}")
        else:
            # 전체 종목 수집
            logger.info("Collecting data for all stocks...")
            logger.info("This may take several hours. Please wait...")

            stats = collector.collect_all_daily_prices(years=args.years)

            logger.info("=" * 60)
            logger.info("Collection Statistics:")
            logger.info(f"  Total stocks: {stats['total']}")
            logger.info(f"  Successful: {stats['success']}")
            logger.info(f"  Failed: {stats['failed']}")
            logger.info("=" * 60)

        logger.info("Daily Price Collection Completed!")
        return 0

    except KeyboardInterrupt:
        logger.warning("Collection interrupted by user")
        return 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    finally:
        # 로그아웃
        collector.logout()


if __name__ == '__main__':
    sys.exit(main())
