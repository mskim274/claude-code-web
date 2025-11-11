"""
데이터 수집 자동 테스트 (Kiwoom API 연결 테스트 포함)
"""

import sys
import logging
from collectors.stock_collector import StockCollector
from db.database import session_scope
from db.models import Stock, DailyPrice
from sqlalchemy import func

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("\n" + "="*70)
    print(" "*20 + "데이터 수집 자동 테스트")
    print("="*70)

    # 1. 종목 리스트 확인
    print("\n[TEST 1/4] 종목 리스트 확인")
    with session_scope() as session:
        stock_count = session.query(Stock).count()
        print(f"  [OK] 등록된 종목: {stock_count:,}개")

    # 2. 일봉 데이터 확인
    print("\n[TEST 2/4] 일봉 데이터 확인")
    with session_scope() as session:
        daily_count = session.query(DailyPrice).count()
        print(f"  [OK] 일봉 데이터: {daily_count:,}건")

        stocks_with_data = session.query(
            DailyPrice.stock_code,
            func.count(DailyPrice.id).label('count')
        ).group_by(DailyPrice.stock_code).count()

        print(f"  [OK] 데이터 있는 종목: {stocks_with_data}개")

    # 3. StockCollector 초기화 (Kiwoom API 없이)
    print("\n[TEST 3/4] StockCollector 초기화 (API 없이)")
    try:
        collector_no_api = StockCollector(use_kiwoom_api=False)
        print("  [OK] API 없이 초기화 성공")
    except Exception as e:
        print(f"  [FAIL] 초기화 실패: {str(e)}")

    # 4. Kiwoom API 연결 테스트
    print("\n[TEST 4/4] Kiwoom API 연결 테스트")
    print("  [INFO] 32-bit Python + Kiwoom OpenAPI 필요")

    try:
        collector = StockCollector(use_kiwoom_api=True)
        print("  [OK] Kiwoom API Client 생성 성공")

        # 로그인 시도
        print("  [INFO] Kiwoom API 로그인 시도...")
        if collector.login():
            print("  [OK] Kiwoom API 로그인 성공!")

            # 간단한 데이터 수집 테스트
            print("\n[EXTRA] 삼성전자 최신 데이터 1건 수집 테스트")
            try:
                # 단일 종목 최신 데이터만 수집
                records = collector.collect_daily_price("005930", years=1)
                print(f"  [OK] {records}건 수집됨")

                # 결과 확인
                with session_scope() as session:
                    samsung_count = session.query(DailyPrice).filter_by(
                        stock_code='005930'
                    ).count()
                    print(f"  [VERIFY] DB에 삼성전자 데이터: {samsung_count}건")

            except Exception as e:
                print(f"  [WARN] 데이터 수집 실패: {str(e)}")

            collector.logout()
            print("  [OK] 로그아웃 완료")

        else:
            print("  [WARN] Kiwoom API 로그인 실패")
            print("  [INFO] 가능한 원인:")
            print("    - 32-bit Python 미설치")
            print("    - Kiwoom OpenAPI 미설치")
            print("    - 계정 정보 미설정")
            print("    - 이미 다른 곳에서 로그인됨")

    except Exception as e:
        print(f"  [ERROR] Kiwoom API 연결 실패: {str(e)}")
        import traceback
        print("\n[DETAIL] 에러 상세:")
        traceback.print_exc()

    # 최종 결과
    print("\n" + "="*70)
    print(" "*25 + "테스트 완료")
    print("="*70)

    with session_scope() as session:
        final_stock_count = session.query(Stock).count()
        final_daily_count = session.query(DailyPrice).count()
        final_stocks_with_data = session.query(
            DailyPrice.stock_code
        ).distinct().count()

        print(f"\n[SUMMARY] 최종 상태:")
        print(f"  - 종목 수: {final_stock_count:,}개")
        print(f"  - 일봉 데이터: {final_daily_count:,}건")
        print(f"  - 데이터 있는 종목: {final_stocks_with_data}개")

    print("\n[NEXT] GUI에서 데이터 수집:")
    print("  1. GUI 실행: python gui_main.py")
    print("  2. '데이터 수집' 탭 이동")
    print("  3. '일봉 수집' 버튼 클릭")
    print("  4. Kiwoom 로그인")
    print("  5. 진행률 확인\n")

if __name__ == '__main__':
    main()
