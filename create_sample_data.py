"""
샘플 데이터 생성 스크립트
백테스팅 테스트용 임시 데이터를 생성합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from db.database import session_scope
from db.models import DailyPrice

def create_sample_data(stock_code='005930', days=365):
    """
    샘플 일봉 데이터 생성

    Args:
        stock_code: 종목코드
        days: 생성할 일수
    """
    print(f"{stock_code} 샘플 데이터 생성 중... ({days}일)")

    # 시작 가격
    start_price = 70000

    # 날짜 생성
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')

    # 랜덤 워크로 가격 생성
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, days)  # 일 평균 0.1% 수익, 표준편차 2%
    prices = start_price * (1 + returns).cumprod()

    # 데이터 생성
    data = []
    for i, date in enumerate(dates):
        price = prices[i]

        # OHLC 생성 (간단한 모델)
        daily_range = price * 0.03  # 일중 변동폭 3%

        open_price = price + np.random.uniform(-daily_range/2, daily_range/2)
        high = max(open_price, price) + np.random.uniform(0, daily_range/2)
        low = min(open_price, price) - np.random.uniform(0, daily_range/2)
        close = price
        volume = int(np.random.uniform(5000000, 20000000))  # 500만~2000만 주

        data.append({
            'stock_code': stock_code,
            'date': date.date(),
            'open': int(open_price),
            'high': int(high),
            'low': int(low),
            'close': int(close),
            'volume': volume
        })

    # DB에 저장
    with session_scope() as session:
        # 기존 데이터 삭제
        session.query(DailyPrice).filter_by(stock_code=stock_code).delete()

        # 새 데이터 삽입
        for row in data:
            daily_price = DailyPrice(**row)
            session.add(daily_price)

        session.commit()

    print(f"[OK] {len(data)}일치 데이터 생성 완료!")
    print(f"   종목: {stock_code}")
    print(f"   기간: {dates[0].date()} ~ {dates[-1].date()}")
    print(f"   시작가: {int(prices[0]):,}원")
    print(f"   종료가: {int(prices[-1]):,}원")
    print(f"   수익률: {(prices[-1]/prices[0]-1)*100:.2f}%")

if __name__ == '__main__':
    # 삼성전자 1년 데이터 생성
    create_sample_data('005930', days=365)

    print("\n이제 GUI에서 백테스팅을 실행할 수 있습니다!")
    print("종목코드: 005930")
    print("기간: 최근 1년")
