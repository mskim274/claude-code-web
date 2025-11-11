"""
데이터베이스에 저장된 데이터 확인 스크립트
"""

from db.database import session_scope
from db.models import Stock, DailyPrice
from sqlalchemy import func, desc
from datetime import datetime

def check_database():
    """데이터베이스 상태 확인"""

    print("\n" + "="*60)
    print("[DATA] 주식 데이터베이스 현황")
    print("="*60)

    with session_scope() as session:
        # 1. 종목 수 확인
        stock_count = session.query(Stock).count()
        print(f"\n[OK] 등록된 종목 수: {stock_count:,}개")

        # 2. 일봉 데이터 수 확인
        daily_count = session.query(DailyPrice).count()
        print(f"[OK] 일봉 데이터 수: {daily_count:,}건")

        # 3. 종목별 데이터 수 확인
        stock_data_count = session.query(
            DailyPrice.stock_code,
            func.count(DailyPrice.id).label('count')
        ).group_by(DailyPrice.stock_code).all()

        stocks_with_data = len(stock_data_count)
        print(f"[OK] 데이터가 있는 종목: {stocks_with_data:,}개")

        if stocks_with_data > 0:
            # 데이터가 많은 상위 10개 종목
            print("\n[TOP10] 데이터가 많은 상위 10개 종목:")
            top_stocks = sorted(stock_data_count, key=lambda x: x.count, reverse=True)[:10]

            for stock_code, count in top_stocks:
                stock = session.query(Stock).filter_by(code=stock_code).first()
                name = stock.name if stock else "알 수 없음"
                print(f"  - {stock_code} ({name}): {count:,}건")

            # 최근 수집된 데이터 확인
            print("\n[RECENT] 최근 수집된 데이터:")
            recent_data = session.query(DailyPrice).order_by(
                desc(DailyPrice.date)
            ).limit(5).all()

            for data in recent_data:
                stock = session.query(Stock).filter_by(code=data.stock_code).first()
                name = stock.name if stock else "알 수 없음"
                print(f"  - {data.stock_code} ({name}): {data.date.strftime('%Y-%m-%d')} - "
                      f"종가 {data.close:,}원")

        # 4. 샘플 데이터 상세 보기 (005930 - 삼성전자)
        print("\n[SAMPLE] 005930 (삼성전자) 최근 10일")
        samsung_data = session.query(DailyPrice).filter_by(
            stock_code='005930'
        ).order_by(desc(DailyPrice.date)).limit(10).all()

        if samsung_data:
            print(f"\n{'날짜':<12} {'시가':>10} {'고가':>10} {'저가':>10} {'종가':>10} {'거래량':>12}")
            print("-" * 70)
            for data in samsung_data:
                print(f"{data.date.strftime('%Y-%m-%d'):<12} "
                      f"{data.open:>10,} {data.high:>10,} {data.low:>10,} "
                      f"{data.close:>10,} {data.volume:>12,}")
        else:
            print("  [WARN] 삼성전자 데이터가 없습니다.")

        # 5. 날짜 범위 확인
        if daily_count > 0:
            min_date = session.query(func.min(DailyPrice.date)).scalar()
            max_date = session.query(func.max(DailyPrice.date)).scalar()
            print(f"\n[DATE] 데이터 기간: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}")

    print("\n" + "="*60)
    print("[OK] 데이터 확인 완료")
    print("="*60 + "\n")

if __name__ == '__main__':
    check_database()
