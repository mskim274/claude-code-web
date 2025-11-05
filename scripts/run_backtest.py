"""
백테스트 실행 스크립트
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.engine import BacktestEngine
from backtest.strategy import MovingAverageCrossStrategy
from db.database import init_db
from utils.logger import setup_logger

logger = setup_logger('run_backtest')


def main():
    """백테스트 실행 메인"""
    parser = argparse.ArgumentParser(description='Run backtest on stock data')
    parser.add_argument('--code', type=str, required=True, help='Stock code (e.g., 005930 for Samsung)')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD, default: 1 year ago)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD, default: today)')
    parser.add_argument('--capital', type=int, default=10000000, help='Initial capital (default: 10,000,000 KRW)')
    parser.add_argument('--short-ma', type=int, default=20, help='Short MA period (default: 20)')
    parser.add_argument('--long-ma', type=int, default=60, help='Long MA period (default: 60)')

    args = parser.parse_args()

    # 날짜 파싱
    if args.end:
        end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
    else:
        end_date = datetime.now().date()

    if args.start:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=365)

    logger.info("=" * 60)
    logger.info("Starting Backtest")
    logger.info("=" * 60)
    logger.info(f"Stock Code: {args.code}")
    logger.info(f"Period: {start_date} ~ {end_date}")
    logger.info(f"Initial Capital: {args.capital:,} KRW")
    logger.info(f"Strategy: Moving Average Cross ({args.short_ma}/{args.long_ma})")
    logger.info("=" * 60)

    # DB 초기화
    init_db()

    try:
        # 전략 생성
        strategy = MovingAverageCrossStrategy(
            short_window=args.short_ma,
            long_window=args.long_ma
        )

        # 백테스트 엔진 생성
        engine = BacktestEngine(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=args.capital
        )

        # 백테스트 실행
        results = engine.run(args.code)

        if results is None:
            logger.error("Backtest failed!")
            return 1

        # 결과 출력
        engine.print_summary()

        # 거래 내역 출력 (최근 10개)
        trades_df = engine.get_trades_df()
        if trades_df is not None and len(trades_df) > 0:
            print("\nRecent Trades (Last 10):")
            print("-" * 80)
            print(trades_df.tail(10).to_string(index=False))
            print("-" * 80)

        # 자산 곡선 정보
        equity_df = engine.get_equity_curve()
        if equity_df is not None:
            print("\nEquity Curve Statistics:")
            print("-" * 60)
            print(f"Starting Value: {equity_df['portfolio_value'].iloc[0]:,.0f} KRW")
            print(f"Ending Value: {equity_df['portfolio_value'].iloc[-1]:,.0f} KRW")
            print(f"Peak Value: {equity_df['portfolio_value'].max():,.0f} KRW")
            print(f"Lowest Value: {equity_df['portfolio_value'].min():,.0f} KRW")
            print("-" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
