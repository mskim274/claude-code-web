"""
Reusable stock table widget with search and filter
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QLineEdit, QComboBox, QPushButton,
                             QLabel, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class StockTableWidget(QWidget):
    """Table widget for displaying stock list with search and filter"""

    stock_selected = pyqtSignal(str, str)  # code, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stocks_data = []
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Search and filter bar
        filter_layout = QHBoxLayout()

        # Search box
        filter_layout.addWidget(QLabel("검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("종목코드 또는 이름...")
        self.search_input.textChanged.connect(self.filter_stocks)
        filter_layout.addWidget(self.search_input)

        # Market filter
        filter_layout.addWidget(QLabel("시장:"))
        self.market_combo = QComboBox()
        self.market_combo.addItems(['전체', '코스피', '코스닥'])
        self.market_combo.currentTextChanged.connect(self.filter_stocks)
        filter_layout.addWidget(self.market_combo)

        # Refresh button
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(self.refresh_btn)

        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Stock table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['종목코드', '종목명', '시장', '업데이트'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)

        layout.addWidget(self.table)

        # Status label
        self.status_label = QLabel("데이터가 로드되지 않았습니다")
        layout.addWidget(self.status_label)

    def load_stocks(self, stocks):
        """Load stock data into table"""
        self.stocks_data = stocks
        self.filter_stocks()

    def filter_stocks(self):
        """Filter stocks based on search and market selection"""
        search_text = self.search_input.text().lower()
        market_filter = self.market_combo.currentText()

        filtered = self.stocks_data

        # Apply market filter
        if market_filter == '코스피':
            filtered = [s for s in filtered if s.get('market') == 'KOSPI']
        elif market_filter == '코스닥':
            filtered = [s for s in filtered if s.get('market') == 'KOSDAQ']
        # '전체'인 경우는 필터링하지 않음

        # Apply search filter
        if search_text:
            filtered = [s for s in filtered if
                       search_text in s.get('code', '').lower() or
                       search_text in s.get('name', '').lower()]

        self.display_stocks(filtered)

    def display_stocks(self, stocks):
        """Display stocks in table"""
        self.table.setRowCount(len(stocks))

        for row, stock in enumerate(stocks):
            self.table.setItem(row, 0, QTableWidgetItem(stock.get('code', '')))
            self.table.setItem(row, 1, QTableWidgetItem(stock.get('name', '')))

            market_item = QTableWidgetItem(stock.get('market', ''))
            if stock.get('market') == 'KOSPI':
                market_item.setBackground(QColor(100, 150, 255, 50))
            else:
                market_item.setBackground(QColor(255, 150, 100, 50))
            self.table.setItem(row, 2, market_item)

            updated = stock.get('updated_at', '')
            if updated:
                updated = str(updated)[:19]
            self.table.setItem(row, 3, QTableWidgetItem(updated))

        self.status_label.setText(f"{len(stocks)}개 종목 표시 중")

    def on_item_double_clicked(self, item):
        """Handle item double click"""
        row = item.row()
        code = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        self.stock_selected.emit(code, name)

    def refresh_data(self):
        """Refresh data (to be implemented by parent)"""
        pass

    def get_selected_stock(self):
        """Get currently selected stock"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            code = self.table.item(current_row, 0).text()
            name = self.table.item(current_row, 1).text()
            return code, name
        return None, None
