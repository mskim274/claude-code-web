"""
Stock manager widget - view and manage stocks
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QGroupBox, QGridLayout)
from PyQt5.QtCore import pyqtSignal
from gui.components.stock_table import StockTableWidget
from db.database import session_scope
from db.models import Stock, DailyPrice
from sqlalchemy import func


class StockManagerWidget(QWidget):
    """Widget for managing stock list"""

    collect_stock_data = pyqtSignal(str)  # stock_code
    view_chart_requested = pyqtSignal(str)  # stock_code

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_stocks()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("종목 관리")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.load_stocks)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Stock table
        self.stock_table = StockTableWidget(self)
        self.stock_table.stock_selected.connect(self.on_stock_selected)
        self.stock_table.refresh_data = self.load_stocks
        layout.addWidget(self.stock_table)

        # Stock details panel
        details_group = QGroupBox("종목 상세정보")
        details_layout = QGridLayout()

        self.detail_code_label = QLabel("-")
        self.detail_name_label = QLabel("-")
        self.detail_market_label = QLabel("-")
        self.detail_records_label = QLabel("-")

        details_layout.addWidget(QLabel("종목코드:"), 0, 0)
        details_layout.addWidget(self.detail_code_label, 0, 1)
        details_layout.addWidget(QLabel("종목명:"), 0, 2)
        details_layout.addWidget(self.detail_name_label, 0, 3)
        details_layout.addWidget(QLabel("시장:"), 1, 0)
        details_layout.addWidget(self.detail_market_label, 1, 1)
        details_layout.addWidget(QLabel("데이터 레코드:"), 1, 2)
        details_layout.addWidget(self.detail_records_label, 1, 3)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Actions
        action_layout = QHBoxLayout()

        self.view_chart_btn = QPushButton("차트 보기")
        self.view_chart_btn.setEnabled(False)
        self.view_chart_btn.clicked.connect(self.on_view_chart)
        action_layout.addWidget(self.view_chart_btn)

        self.collect_data_btn = QPushButton("데이터 수집")
        self.collect_data_btn.setEnabled(False)
        self.collect_data_btn.clicked.connect(self.on_collect_data)
        action_layout.addWidget(self.collect_data_btn)

        self.run_backtest_btn = QPushButton("백테스트 실행")
        self.run_backtest_btn.setEnabled(False)
        self.run_backtest_btn.clicked.connect(self.on_run_backtest)
        action_layout.addWidget(self.run_backtest_btn)

        action_layout.addStretch()

        layout.addLayout(action_layout)

    def load_stocks(self):
        """Load stocks from database"""
        try:
            with session_scope() as session:
                stocks = session.query(Stock).all()

                stock_data = []
                for stock in stocks:
                    stock_data.append({
                        'code': stock.code,
                        'name': stock.name,
                        'market': stock.market,
                        'updated_at': stock.updated_at
                    })

                self.stock_table.load_stocks(stock_data)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"종목 로드 실패: {e}")

    def on_stock_selected(self, code: str, name: str):
        """Handle stock selection"""
        self.detail_code_label.setText(code)
        self.detail_name_label.setText(name)

        try:
            with session_scope() as session:
                stock = session.query(Stock).filter_by(code=code).first()

                if stock:
                    self.detail_market_label.setText(stock.market)

                    # Count records
                    records = session.query(DailyPrice).filter_by(stock_code=code).count()
                    self.detail_records_label.setText(str(records))

                    # Enable buttons
                    self.view_chart_btn.setEnabled(True)
                    self.collect_data_btn.setEnabled(True)
                    self.run_backtest_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "오류", f"종목 상세정보 로드 실패: {e}")

    def on_view_chart(self):
        """View stock chart"""
        code, name = self.stock_table.get_selected_stock()
        if code:
            self.view_chart_requested.emit(code)

    def on_collect_data(self):
        """Collect data for selected stock"""
        code, name = self.stock_table.get_selected_stock()
        if code:
            self.collect_stock_data.emit(code)

    def on_run_backtest(self):
        """Run backtest for selected stock"""
        code, name = self.stock_table.get_selected_stock()
        if code:
            # Switch to backtest tab with this stock
            # This will be implemented in main window
            pass
