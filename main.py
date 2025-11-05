"""
메인 실행 파일 - 대화형 메뉴
"""

import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collectors.stock_collector import StockCollector
from backtest.engine import BacktestEngine
from backtest.strategy import MovingAverageCrossStrategy
from db.database import init_db, session_scope
from db.models import Stock
from utils.logger import setup_logger


from config.kiwoom_config import KiwoomConfig

logger = setup_logger('main')


def print_menu():
    """메뉴 출력"""
    print("\n" + "=" * 60)
    print("키움증권 API 백테스팅 시스템")
    print("=" * 60)
    print("1. 데이터베이스 초기화")
    print("2. 종목 리스트 수집")
    print("3. 일봉 데이터 수집 (전체)")
    print("4. 일봉 데이터 수집 (특정 종목)")
    print("5. 최신 데이터 업데이트")
    print("6. 백테스트 실행")
    print("7. 종목 통계 보기")
    print("0. 종료")
    print("=" * 60)


def init_database():
    """데이터베이스 초기화"""
    print("\n[데이터베이스 초기화]")
    try:
        KiwoomConfig.ensure_directories()
        db_manager = init_db()
        print(f"✓ 데이터베이스 초기화 완료: {db_manager.db_url}")
    except Exception as e:
        print(f"✗ 오류 발생: {e}")


def collect_stocks():
    """종목 리스트 수집"""
    print("\n[종목 리스트 수집]")
    collector = StockCollector()

    try:
        print("키움 API 로그인 중...")
        if not collector.login():
            print("✗ 로그인 실패")
            return

        print("종목 리스트 수집 중...")
        count = collector.collect_all_stock_list()
        print(f"✓ {count}개 종목 수집 완료")

    except Exception as e:
        print(f"✗ 오류 발생: {e}")
    finally:
        collector.logout()


def collect_all_prices():
    """전체 종목 일봉 수집"""
    print("\n[전체 종목 일봉 데이터 수집]")
    years = input("수집할 연도 (기본: 5년): ").strip()
    years = int(years) if years else 5

    print(f"\n⚠ 경고: 전체 종목 {years}년치 데이터 수집은 2-3일 소요됩니다!")
    confirm = input("계속하시겠습니까? (y/N): ").strip().lower()

    if confirm != 'y':
        print("취소되었습니다.")
        return

    collector = StockCollector()

    try:
        print("키움 API 로그인 중...")
        if not collector.login():
            print("✗ 로그인 실패")
            return

        print(f"데이터 수집 시작 ({years}년)...")
        stats = collector.collect_all_daily_prices(years=years)

        print(f"\n✓ 수집 완료!")
        print(f"  성공: {stats['success']}")
        print(f"  실패: {stats['failed']}")
        print(f"  총합: {stats['total']}")

    except KeyboardInterrupt:
        print("\n\n⚠ 사용자가 중단했습니다. 수집된 데이터는 DB에 저장되었습니다.")
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
    finally:
        collector.logout()


def collect_single_price():
    """특정 종목 일봉 수집"""
    print("\n[특정 종목 일봉 데이터 수집]")
    stock_code = input("종목 코드 (예: 005930): ").strip()
    years = input("수집할 연도 (기본: 5년): ").strip()
    years = int(years) if years else 5

    if not stock_code:
        print("✗ 종목 코드를 입력해주세요.")
        return

    collector = StockCollector()

    try:
        print("키움 API 로그인 중...")
        if not collector.login():
            print("✗ 로그인 실패")
            return

        print(f"{stock_code} 데이터 수집 중 ({years}년)...")
        records = collector.collect_daily_price(stock_code, years=years)

        if records > 0:
            print(f"✓ {records}개 레코드 수집 완료")
        else:
            print("✗ 데이터를 수집하지 못했습니다.")

    except Exception as e:
        print(f"✗ 오류 발생: {e}")
    finally:
        collector.logout()


def update_latest():
    """최신 데이터 업데이트"""
    print("\n[최신 데이터 업데이트]")
    collector = StockCollector()

    try:
        print("키움 API 로그인 중...")
        if not collector.login():
            print("✗ 로그인 실패")
            return

        print("최신 데이터 업데이트 중...")
        updated = collector.update_latest_prices()
        print(f"✓ {updated}개 종목 업데이트 완료")

    except Exception as e:
        print(f"✗ 오류 발생: {e}")
    finally:
        collector.logout()


def run_backtest():
    """백테스트 실행"""
    print("\n[백테스트 실행]")

    stock_code = input("종목 코드 (예: 005930): ").strip()
    if not stock_code:
        print("✗ 종목 코드를 입력해주세요.")
        return

    # 기본값: 1년 전 ~ 오늘
    default_start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    default_end = datetime.now().strftime('%Y-%m-%d')

    start_date = input(f"시작일 (기본: {default_start}): ").strip() or default_start
    end_date = input(f"종료일 (기본: {default_end}): ").strip() or default_end
    capital = input("초기 자본금 (기본: 10,000,000원): ").strip()
    capital = int(capital) if capital else 10000000

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        print("\n백테스트 실행 중...")

        # 전략 생성 (이동평균 교차 전략)
        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)

        # 백테스트 엔진
        engine = BacktestEngine(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital
        )

        # 실행
        results = engine.run(stock_code)

        if results:
            engine.print_summary()

            # 거래 내역 표시
            trades_df = engine.get_trades_df()
            if trades_df is not None and len(trades_df) > 0:
                show_trades = input("\n거래 내역을 보시겠습니까? (y/N): ").strip().lower()
                if show_trades == 'y':
                    print("\n최근 거래 내역 (최대 20개):")
                    print("-" * 80)
                    print(trades_df.tail(20).to_string(index=False))
        else:
            print("✗ 백테스트 실행 실패")

    except ValueError:
        print("✗ 날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.")
    except Exception as e:
        print(f"✗ 오류 발생: {e}")


def show_stats():
    """종목 통계 보기"""
    print("\n[종목 통계]")

    try:
        with session_scope() as session:
            total_stocks = session.query(Stock).count()
            kospi_stocks = session.query(Stock).filter_by(market='KOSPI').count()
            kosdaq_stocks = session.query(Stock).filter_by(market='KOSDAQ').count()

            print(f"\n총 종목 수: {total_stocks}")
            print(f"  ├─ KOSPI: {kospi_stocks}")
            print(f"  └─ KOSDAQ: {kosdaq_stocks}")

            # 최근 수집된 종목 5개
            recent_stocks = session.query(Stock).order_by(Stock.updated_at.desc()).limit(5).all()

            if recent_stocks:
                print("\n최근 업데이트된 종목 (5개):")
                for stock in recent_stocks:
                    print(f"  - {stock.code}: {stock.name} ({stock.market})")

    except Exception as e:
        print(f"✗ 오류 발생: {e}")


def main():
    """메인 함수"""
    # 초기 설정
    init_db()

    while True:
        print_menu()
        choice = input("\n선택하세요: ").strip()

        if choice == '1':
            init_database()
        elif choice == '2':
            collect_stocks()
        elif choice == '3':
            collect_all_prices()
        elif choice == '4':
            collect_single_price()
        elif choice == '5':
            update_latest()
        elif choice == '6':
            run_backtest()
        elif choice == '7':
            show_stats()
        elif choice == '0':
            print("\n프로그램을 종료합니다.")
            break
        else:
            print("\n✗ 잘못된 선택입니다. 다시 선택해주세요.")

        input("\nEnter를 눌러 계속...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        print(f"\n✗ 치명적인 오류 발생: {e}")
