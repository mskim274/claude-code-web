#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""실시간 데이터 수집 모니터링"""

import sqlite3
import time
import os
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_collection_status():
    conn = sqlite3.connect('data/stock_data.db')
    cursor = conn.cursor()

    # 전체 종목 수
    cursor.execute('SELECT COUNT(*) FROM stocks')
    total_stocks = cursor.fetchone()[0]

    # 일봉 데이터 수집된 종목 수
    cursor.execute('SELECT COUNT(DISTINCT stock_code) FROM daily_prices')
    collected_stocks = cursor.fetchone()[0]

    # 전체 일봉 데이터 개수
    cursor.execute('SELECT COUNT(*) FROM daily_prices')
    total_prices = cursor.fetchone()[0]

    # 최근 수집된 5개 종목
    cursor.execute('''
        SELECT dp.stock_code, s.name, COUNT(*) as cnt, MAX(dp.created_at) as last_update
        FROM daily_prices dp
        JOIN stocks s ON dp.stock_code = s.code
        GROUP BY dp.stock_code
        ORDER BY MAX(dp.created_at) DESC
        LIMIT 5
    ''')
    recent = cursor.fetchall()

    # 수집 로그
    cursor.execute('''
        SELECT status, COUNT(*) as cnt
        FROM collection_logs
        WHERE collection_type = 'daily'
        GROUP BY status
    ''')
    log_stats = dict(cursor.fetchall())

    conn.close()

    return {
        'total_stocks': total_stocks,
        'collected_stocks': collected_stocks,
        'total_prices': total_prices,
        'recent': recent,
        'log_stats': log_stats
    }

def format_time_diff(timestamp_str):
    """시간 차이를 사람이 읽기 쉽게 포맷"""
    try:
        last_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        diff = datetime.now() - last_time

        if diff.seconds < 60:
            return f"{diff.seconds}초 전"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}분 전"
        else:
            return f"{diff.seconds // 3600}시간 전"
    except:
        return timestamp_str

def monitor_loop():
    """실시간 모니터링 루프"""
    print("데이터 수집 모니터링 시작 (Ctrl+C로 종료)")
    print("=" * 70)

    last_collected = 0
    start_time = datetime.now()

    while True:
        try:
            clear_screen()
            status = get_collection_status()

            # 진행률 계산
            progress = (status['collected_stocks'] / status['total_stocks'] * 100) if status['total_stocks'] > 0 else 0
            remaining = status['total_stocks'] - status['collected_stocks']

            # 수집 속도 계산
            if last_collected > 0:
                new_stocks = status['collected_stocks'] - last_collected
                elapsed = 10  # 10초마다 갱신
                stocks_per_min = (new_stocks / elapsed) * 60 if new_stocks > 0 else 0
            else:
                stocks_per_min = 0

            last_collected = status['collected_stocks']

            # 남은 시간 예상
            if stocks_per_min > 0:
                remaining_minutes = remaining / stocks_per_min
                eta_hours = int(remaining_minutes // 60)
                eta_mins = int(remaining_minutes % 60)
                eta_str = f"{eta_hours}시간 {eta_mins}분"
            else:
                eta_str = "계산 중..."

            # 출력
            print("=" * 70)
            print(f"📊 키움증권 일봉 데이터 수집 모니터링")
            print(f"   시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            print()

            print(f"🎯 전체 진행 상황")
            print(f"   수집 완료: {status['collected_stocks']:,} / {status['total_stocks']:,} 종목")
            print(f"   진행률: {progress:.1f}%")
            print(f"   남은 종목: {remaining:,}개")

            # 프로그레스 바
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"   [{bar}] {progress:.1f}%")
            print()

            print(f"⚡ 수집 속도")
            print(f"   현재 속도: {stocks_per_min:.1f} 종목/분")
            print(f"   예상 남은 시간: {eta_str}")
            print()

            print(f"📈 데이터 통계")
            print(f"   총 일봉 데이터: {status['total_prices']:,}개")
            print(f"   종목당 평균: {status['total_prices'] // status['collected_stocks'] if status['collected_stocks'] > 0 else 0}일")
            print()

            print(f"📝 수집 로그 상태")
            for log_status, count in status['log_stats'].items():
                print(f"   {log_status}: {count}개")
            print()

            print(f"🕐 최근 수집된 종목 (5개)")
            print("-" * 70)
            for stock in status['recent']:
                code, name, cnt, last_update = stock
                time_ago = format_time_diff(last_update)
                print(f"   {code} - {name:20s} | {cnt:3d}일 | {time_ago}")

            print("-" * 70)
            print(f"⏰ 업데이트: {datetime.now().strftime('%H:%M:%S')} (10초마다 자동 갱신)")
            print("   Ctrl+C를 눌러 종료")

            time.sleep(10)

        except KeyboardInterrupt:
            print("\n\n모니터링을 종료합니다.")
            break
        except Exception as e:
            print(f"\n오류 발생: {e}")
            time.sleep(10)

if __name__ == '__main__':
    monitor_loop()
