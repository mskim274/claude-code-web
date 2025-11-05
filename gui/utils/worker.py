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
