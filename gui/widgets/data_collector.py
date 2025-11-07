"""
Data collector widget - collect stock data from Kiwoom API
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QSpinBox, QLineEdit,
                             QMessageBox, QTextEdit, QCheckBox, QScrollArea,
                             QComboBox)
from PyQt5.QtCore import Qt
from gui.components.progress_dialog import ProgressDialog
from gui.utils.worker import DataCollectionWorker
from collectors.stock_collector import StockCollector
from collectors.optimized_collector import OptimizedStockCollector


class DataCollectorWidget(QWidget):
    """Widget for collecting stock data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # 스크롤 가능한 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

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

        # Minute price collection
        minute_group = QGroupBox("5. 분봉 데이터 수집")
        minute_layout = QVBoxLayout()

        desc4 = QLabel("선택한 종목의 분봉 데이터를 수집합니다 (1/5/10/30/60분)")
        desc4.setWordWrap(True)
        minute_layout.addWidget(desc4)

        # 분봉 간격 선택
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("분봉 간격:"))
        self.interval_1min = QCheckBox("1분")
        self.interval_5min = QCheckBox("5분")
        self.interval_10min = QCheckBox("10분")
        self.interval_30min = QCheckBox("30분")
        self.interval_60min = QCheckBox("60분")
        self.interval_60min.setChecked(True)  # 기본 선택
        interval_layout.addWidget(self.interval_1min)
        interval_layout.addWidget(self.interval_5min)
        interval_layout.addWidget(self.interval_10min)
        interval_layout.addWidget(self.interval_30min)
        interval_layout.addWidget(self.interval_60min)
        interval_layout.addStretch()
        minute_layout.addLayout(interval_layout)

        # 분봉 개수
        minute_count_layout = QHBoxLayout()
        minute_count_layout.addWidget(QLabel("수집 개수:"))
        self.minute_count_spin = QSpinBox()
        self.minute_count_spin.setMinimum(100)
        self.minute_count_spin.setMaximum(900)
        self.minute_count_spin.setValue(500)
        self.minute_count_spin.setSuffix("개")
        minute_count_layout.addWidget(self.minute_count_spin)
        minute_count_layout.addStretch()
        minute_layout.addLayout(minute_count_layout)

        # 종목 입력
        minute_code_layout = QHBoxLayout()
        minute_code_layout.addWidget(QLabel("종목코드:"))
        self.minute_stock_code_input = QLineEdit()
        self.minute_stock_code_input.setPlaceholderText("예: 005930,000660,035420 (쉼표 구분)")
        minute_code_layout.addWidget(self.minute_stock_code_input)
        minute_layout.addLayout(minute_code_layout)

        warning2 = QLabel("주의: 전체 종목 수집은 수 시간이 소요될 수 있습니다!")
        warning2.setStyleSheet("color: orange; font-weight: bold;")
        minute_layout.addWidget(warning2)

        # 버튼 레이아웃
        minute_btn_layout = QHBoxLayout()
        self.collect_minute_selected_btn = QPushButton("선택 종목 수집")
        self.collect_minute_selected_btn.clicked.connect(self.collect_minute_prices_selected)
        minute_btn_layout.addWidget(self.collect_minute_selected_btn)

        self.collect_minute_all_btn = QPushButton("전체 종목 수집")
        self.collect_minute_all_btn.clicked.connect(self.collect_minute_prices_all)
        self.collect_minute_all_btn.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold;")
        minute_btn_layout.addWidget(self.collect_minute_all_btn)

        minute_layout.addLayout(minute_btn_layout)

        minute_group.setLayout(minute_layout)
        layout.addWidget(minute_group)

        # Tick data collection
        tick_group = QGroupBox("6. 틱 데이터 수집")
        tick_layout = QVBoxLayout()

        desc5 = QLabel("틱 데이터 수집 (최대 600틱, 최근 체결 데이터)")
        desc5.setWordWrap(True)
        tick_layout.addWidget(desc5)

        # 틱 개수
        tick_count_layout = QHBoxLayout()
        tick_count_layout.addWidget(QLabel("수집 개수:"))
        self.tick_count_spin = QSpinBox()
        self.tick_count_spin.setMinimum(100)
        self.tick_count_spin.setMaximum(600)
        self.tick_count_spin.setValue(600)
        self.tick_count_spin.setSuffix("틱")
        tick_count_layout.addWidget(self.tick_count_spin)
        tick_count_layout.addStretch()
        tick_layout.addLayout(tick_count_layout)

        # 종목 입력
        tick_code_layout = QHBoxLayout()
        tick_code_layout.addWidget(QLabel("종목코드:"))
        self.tick_stock_code_input = QLineEdit()
        self.tick_stock_code_input.setPlaceholderText("예: 005930,000660,035420 (쉼표 구분)")
        tick_code_layout.addWidget(self.tick_stock_code_input)
        tick_layout.addLayout(tick_code_layout)

        tick_note = QLabel("※ 틱 데이터는 최근 600틱만 조회 가능합니다")
        tick_note.setStyleSheet("color: gray; font-size: 11px;")
        tick_layout.addWidget(tick_note)

        # 버튼 레이아웃
        tick_btn_layout = QHBoxLayout()
        self.collect_tick_selected_btn = QPushButton("선택 종목 수집")
        self.collect_tick_selected_btn.clicked.connect(self.collect_tick_data_selected)
        tick_btn_layout.addWidget(self.collect_tick_selected_btn)

        self.collect_tick_all_btn = QPushButton("전체 종목 수집")
        self.collect_tick_all_btn.clicked.connect(self.collect_tick_data_all)
        self.collect_tick_all_btn.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold;")
        tick_btn_layout.addWidget(self.collect_tick_all_btn)

        tick_layout.addLayout(tick_btn_layout)

        tick_group.setLayout(tick_layout)
        layout.addWidget(tick_group)

        # Statistics panel
        stats_group = QGroupBox("실시간 수집 현황")
        stats_layout = QHBoxLayout()

        self.current_stock_label = QLabel("대기 중...")
        self.current_stock_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        stats_layout.addWidget(QLabel("현재 종목:"))
        stats_layout.addWidget(self.current_stock_label)
        stats_layout.addStretch()

        self.success_count_label = QLabel("0")
        self.success_count_label.setStyleSheet("font-weight: bold; color: green;")
        stats_layout.addWidget(QLabel("성공:"))
        stats_layout.addWidget(self.success_count_label)

        self.skipped_count_label = QLabel("0")
        self.skipped_count_label.setStyleSheet("font-weight: bold; color: #9E9E9E;")
        stats_layout.addWidget(QLabel("건너뜀:"))
        stats_layout.addWidget(self.skipped_count_label)

        self.failed_count_label = QLabel("0")
        self.failed_count_label.setStyleSheet("font-weight: bold; color: red;")
        stats_layout.addWidget(QLabel("실패:"))
        stats_layout.addWidget(self.failed_count_label)

        self.total_count_label = QLabel("0")
        self.total_count_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(QLabel("전체:"))
        stats_layout.addWidget(self.total_count_label)

        self.speed_label = QLabel("0.0/초")
        self.speed_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        stats_layout.addWidget(QLabel("처리 속도:"))
        stats_layout.addWidget(self.speed_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

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

        # Reset statistics
        self.reset_stats()

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
        """Add log message and update statistics"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_output.append(f"[{timestamp}] {message}")

        # Parse log message for real-time statistics
        self._update_stats_from_log(message)

    def _update_stats_from_log(self, message: str):
        """Update statistics from log message"""
        import re

        # Extract current stock being processed
        if "수집 중:" in message:
            # Example: "수집 중: 005930 (1/100)"
            try:
                parts = message.split("수집 중:")[1].strip()
                stock_code = parts.split()[0]
                self.current_stock_label.setText(stock_code)
            except:
                pass

        elif "✓" in message or "✗" in message:
            # Example: "✓ 005930: 600개 틱 저장됨" or "✗ 005930: 데이터 없음"
            try:
                stock_code = message.split()[1].replace(":", "")
                self.current_stock_label.setText(stock_code)
            except:
                pass

        # Extract success/failure counts from final summary
        if "성공:" in message and "실패:" in message:
            # Example: "수집 완료 - 성공: 150, 실패: 2, 소요 시간: 2분 32초"
            try:
                success_match = re.search(r"성공:\s*(\d+)", message)
                failed_match = re.search(r"실패:\s*(\d+)", message)

                if success_match:
                    self.success_count_label.setText(success_match.group(1))
                if failed_match:
                    self.failed_count_label.setText(failed_match.group(1))
            except:
                pass

        elif "Success=" in message:
            # Example: "수집 완료 - Success=1500, Failed=20, Total=1520"
            try:
                success_match = re.search(r"Success=(\d+)", message)
                failed_match = re.search(r"Failed=(\d+)", message)
                total_match = re.search(r"Total=(\d+)", message)

                if success_match:
                    self.success_count_label.setText(success_match.group(1))
                if failed_match:
                    self.failed_count_label.setText(failed_match.group(1))
                if total_match:
                    self.total_count_label.setText(total_match.group(1))
            except:
                pass

        # Extract from dictionary format
        elif "'success':" in message:
            try:
                success_match = re.search(r"'success':\s*(\d+)", message)
                failed_match = re.search(r"'failed':\s*(\d+)", message)
                total_match = re.search(r"'total':\s*(\d+)", message)

                if success_match:
                    self.success_count_label.setText(success_match.group(1))
                if failed_match:
                    self.failed_count_label.setText(failed_match.group(1))
                if total_match:
                    self.total_count_label.setText(total_match.group(1))
            except:
                pass

        # Extract progress and speed information
        if "Processed" in message:
            # Example: "Processed 100/2500 stocks"
            try:
                parts = message.split("Processed")[1].strip().split()[0]
                if "/" in parts:
                    current, total = parts.split("/")
                    # Update total if not already set
                    if self.total_count_label.text() == "0":
                        self.total_count_label.setText(total)
            except:
                pass

        # Extract speed from status message
        if "속도:" in message:
            # Example: "진행: 100/2500 | 속도: 1.2/초 | 남은 시간: 33분 20초"
            try:
                speed_match = re.search(r"속도:\s*([\d.]+)/초", message)
                if speed_match:
                    self.speed_label.setText(f"{speed_match.group(1)}/초")
            except:
                pass

        # Update success count from checkmark messages
        if "✓" in message and ("저장됨" in message or "레코드" in message):
            try:
                current_success = int(self.success_count_label.text())
                self.success_count_label.setText(str(current_success + 1))
            except:
                pass

        # Update skipped count from circle mark messages
        elif "○" in message and "이미 최신 데이터" in message:
            try:
                current_skipped = int(self.skipped_count_label.text())
                self.skipped_count_label.setText(str(current_skipped + 1))
            except:
                pass

        # Update failed count from X mark messages
        elif "✗" in message and ("데이터 없음" in message or "오류:" in message or "실패" in message):
            try:
                current_failed = int(self.failed_count_label.text())
                self.failed_count_label.setText(str(current_failed + 1))
            except:
                pass

    def reset_stats(self):
        """Reset statistics display"""
        self.current_stock_label.setText("대기 중...")
        self.success_count_label.setText("0")
        self.skipped_count_label.setText("0")
        self.failed_count_label.setText("0")
        self.total_count_label.setText("0")
        self.speed_label.setText("0.0/초")

    def collect_minute_prices_selected(self):
        """Collect minute price data for selected stocks"""
        # 종목 코드 확인
        stock_codes_text = self.minute_stock_code_input.text().strip()
        if not stock_codes_text:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력해주세요")
            return

        stock_codes = [code.strip() for code in stock_codes_text.split(',')]
        self._collect_minute_prices_internal(stock_codes)

    def collect_minute_prices_all(self):
        """Collect minute price data for all stocks"""
        from db.database import session_scope
        from db.models import Stock

        # 전체 종목 수 확인
        with session_scope() as session:
            total_stocks = session.query(Stock).count()

        # 선택된 간격 수 확인
        interval_count = sum([
            self.interval_1min.isChecked(),
            self.interval_5min.isChecked(),
            self.interval_10min.isChecked(),
            self.interval_30min.isChecked(),
            self.interval_60min.isChecked()
        ])

        if interval_count == 0:
            interval_count = 1  # 최소 1개

        # 예상 시간 계산 (병렬 처리 5 워커, 배치 30)
        # 순차: total_stocks * interval_count 초
        # 병렬: (total_stocks * interval_count) / 5 초 (약 70% 개선)
        total_tasks = total_stocks * interval_count
        estimated_seconds = total_tasks // 5  # 병렬 처리
        estimated_minutes = estimated_seconds // 60
        estimated_hours = estimated_minutes // 60
        remaining_minutes = estimated_minutes % 60

        if estimated_hours > 0:
            time_str = f'약 {estimated_hours}시간 {remaining_minutes}분'
        else:
            time_str = f'약 {estimated_minutes}분'

        reply = QMessageBox.warning(
            self, '경고',
            f'전체 {total_stocks}개 종목의 분봉 데이터를 수집합니다.\n\n'
            f'⚠️ 예상 소요 시간: {time_str} (병렬 처리)\n'
            f'⚠️ 선택된 간격: {interval_count}개\n'
            f'⚠️ 총 수집 작업: {total_tasks:,}개\n\n'
            f'정말 계속하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        self._collect_minute_prices_internal(None)

    def _collect_minute_prices_internal(self, stock_codes):
        """Internal method to collect minute prices"""
        # 선택된 분봉 간격
        intervals = []
        if self.interval_1min.isChecked():
            intervals.append(1)
        if self.interval_5min.isChecked():
            intervals.append(5)
        if self.interval_10min.isChecked():
            intervals.append(10)
        if self.interval_30min.isChecked():
            intervals.append(30)
        if self.interval_60min.isChecked():
            intervals.append(60)

        if not intervals:
            QMessageBox.warning(self, "입력 오류", "최소 하나의 분봉 간격을 선택해주세요")
            return

        count = self.minute_count_spin.value()

        reply = QMessageBox.question(
            self, '확인',
            f'분봉 데이터를 수집합니다.\n'
            f'간격: {intervals}\n'
            f'개수: {count}개\n'
            f'종목: {"전체" if not stock_codes else f"{len(stock_codes)}개"}\n'
            f'계속하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Reset statistics
        self.reset_stats()

        self.add_log(f"분봉 데이터 수집 시작 (간격: {intervals}, 개수: {count})...")
        self.set_buttons_enabled(False)

        progress = ProgressDialog("분봉 데이터 수집 중", self)

        collector = OptimizedStockCollector(max_workers=5)
        self.worker = DataCollectionWorker(
            collector, 'minute_prices_optimized',
            intervals=intervals, count=count, stock_codes=stock_codes
        )
        self.worker.progress.connect(progress.set_progress)
        self.worker.log.connect(progress.add_log)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(lambda r: self.on_collection_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_collection_error(progress, e))

        progress.rejected.connect(self.worker.stop)
        self.worker.start()
        progress.exec_()

    def collect_tick_data_selected(self):
        """Collect tick data for selected stocks"""
        stock_codes_text = self.tick_stock_code_input.text().strip()
        if not stock_codes_text:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력해주세요")
            return

        stock_codes = [code.strip() for code in stock_codes_text.split(',')]
        self._collect_tick_data_internal(stock_codes)

    def collect_tick_data_all(self):
        """Collect tick data for all stocks"""
        from db.database import session_scope
        from db.models import Stock

        # 전체 종목 수 확인
        with session_scope() as session:
            total_stocks = session.query(Stock).count()

        # 예상 시간 계산 (1초당 1종목)
        estimated_seconds = total_stocks
        estimated_minutes = estimated_seconds // 60
        estimated_hours = estimated_minutes // 60
        remaining_minutes = estimated_minutes % 60

        if estimated_hours > 0:
            time_str = f'약 {estimated_hours}시간 {remaining_minutes}분'
        else:
            time_str = f'약 {estimated_minutes}분'

        reply = QMessageBox.warning(
            self, '경고',
            f'전체 {total_stocks}개 종목의 틱 데이터를 수집합니다.\n\n'
            f'⚠️ 예상 소요 시간: {time_str}\n'
            f'⚠️ API 호출 제한: 1초당 1종목 (순차 처리)\n'
            f'⚠️ 틱 데이터는 최근 600틱만 저장됩니다.\n\n'
            f'정말 계속하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # 전체 종목 코드 조회
        with session_scope() as session:
            stocks = session.query(Stock).all()
            stock_codes = [s.code for s in stocks]

        self._collect_tick_data_internal(stock_codes)

    def _collect_tick_data_internal(self, stock_codes):
        """Internal method to collect tick data"""
        count = self.tick_count_spin.value()

        reply = QMessageBox.question(
            self, '확인',
            f'틱 데이터를 수집합니다.\n'
            f'종목: {len(stock_codes)}개\n'
            f'개수: {count}틱\n'
            f'계속하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Reset statistics
        self.reset_stats()
        self.total_count_label.setText(str(len(stock_codes)))

        self.add_log(f"틱 데이터 수집 시작 ({len(stock_codes)}개 종목, {count}틱)...")
        self.set_buttons_enabled(False)

        progress = ProgressDialog("틱 데이터 수집 중", self)

        collector = StockCollector()
        self.worker = DataCollectionWorker(
            collector, 'tick_data',
            stock_codes=stock_codes, count=count
        )
        self.worker.progress.connect(progress.set_progress)
        self.worker.log.connect(progress.add_log)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(lambda r: self.on_collection_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_collection_error(progress, e))

        progress.rejected.connect(self.worker.stop)
        self.worker.start()
        progress.exec_()

    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable all buttons"""
        self.collect_stocks_btn.setEnabled(enabled)
        self.collect_all_btn.setEnabled(enabled)
        self.collect_single_btn.setEnabled(enabled)
        self.update_btn.setEnabled(enabled)
        self.collect_minute_selected_btn.setEnabled(enabled)
        self.collect_minute_all_btn.setEnabled(enabled)
        self.collect_tick_selected_btn.setEnabled(enabled)
        self.collect_tick_all_btn.setEnabled(enabled)
