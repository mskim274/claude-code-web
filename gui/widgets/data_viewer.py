"""
Data viewer widget for displaying collected minute and tick data
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QLabel, QLineEdit, QPushButton, QDateEdit,
                             QComboBox, QTabWidget, QMessageBox, QSpinBox)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta

from db.database import session_scope
from db.models import MinutePrice, TickPrice, Stock


class DataViewerWidget(QWidget):
    """Widget for viewing collected minute and tick data"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tabs for different data types
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Minute data tab
        self.minute_tab = self.create_minute_tab()
        self.tabs.addTab(self.minute_tab, "분봉 데이터")

        # Tick data tab
        self.tick_tab = self.create_tick_tab()
        self.tabs.addTab(self.tick_tab, "틱 데이터")

    def create_minute_tab(self):
        """Create minute data viewer tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Filter controls
        filter_group = QGroupBox("조회 조건")
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)

        # Stock code filter
        filter_layout.addWidget(QLabel("종목코드:"))
        self.minute_stock_code = QLineEdit()
        self.minute_stock_code.setPlaceholderText("예: 005930 (전체는 비워두세요)")
        self.minute_stock_code.setMaximumWidth(200)
        filter_layout.addWidget(self.minute_stock_code)

        # Interval filter
        filter_layout.addWidget(QLabel("분봉 간격:"))
        self.minute_interval = QComboBox()
        self.minute_interval.addItems(["전체", "1분", "5분", "10분", "30분", "60분"])
        self.minute_interval.setMaximumWidth(100)
        filter_layout.addWidget(self.minute_interval)

        # Date range
        filter_layout.addWidget(QLabel("시작일:"))
        self.minute_start_date = QDateEdit()
        self.minute_start_date.setDate(QDate.currentDate().addDays(-7))
        self.minute_start_date.setCalendarPopup(True)
        self.minute_start_date.setMaximumWidth(120)
        filter_layout.addWidget(self.minute_start_date)

        filter_layout.addWidget(QLabel("종료일:"))
        self.minute_end_date = QDateEdit()
        self.minute_end_date.setDate(QDate.currentDate())
        self.minute_end_date.setCalendarPopup(True)
        self.minute_end_date.setMaximumWidth(120)
        filter_layout.addWidget(self.minute_end_date)

        # Limit
        filter_layout.addWidget(QLabel("조회 개수:"))
        self.minute_limit = QSpinBox()
        self.minute_limit.setRange(10, 10000)
        self.minute_limit.setValue(100)
        self.minute_limit.setMaximumWidth(100)
        filter_layout.addWidget(self.minute_limit)

        # Query button
        self.minute_query_btn = QPushButton("조회")
        self.minute_query_btn.clicked.connect(self.query_minute_data)
        self.minute_query_btn.setMaximumWidth(80)
        filter_layout.addWidget(self.minute_query_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Statistics display
        self.minute_stats_label = QLabel("통계 정보: 조회 버튼을 클릭하세요")
        layout.addWidget(self.minute_stats_label)

        # Data table
        self.minute_table = QTableWidget()
        self.minute_table.setColumnCount(9)
        self.minute_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "일시", "간격", "시가", "고가", "저가", "종가", "거래량"
        ])
        self.minute_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.minute_table.setAlternatingRowColors(True)
        self.minute_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.minute_table)

        return widget

    def create_tick_tab(self):
        """Create tick data viewer tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Filter controls
        filter_group = QGroupBox("조회 조건")
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)

        # Stock code filter
        filter_layout.addWidget(QLabel("종목코드:"))
        self.tick_stock_code = QLineEdit()
        self.tick_stock_code.setPlaceholderText("예: 005930 (전체는 비워두세요)")
        self.tick_stock_code.setMaximumWidth(200)
        filter_layout.addWidget(self.tick_stock_code)

        # Date range
        filter_layout.addWidget(QLabel("시작일:"))
        self.tick_start_date = QDateEdit()
        self.tick_start_date.setDate(QDate.currentDate().addDays(-1))
        self.tick_start_date.setCalendarPopup(True)
        self.tick_start_date.setMaximumWidth(120)
        filter_layout.addWidget(self.tick_start_date)

        filter_layout.addWidget(QLabel("종료일:"))
        self.tick_end_date = QDateEdit()
        self.tick_end_date.setDate(QDate.currentDate())
        self.tick_end_date.setCalendarPopup(True)
        self.tick_end_date.setMaximumWidth(120)
        filter_layout.addWidget(self.tick_end_date)

        # Limit
        filter_layout.addWidget(QLabel("조회 개수:"))
        self.tick_limit = QSpinBox()
        self.tick_limit.setRange(10, 10000)
        self.tick_limit.setValue(100)
        self.tick_limit.setMaximumWidth(100)
        filter_layout.addWidget(self.tick_limit)

        # Query button
        self.tick_query_btn = QPushButton("조회")
        self.tick_query_btn.clicked.connect(self.query_tick_data)
        self.tick_query_btn.setMaximumWidth(80)
        filter_layout.addWidget(self.tick_query_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Statistics display
        self.tick_stats_label = QLabel("통계 정보: 조회 버튼을 클릭하세요")
        layout.addWidget(self.tick_stats_label)

        # Data table
        self.tick_table = QTableWidget()
        self.tick_table.setColumnCount(7)
        self.tick_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "체결시간", "체결가", "체결량", "전일대비", "매도호가"
        ])
        self.tick_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tick_table.setAlternatingRowColors(True)
        self.tick_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tick_table)

        return widget

    def query_minute_data(self):
        """Query and display minute data"""
        try:
            # Get filter values
            stock_code = self.minute_stock_code.text().strip()
            interval_text = self.minute_interval.currentText()
            start_date = self.minute_start_date.date().toPyDate()
            end_date = self.minute_end_date.date().toPyDate()
            limit = self.minute_limit.value()

            # Convert interval text to number
            interval_map = {
                "전체": None,
                "1분": 1,
                "5분": 5,
                "10분": 10,
                "30분": 30,
                "60분": 60
            }
            interval = interval_map.get(interval_text)

            # Query database
            with session_scope() as session:
                query = session.query(MinutePrice, Stock).join(
                    Stock, MinutePrice.stock_code == Stock.code
                )

                # Apply filters
                if stock_code:
                    query = query.filter(MinutePrice.stock_code == stock_code)

                if interval is not None:
                    query = query.filter(MinutePrice.interval == interval)

                query = query.filter(MinutePrice.datetime >= datetime.combine(start_date, datetime.min.time()))
                query = query.filter(MinutePrice.datetime <= datetime.combine(end_date, datetime.max.time()))

                # Order by datetime descending and limit
                query = query.order_by(MinutePrice.datetime.desc()).limit(limit)

                results = query.all()

                # Update statistics
                total_count = session.query(MinutePrice).count()
                filtered_count = len(results)

                stats_text = f"총 레코드: {total_count:,}개 | 조회된 레코드: {filtered_count:,}개"
                if results:
                    latest_date = results[0][0].datetime.strftime("%Y-%m-%d %H:%M:%S")
                    stats_text += f" | 최신 데이터: {latest_date}"

                self.minute_stats_label.setText(stats_text)

                # Update table
                self.minute_table.setRowCount(filtered_count)
                for row, (minute_price, stock) in enumerate(results):
                    self.minute_table.setItem(row, 0, QTableWidgetItem(minute_price.stock_code))
                    self.minute_table.setItem(row, 1, QTableWidgetItem(stock.name))
                    self.minute_table.setItem(row, 2, QTableWidgetItem(
                        minute_price.datetime.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    self.minute_table.setItem(row, 3, QTableWidgetItem(f"{minute_price.interval}분"))
                    self.minute_table.setItem(row, 4, QTableWidgetItem(f"{minute_price.open:,}"))
                    self.minute_table.setItem(row, 5, QTableWidgetItem(f"{minute_price.high:,}"))
                    self.minute_table.setItem(row, 6, QTableWidgetItem(f"{minute_price.low:,}"))
                    self.minute_table.setItem(row, 7, QTableWidgetItem(f"{minute_price.close:,}"))
                    self.minute_table.setItem(row, 8, QTableWidgetItem(f"{minute_price.volume:,}"))

                    # Center align numeric columns
                    for col in range(4, 9):
                        self.minute_table.item(row, col).setTextAlignment(Qt.AlignCenter)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"분봉 데이터 조회 중 오류 발생:\n{str(e)}")

    def query_tick_data(self):
        """Query and display tick data"""
        try:
            # Get filter values
            stock_code = self.tick_stock_code.text().strip()
            start_date = self.tick_start_date.date().toPyDate()
            end_date = self.tick_end_date.date().toPyDate()
            limit = self.tick_limit.value()

            # Query database
            with session_scope() as session:
                query = session.query(TickPrice, Stock).join(
                    Stock, TickPrice.stock_code == Stock.code
                )

                # Apply filters
                if stock_code:
                    query = query.filter(TickPrice.stock_code == stock_code)

                query = query.filter(TickPrice.datetime >= datetime.combine(start_date, datetime.min.time()))
                query = query.filter(TickPrice.datetime <= datetime.combine(end_date, datetime.max.time()))

                # Order by datetime descending and limit
                query = query.order_by(TickPrice.datetime.desc()).limit(limit)

                results = query.all()

                # Update statistics
                total_count = session.query(TickPrice).count()
                filtered_count = len(results)

                stats_text = f"총 레코드: {total_count:,}개 | 조회된 레코드: {filtered_count:,}개"
                if results:
                    latest_date = results[0][0].datetime.strftime("%Y-%m-%d %H:%M:%S")
                    stats_text += f" | 최신 데이터: {latest_date}"

                self.tick_stats_label.setText(stats_text)

                # Update table
                self.tick_table.setRowCount(filtered_count)
                for row, (tick_price, stock) in enumerate(results):
                    self.tick_table.setItem(row, 0, QTableWidgetItem(tick_price.stock_code))
                    self.tick_table.setItem(row, 1, QTableWidgetItem(stock.name))
                    self.tick_table.setItem(row, 2, QTableWidgetItem(
                        tick_price.datetime.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    self.tick_table.setItem(row, 3, QTableWidgetItem(f"{tick_price.price:,}"))
                    self.tick_table.setItem(row, 4, QTableWidgetItem(f"{tick_price.volume:,}"))

                    change_text = f"{tick_price.change:,}" if tick_price.change else "-"
                    self.tick_table.setItem(row, 5, QTableWidgetItem(change_text))

                    ask_text = f"{tick_price.ask_volume:,}" if tick_price.ask_volume else "-"
                    self.tick_table.setItem(row, 6, QTableWidgetItem(ask_text))

                    # Center align numeric columns
                    for col in range(3, 7):
                        self.tick_table.item(row, col).setTextAlignment(Qt.AlignCenter)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"틱 데이터 조회 중 오류 발생:\n{str(e)}")

    def refresh_current_tab(self):
        """Refresh data for current tab"""
        current_index = self.tabs.currentIndex()
        if current_index == 0:  # Minute data tab
            self.query_minute_data()
        elif current_index == 1:  # Tick data tab
            self.query_tick_data()
