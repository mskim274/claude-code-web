"""
Data collector widget - collect stock data from Kiwoom API
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QSpinBox, QLineEdit,
                             QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt
from gui.components.progress_dialog import ProgressDialog
from gui.utils.worker import DataCollectionWorker
from collectors.stock_collector import StockCollector


class DataCollectorWidget(QWidget):
    """Widget for collecting stock data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("데이터 수집")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Stock list collection
        stock_list_group = QGroupBox("1. 종목 리스트 수집")
        stock_list_layout = QVBoxLayout()

        desc = QLabel("키움 API로부터 모든 코스피/코스닥 종목 리스트를 수집합니다")
        desc.setWordWrap(True)
        stock_list_layout.addWidget(desc)

        self.collect_stocks_btn = QPushButton("종목 리스트 수집")
        self.collect_stocks_btn.clicked.connect(self.collect_stock_list)
        stock_list_layout.addWidget(self.collect_stocks_btn)

        stock_list_group.setLayout(stock_list_layout)
        layout.addWidget(stock_list_group)

        # Daily price collection
        daily_group = QGroupBox("2. 일봉 데이터 수집")
        daily_layout = QVBoxLayout()

        desc2 = QLabel("모든 종목의 과거 일봉 데이터를 수집합니다")
        desc2.setWordWrap(True)
        daily_layout.addWidget(desc2)

        years_layout = QHBoxLayout()
        years_layout.addWidget(QLabel("수집 기간(년):"))
        self.years_spin = QSpinBox()
        self.years_spin.setMinimum(1)
        self.years_spin.setMaximum(20)
        self.years_spin.setValue(5)
        years_layout.addWidget(self.years_spin)
        years_layout.addStretch()
        daily_layout.addLayout(years_layout)

        warning = QLabel("주의: 전체 종목 수집은 2-3일이 소요될 수 있습니다!")
        warning.setStyleSheet("color: orange; font-weight: bold;")
        daily_layout.addWidget(warning)

        self.collect_all_btn = QPushButton("전체 종목 데이터 수집")
        self.collect_all_btn.clicked.connect(self.collect_all_daily_prices)
        daily_layout.addWidget(self.collect_all_btn)

        daily_group.setLayout(daily_layout)
        layout.addWidget(daily_group)

        # Single stock collection
        single_group = QGroupBox("3. 개별 종목 데이터 수집")
        single_layout = QVBoxLayout()

        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("종목코드:"))
        self.stock_code_input = QLineEdit()
        self.stock_code_input.setPlaceholderText("예: 005930 (삼성전자)")
        code_layout.addWidget(self.stock_code_input)

        years_layout2 = QHBoxLayout()
        years_layout2.addWidget(QLabel("수집 기간(년):"))
        self.single_years_spin = QSpinBox()
        self.single_years_spin.setMinimum(1)
        self.single_years_spin.setMaximum(20)
        self.single_years_spin.setValue(5)
        years_layout2.addWidget(self.single_years_spin)
        years_layout2.addStretch()

        single_layout.addLayout(code_layout)
        single_layout.addLayout(years_layout2)

        self.collect_single_btn = QPushButton("개별 종목 수집")
        self.collect_single_btn.clicked.connect(self.collect_single_stock)
        single_layout.addWidget(self.collect_single_btn)

        single_group.setLayout(single_layout)
        layout.addWidget(single_group)

        # Update latest
        update_group = QGroupBox("4. 최신 가격 업데이트")
        update_layout = QVBoxLayout()

        desc3 = QLabel("기존 데이터가 있는 모든 종목의 가격을 업데이트합니다")
        desc3.setWordWrap(True)
        update_layout.addWidget(desc3)

        self.update_btn = QPushButton("최신 가격 업데이트")
        self.update_btn.clicked.connect(self.update_latest)
        update_layout.addWidget(self.update_btn)

        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        # Log output
        log_group = QGroupBox("수집 로그")
        log_layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        log_layout.addWidget(self.log_output)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()

    def collect_stock_list(self):
        """Collect stock list"""
        reply = QMessageBox.question(
            self, '확인',
            '키움 API에서 종목 리스트를 수집하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        self.add_log("종목 리스트 수집 시작...")
        self.set_buttons_enabled(False)

        # Create progress dialog
        progress = ProgressDialog("종목 리스트 수집 중", self)

        # Create worker
        collector = StockCollector()
        self.worker = DataCollectionWorker(collector, 'stock_list')
        self.worker.progress.connect(progress.set_progress)
        self.worker.log.connect(progress.add_log)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(lambda r: self.on_collection_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_collection_error(progress, e))

        progress.rejected.connect(self.worker.stop)
        self.worker.start()
        progress.exec_()

    def collect_all_daily_prices(self):
        """Collect all daily prices"""
        years = self.years_spin.value()

        reply = QMessageBox.question(
            self, '확인',
            f'모든 종목의 {years}년 데이터를 수집합니다.\n'
            f'2-3일이 소요될 수 있습니다. 계속하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        self.add_log(f"일봉 데이터 수집 시작 ({years}년)...")
        self.set_buttons_enabled(False)

        progress = ProgressDialog("일봉 데이터 수집 중", self)

        collector = StockCollector()
        self.worker = DataCollectionWorker(collector, 'daily_prices', years=years)
        self.worker.progress.connect(progress.set_progress)
        self.worker.log.connect(progress.add_log)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(lambda r: self.on_collection_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_collection_error(progress, e))

        progress.rejected.connect(self.worker.stop)
        self.worker.start()
        progress.exec_()

    def collect_single_stock(self):
        """Collect single stock data"""
        stock_code = self.stock_code_input.text().strip()
        years = self.single_years_spin.value()

        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력해주세요")
            return

        self.add_log(f"{stock_code} 데이터 수집 중...")
        self.set_buttons_enabled(False)

        progress = ProgressDialog(f"{stock_code} 수집 중", self)

        collector = StockCollector()
        self.worker = DataCollectionWorker(
            collector, 'single_stock',
            stock_code=stock_code, years=years
        )
        self.worker.progress.connect(progress.set_progress)
        self.worker.log.connect(progress.add_log)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(lambda r: self.on_collection_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_collection_error(progress, e))

        progress.rejected.connect(self.worker.stop)
        self.worker.start()
        progress.exec_()

    def update_latest(self):
        """Update latest prices"""
        reply = QMessageBox.question(
            self, '확인',
            '모든 종목의 최신 가격을 업데이트하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        self.add_log("최신 가격 업데이트 중...")
        self.set_buttons_enabled(False)

        progress = ProgressDialog("최신 가격 업데이트 중", self)

        collector = StockCollector()
        self.worker = DataCollectionWorker(collector, 'update_latest')
        self.worker.progress.connect(progress.set_progress)
        self.worker.log.connect(progress.add_log)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(lambda r: self.on_collection_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_collection_error(progress, e))

        progress.rejected.connect(self.worker.stop)
        self.worker.start()
        progress.exec_()

    def on_collection_finished(self, dialog, results):
        """Handle collection completion"""
        dialog.on_complete(success=True)
        self.add_log(f"수집 완료: {results}")
        self.set_buttons_enabled(True)

    def on_collection_error(self, dialog, error):
        """Handle collection error"""
        dialog.on_error(error)
        self.add_log(f"오류: {error}")
        self.set_buttons_enabled(True)

    def add_log(self, message: str):
        """Add log message"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_output.append(f"[{timestamp}] {message}")

    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable all buttons"""
        self.collect_stocks_btn.setEnabled(enabled)
        self.collect_all_btn.setEnabled(enabled)
        self.collect_single_btn.setEnabled(enabled)
        self.update_btn.setEnabled(enabled)
