"""
최적화된 주식 데이터 수집기
병렬 처리 및 커넥션 풀링 지원
"""

import logging
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
from queue import Queue
from threading import Lock

from collectors.kiwoom_api_client import KiwoomAPIClient
from db.database import session_scope
from db.models import Stock, DailyPrice, MinutePrice, TickPrice, CollectionLog
from config.kiwoom_config import KiwoomConfig

logger = logging.getLogger(__name__)


class ConnectionPool:
    """API 클라이언트 커넥션 풀"""

    def __init__(self, pool_size=3):
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = Lock()
        self._initialized = False

    def initialize(self):
        """풀 초기화"""
        with self.lock:
            if self._initialized:
                return

            logger.info(f"Initializing connection pool (size: {self.pool_size})")
            for i in range(self.pool_size):
                try:
                    client = KiwoomAPIClient()
                    # 로그인은 한 번만 수행
                    if i == 0:
                        success = client.login()
                        if not success:
                            raise Exception("Login failed")
                    self.pool.put(client)
                except Exception as e:
                    logger.error(f"Failed to create client #{i}: {e}")
                    raise

            self._initialized = True
            logger.info("Connection pool initialized")

    def get_client(self) -> KiwoomAPIClient:
        """클라이언트 가져오기"""
        return self.pool.get()

    def return_client(self, client: KiwoomAPIClient):
        """클라이언트 반환"""
        self.pool.put(client)

    def close_all(self):
        """모든 연결 종료"""
        while not self.pool.empty():
            client = self.pool.get()
            try:
                client.logout()
            except:
                pass


