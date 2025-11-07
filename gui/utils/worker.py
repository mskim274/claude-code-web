"""
Background worker threads for long-running operations
"""

from PyQt5.QtCore import QThread, pyqtSignal
from typing import Callable, Any


class Worker(QThread):
    """Generic worker thread for running tasks in background"""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        """Execute the function in background"""
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.finished.emit(self.result)
        except Exception as e:
            self.error.emit(str(e))

    def emit_progress(self, percent: int, message: str):
        """Emit progress update"""
        self.progress.emit(percent, message)


class DataCollectionWorker(QThread):
    """Worker for data collection tasks with progress tracking"""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, collector, collection_type: str, **kwargs):
        super().__init__()
        self.collector = collector
        self.collection_type = collection_type
        self.kwargs = kwargs
        self._is_running = True

    def run(self):
        """Execute data collection"""
        try:
            if self.collection_type == 'stock_list':
                self._collect_stock_list()
            elif self.collection_type == 'daily_prices':
                self._collect_daily_prices()
            elif self.collection_type == 'single_stock':
                self._collect_single_stock()
            elif self.collection_type == 'update_latest':
                self._update_latest()
            elif self.collection_type == 'minute_prices_optimized':
                self._collect_minute_prices_optimized()
            elif self.collection_type == 'tick_data':
                self._collect_tick_data()
        except Exception as e:
            self.error.emit(str(e))

    def _collect_stock_list(self):
        """Collect stock list"""
        self.log.emit("Starting stock list collection...")
        self.progress.emit(10, "Logging in to Kiwoom API...")

        if not self.collector.login():
            self.error.emit("Login failed")
            return

        self.progress.emit(30, "Collecting stock list...")
        count = self.collector.collect_all_stock_list()

        self.progress.emit(100, f"Completed: {count} stocks collected")
        self.finished.emit({'count': count})
        self.collector.logout()

    def _collect_daily_prices(self):
        """Collect daily prices for all stocks"""
        years = self.kwargs.get('years', 5)

        self.log.emit(f"Starting daily price collection ({years} years)...")
        self.progress.emit(5, "Logging in to Kiwoom API...")

        if not self.collector.login():
            self.error.emit("Login failed")
            return

        self.progress.emit(10, "Starting data collection...")
        stats = self.collector.collect_all_daily_prices(years=years)

        self.progress.emit(100, "Collection completed")
        self.finished.emit(stats)
        self.collector.logout()

    def _collect_single_stock(self):
        """Collect data for a single stock"""
        stock_code = self.kwargs.get('stock_code')
        years = self.kwargs.get('years', 5)

        self.log.emit(f"Collecting data for {stock_code}...")
        self.progress.emit(10, "Logging in...")

        if not self.collector.login():
            self.error.emit("Login failed")
            return

        self.progress.emit(30, f"Collecting {stock_code} data...")
        records = self.collector.collect_daily_price(stock_code, years=years)

        self.progress.emit(100, f"Collected {records} records")
        self.finished.emit({'records': records})
        self.collector.logout()

    def _update_latest(self):
        """Update latest prices"""
        self.log.emit("Updating latest prices...")
        self.progress.emit(10, "Logging in...")

        if not self.collector.login():
            self.error.emit("Login failed")
            return

        self.progress.emit(30, "Updating prices...")
        updated = self.collector.update_latest_prices()

        self.progress.emit(100, f"Updated {updated} stocks")
        self.finished.emit({'updated': updated})
        self.collector.logout()

    def _collect_minute_prices_optimized(self):
        """Collect minute prices with optimization"""
        intervals = self.kwargs.get('intervals', [60])
        count = self.kwargs.get('count', 500)
        stock_codes = self.kwargs.get('stock_codes')

        self.log.emit(f"분봉 데이터 수집 시작 (간격: {intervals}, 개수: {count})")
        self.progress.emit(5, "API 로그인 및 커넥션 풀 초기화 중...")

        if not self.collector.login():
            self.error.emit("Login failed")
            return

        self.log.emit("병렬 처리 시작 (5 워커, 배치 크기 30)")
        self.progress.emit(10, "병렬 데이터 수집 시작...")

        # Get total stock count for logging
        if stock_codes:
            total_stocks = len(stock_codes)
        else:
            from db.database import session_scope
            from db.models import Stock
            with session_scope() as session:
                total_stocks = session.query(Stock).count()

        total_tasks = total_stocks * len(intervals)
        self.log.emit(f"총 수집 작업: {total_tasks:,}개 (종목: {total_stocks:,}개 × 간격: {len(intervals)}개)")

        stats = self.collector.collect_all_minute_prices_parallel(
            intervals=intervals,
            count=count,
            stock_codes=stock_codes,
            batch_size=30
        )

        self.log.emit(f"수집 완료 - Success={stats.get('success', 0)}, Failed={stats.get('failed', 0)}, Total={stats.get('total', 0)}")
        self.progress.emit(100, "분봉 수집 완료")
        self.finished.emit(stats)
        self.collector.logout()

    def _collect_tick_data(self):
        """Collect tick data"""
        import time
        stock_codes = self.kwargs.get('stock_codes', [])
        count = self.kwargs.get('count', 600)

        self.log.emit(f"틱 데이터 수집 시작 (종목: {len(stock_codes)}개, 틱: {count}개)")
        self.progress.emit(10, "API 로그인 중...")

        if not self.collector.login():
            self.error.emit("Login failed")
            return

        self.log.emit("순차 처리 시작 (1초당 1종목)")
        self.progress.emit(30, "틱 데이터 수집 중...")

        # 각 종목별로 수집
        success_count = 0
        failed_count = 0
        start_time = time.time()

        for i, code in enumerate(stock_codes):
            if not self._is_running:
                self.log.emit(f"수집 중단됨 (처리: {i}/{len(stock_codes)})")
                break

            try:
                self.log.emit(f"수집 중: {code} ({i+1}/{len(stock_codes)})")
                records = self.collector.collect_tick_data(code, count=count)

                if records > 0:
                    success_count += 1
                    self.log.emit(f"✓ {code}: {records}개 틱 저장됨")
                else:
                    failed_count += 1
                    self.log.emit(f"✗ {code}: 데이터 없음")

                # 진행률 및 속도 계산
                progress = int(30 + (60 * (i + 1) / len(stock_codes)))
                elapsed = time.time() - start_time
                speed = (i + 1) / elapsed if elapsed > 0 else 0
                remaining = (len(stock_codes) - (i + 1)) / speed if speed > 0 else 0

                status_msg = f"진행: {i+1}/{len(stock_codes)} | 속도: {speed:.1f}/초 | 남은 시간: {int(remaining//60)}분 {int(remaining%60)}초"
                self.progress.emit(progress, status_msg)
                self.log.emit(f"Processed {i+1}/{len(stock_codes)} stocks")

            except Exception as e:
                failed_count += 1
                self.log.emit(f"✗ {code} 오류: {str(e)}")

        total_time = time.time() - start_time
        self.log.emit(f"수집 완료 - 성공: {success_count}, 실패: {failed_count}, 소요 시간: {int(total_time//60)}분 {int(total_time%60)}초")
        self.progress.emit(100, f"틱 수집 완료")
        self.finished.emit({
            'success': success_count,
            'failed': failed_count,
            'total': len(stock_codes)
        })
        self.collector.logout()

    def stop(self):
        """Stop the worker"""
        self._is_running = False
        self.quit()


class BacktestWorker(QThread):
    """Worker for running backtests"""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, engine, stock_code: str):
        super().__init__()
        self.engine = engine
        self.stock_code = stock_code

    def run(self):
        """Execute backtest"""
        try:
            self.progress.emit(20, f"Loading data for {self.stock_code}...")
            results = self.engine.run(self.stock_code)

            if results:
                self.progress.emit(100, "Backtest completed")
                self.finished.emit(results)
            else:
                self.error.emit("Backtest failed: No results")

        except Exception as e:
            self.error.emit(f"Backtest error: {str(e)}")
