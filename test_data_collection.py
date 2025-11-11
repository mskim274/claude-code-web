"""
데이터 수집 기능 테스트 스크립트
"""

import sys
import logging
from collectors.stock_collector import StockCollector
from db.database import session_scope
from db.models import Stock, DailyPrice

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_stock_list():
    """종목 리스트 확인"""
    print("\n" + "="*60)
    print("[TEST] 종목 리스트 확인")
    print("="*60)

    with session_scope() as session:
        stock_count = session.query(Stock).count()
        print(f"[OK] 등록된 종목 수: {stock_count:,}개")

        if stock_count > 0:
            # 샘플 종목 10개 표시
            stocks = session.query(Stock).limit(10).all()
            print("\n[SAMPLE] 샘플 종목 10개:")
            for stock in stocks:
                print(f"  - {stock.code}: {stock.name} ({stock.market})")
        else:
            print("[WARN] 종목이 하나도 없습니다!")

    return stock_count > 0

def test_collector_init():
    """StockCollector 초기화 테스트"""
    print("\n" + "="*60)
    print("[TEST] StockCollector 초기화")
    print("="*60)

    try:
        collector = StockCollector(use_kiwoom_api=False)
        print("[OK] StockCollector 초기화 성공")
        return True
    except Exception as e:
        print(f"[ERROR] StockCollector 초기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_daily_price_collection():
    """일봉 데이터 수집 테스트 (Kiwoom API 없이)"""
    print("\n" + "="*60)
    print("[TEST] 일봉 데이터 수집 (API 없이 DB 확인)")
    print("="*60)

    with session_scope() as session:
        # 현재 일봉 데이터 수
        before_count = session.query(DailyPrice).count()
        print(f"[BEFORE] 일봉 데이터 수: {before_count:,}건")

        # 데이터가 있는 종목 확인
        from sqlalchemy import func
        stock_with_data = session.query(
            DailyPrice.stock_code,
            func.count(DailyPrice.id).label('count')
        ).group_by(DailyPrice.stock_code).all()

        print(f"[INFO] 데이터가 있는 종목: {len(stock_with_data)}개")

        if len(stock_with_data) > 0:
            print("\n[DETAIL] 종목별 데이터 수:")
            for stock_code, count in stock_with_data[:10]:
                stock = session.query(Stock).filter_by(code=stock_code).first()
                name = stock.name if stock else "알 수 없음"
                print(f"  - {stock_code} ({name}): {count:,}건")

def test_kiwoom_connection():
    """Kiwoom API 연결 테스트"""
    print("\n" + "="*60)
    print("[TEST] Kiwoom API 연결 (32-bit)")
    print("="*60)

    try:
        collector = StockCollector(use_kiwoom_api=True)
        print("[INFO] Kiwoom API Client 생성 시도...")

        # 로그인 시도
        if collector.login():
            print("[OK] Kiwoom API 로그인 성공!")
            collector.logout()
            return True
        else:
            print("[WARN] Kiwoom API 로그인 실패 (계정 정보 또는 32-bit Python 필요)")
            return False

    except Exception as e:
        print(f"[ERROR] Kiwoom API 연결 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_data_collection():
    """샘플 데이터로 1개 종목 수집 테스트"""
    print("\n" + "="*60)
    print("[TEST] 샘플 종목 1개 수집 (Kiwoom API 필요)")
    print("="*60)

    try:
        collector = StockCollector(use_kiwoom_api=True)

        if not collector.login():
            print("[SKIP] Kiwoom API 로그인 불가")
            return False

        # 삼성전자 데이터 수집
        test_code = "005930"
        print(f"[INFO] {test_code} (삼성전자) 데이터 수집 중...")

        records = collector.collect_daily_price(test_code, years=1)

        print(f"[OK] {records}건 수집 완료")

        collector.logout()
        return True

    except Exception as e:
        print(f"[ERROR] 데이터 수집 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """전체 테스트 실행"""
    print("\n" + "="*70)
    print(" "*20 + "데이터 수집 테스트")
    print("="*70)

    results = {}

    # 1. 종목 리스트 확인
    results['stock_list'] = test_stock_list()

    # 2. Collector 초기화
    results['collector_init'] = test_collector_init()

    # 3. 일봉 데이터 확인
    test_daily_price_collection()

    # 4. Kiwoom API 연결 테스트 (선택)
    print("\n[OPTION] Kiwoom API 연결 테스트를 진행하시겠습니까?")
    print("  - Kiwoom OpenAPI가 설치되어 있어야 합니다")
    print("  - 32-bit Python이 필요합니다")
    print("  - 계정 로그인이 필요합니다")

    user_input = input("\n테스트 진행? (y/N): ").strip().lower()

    if user_input == 'y':
        results['kiwoom_connection'] = test_kiwoom_connection()

        if results['kiwoom_connection']:
            # 5. 샘플 수집
            user_input2 = input("\n샘플 데이터 수집 테스트? (y/N): ").strip().lower()
            if user_input2 == 'y':
                results['sample_collection'] = test_sample_data_collection()

    # 결과 요약
    print("\n" + "="*70)
    print(" "*25 + "테스트 결과 요약")
    print("="*70)

    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "="*70)

if __name__ == '__main__':
    main()