class OptimizedStockCollector:
    """최적화된 주식 데이터 수집기"""

    def __init__(self, max_workers=5):
        """
        Args:
            max_workers: 최대 워커 스레드 수 (기본 5)
        """
        self.max_workers = max_workers
        self.pool = ConnectionPool(pool_size=min(max_workers, 3))
        self.is_logged_in = False
        logger.info(f"OptimizedStockCollector initialized (workers: {max_workers})")

    def login(self):
        """로그인 및 커넥션 풀 초기화"""
        if not self.is_logged_in:
            self.pool.initialize()
            self.is_logged_in = True
            logger.info("Optimized collector logged in")
            return True
        return True

    def logout(self):
        """로그아웃"""
        if self.is_logged_in:
            self.pool.close_all()
            self.is_logged_in = False
            logger.info("Optimized collector logged out")

    def collect_all_daily_prices_parallel(self, years=5, batch_size=50):
        """
        병렬로 일봉 데이터 수집

        Args:
            years: 수집 기간 (년)
            batch_size: 배치 크기

        Returns:
            dict: 수집 통계
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return {'success': 0, 'skipped': 0, 'failed': 0, 'total': 0}

        # 종목 리스트 조회
        with session_scope() as session:
            stocks = session.query(Stock).all()
            stock_list = [(s.code, s.name) for s in stocks]

        total = len(stock_list)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        logger.info(f"Starting parallel daily price collection for {total} stocks")

        # 배치 단위로 처리
        for batch_start in range(0, total, batch_size):
            batch = stock_list[batch_start:batch_start + batch_size]
            logger.info(f"Processing batch {batch_start//batch_size + 1}/{(total + batch_size - 1)//batch_size}")

            # 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for code, name in batch:
                    future = executor.submit(self._collect_daily_price_task, code, name, years)
                    futures[future] = (code, name)

                # 결과 수집
                for future in as_completed(futures):
                    code, name = futures[future]
                    try:
                        result = future.result()
                        if result > 0:
                            success_count += 1
                        elif result == 0:
                            skipped_count += 1
                        else:
                            failed_count += 1

                        # 진행률 로그
                        current = batch_start + list(futures.values()).index((code, name)) + 1
                        if current % 10 == 0:
                            progress = (current / total) * 100
                            logger.info(f"Progress: {progress:.1f}% ({current}/{total})")

                    except Exception as e:
                        logger.error(f"Error processing {code}: {e}")
                        failed_count += 1

        logger.info(f"Parallel collection completed: Success={success_count}, Skipped={skipped_count}, Failed={failed_count}")
        return {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': total
        }

    def _collect_daily_price_task(self, stock_code: str, stock_name: str, years: int) -> int:
        """일봉 수집 태스크 (스레드에서 실행)"""
        client = self.pool.get_client()
        try:
            # 시작일/종료일 계산
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)

            # 수집 로그 생성
            log_id = None
            with session_scope() as session:
                log = CollectionLog(
                    stock_code=stock_code,
                    collection_type='daily',
                    start_date=start_date.date(),
                    end_date=end_date.date(),
                    status='in_progress'
                )
                session.add(log)
                session.flush()
                log_id = log.id

            # API 호출
            data_list = client.get_daily_price(
                stock_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )

            if not data_list:
                with session_scope() as session:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = 'No data returned'
                    log.completed_at = datetime.now()
                return 0

            # DB 저장
            saved_count = 0
            with session_scope() as session:
                for data in data_list:
                    try:
                        date_str = data['일자'].strip()
                        date = datetime.strptime(date_str, '%Y%m%d').date()

                        existing = session.query(DailyPrice).filter_by(
                            stock_code=stock_code,
                            date=date
                        ).first()

                        if existing:
                            continue

                        close = abs(int(data['현재가'].strip()))
                        open_price = abs(int(data['시가'].strip()))
                        high = abs(int(data['고가'].strip()))
                        low = abs(int(data['저가'].strip()))
                        volume = int(data['거래량'].strip())

                        daily_price = DailyPrice(
                            stock_code=stock_code,
                            date=date,
                            open=open_price,
                            high=high,
                            low=low,
                            close=close,
                            volume=volume,
                            adj_close=float(close)
                        )
                        session.add(daily_price)
                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error parsing data for {stock_code}: {e}")
                        continue

                # 로그 업데이트
                log = session.query(CollectionLog).get(log_id)
                log.status = 'success'
                log.records_collected = saved_count
                log.completed_at = datetime.now()

            logger.info(f"Saved {saved_count} daily prices for {stock_name} ({stock_code})")
            return saved_count

        except Exception as e:
            logger.error(f"Error in daily price task for {stock_code}: {e}")
            with session_scope() as session:
                if log_id:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = str(e)
                    log.completed_at = datetime.now()
            return -1

        finally:
            self.pool.return_client(client)

    def collect_all_minute_prices_parallel(self, intervals=[60, 30, 10], count=500,
                                           stock_codes=None, batch_size=30):
        """
        병렬로 분봉 데이터 수집

        Args:
            intervals: 분봉 간격 리스트
            count: 각 분봉당 수집 개수
            stock_codes: 종목 코드 리스트 (None이면 전체)
            batch_size: 배치 크기

        Returns:
            dict: 수집 통계
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return {'success': 0, 'skipped': 0, 'failed': 0, 'total': 0}

        # 종목 리스트
        if stock_codes:
            with session_scope() as session:
                stocks = session.query(Stock).filter(Stock.code.in_(stock_codes)).all()
                stock_list = [(s.code, s.name) for s in stocks]
        else:
            with session_scope() as session:
                stocks = session.query(Stock).all()
                stock_list = [(s.code, s.name) for s in stocks]

        total = len(stock_list) * len(intervals)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        logger.info(f"Starting parallel minute price collection for {len(stock_list)} stocks, {len(intervals)} intervals")

        # 배치 처리
        for batch_start in range(0, len(stock_list), batch_size):
            batch = stock_list[batch_start:batch_start + batch_size]

            # 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for code, name in batch:
                    for interval in intervals:
                        future = executor.submit(self._collect_minute_price_task, code, name, interval, count)
                        futures[future] = (code, name, interval)

                # 결과 수집
                for future in as_completed(futures):
                    code, name, interval = futures[future]
                    try:
                        result = future.result()
                        if result > 0:
                            success_count += 1
                        elif result == 0:
                            skipped_count += 1
                        else:
                            failed_count += 1

                    except Exception as e:
                        logger.error(f"Error processing {code} {interval}min: {e}")
                        failed_count += 1

        logger.info(f"Parallel minute collection completed: Success={success_count}, Skipped={skipped_count}, Failed={failed_count}")
        return {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': total
        }

    def _collect_minute_price_task(self, stock_code: str, stock_name: str, interval: int, count: int) -> int:
        """분봉 수집 태스크"""
        client = self.pool.get_client()
        try:
            log_id = None
            with session_scope() as session:
                log = CollectionLog(
                    stock_code=stock_code,
                    collection_type=f'minute_{interval}',
                    status='in_progress'
                )
                session.add(log)
                session.flush()
                log_id = log.id

            data_list = client.get_minute_price(stock_code, tick=interval, count=count)

            if not data_list:
                with session_scope() as session:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = 'No data returned'
                    log.completed_at = datetime.now()
                return 0

            saved_count = 0
            with session_scope() as session:
                for data in data_list:
                    try:
                        time_str = data['체결시간'].strip()
                        dt = datetime.strptime(time_str, '%Y%m%d%H%M%S')

                        existing = session.query(MinutePrice).filter_by(
                            stock_code=stock_code,
                            datetime=dt,
                            interval=interval
                        ).first()

                        if existing:
                            continue

                        close = abs(int(data['현재가'].strip()))
                        open_price = abs(int(data['시가'].strip()))
                        high = abs(int(data['고가'].strip()))
                        low = abs(int(data['저가'].strip()))
                        volume = int(data['거래량'].strip())

                        minute_price = MinutePrice(
                            stock_code=stock_code,
                            datetime=dt,
                            interval=interval,
                            open=open_price,
                            high=high,
                            low=low,
                            close=close,
                            volume=volume
                        )
                        session.add(minute_price)
                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error parsing minute data for {stock_code}: {e}")
                        continue

                log = session.query(CollectionLog).get(log_id)
                log.status = 'success'
                log.records_collected = saved_count
                log.completed_at = datetime.now()

            logger.info(f"Saved {saved_count} {interval}min prices for {stock_name} ({stock_code})")
            return saved_count

        except Exception as e:
            logger.error(f"Error in minute price task for {stock_code}: {e}")
            with session_scope() as session:
                if log_id:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = str(e)
                    log.completed_at = datetime.now()
            return -1

        finally:
            self.pool.return_client(client)
