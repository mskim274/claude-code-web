"""
Stock detail widget - comprehensive stock information viewer
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QGroupBox, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QSplitter, QComboBox)
from PyQt5.QtCore import Qt
from datetime import datetime
import pandas as pd

from gui.components.chart_widget import ChartWidget
from db.database import session_scope
from db.models import Stock, DailyPrice, StockInfo


class StockDetailWidget(QWidget):
    """Widget for viewing comprehensive stock information"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stock_code = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title and search
        header_layout = QHBoxLayout()
        title = QLabel("종목 상세 정보")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        header_layout.addWidget(QLabel("종목코드:"))
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("예: 005930")
        self.stock_input.setMaximumWidth(150)
        header_layout.addWidget(self.stock_input)

        self.load_btn = QPushButton("조회")
        self.load_btn.clicked.connect(self.load_stock_info)
        header_layout.addWidget(self.load_btn)

        layout.addLayout(header_layout)

        # Main splitter
        splitter = QSplitter(Qt.Vertical)

        # Top section: Stock info + Statistics
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        # Stock basic info
        info_group = QGroupBox("기본 정보")
        info_layout = QGridLayout()

        self.code_label = QLabel("-")
        self.name_label = QLabel("-")
        self.market_label = QLabel("-")
        self.listing_date_label = QLabel("-")

        info_layout.addWidget(QLabel("종목코드:"), 0, 0)
        info_layout.addWidget(self.code_label, 0, 1)
        info_layout.addWidget(QLabel("종목명:"), 0, 2)
        info_layout.addWidget(self.name_label, 0, 3)
        info_layout.addWidget(QLabel("시장:"), 1, 0)
        info_layout.addWidget(self.market_label, 1, 1)
        info_layout.addWidget(QLabel("상장일:"), 1, 2)
        info_layout.addWidget(self.listing_date_label, 1, 3)

        info_group.setLayout(info_layout)
        top_layout.addWidget(info_group)

        # Data statistics
        stats_group = QGroupBox("수집 데이터 통계")
        stats_layout = QGridLayout()

        self.daily_count_label = QLabel("-")
        self.data_period_label = QLabel("-")
        self.last_update_label = QLabel("-")
        self.data_quality_label = QLabel("-")

        stats_layout.addWidget(QLabel("일봉 데이터:"), 0, 0)
        stats_layout.addWidget(self.daily_count_label, 0, 1)
        stats_layout.addWidget(QLabel("수집 기간:"), 0, 2)
        stats_layout.addWidget(self.data_period_label, 0, 3)
        stats_layout.addWidget(QLabel("최종 업데이트:"), 1, 0)
        stats_layout.addWidget(self.last_update_label, 1, 1)
        stats_layout.addWidget(QLabel("데이터 품질:"), 1, 2)
        stats_layout.addWidget(self.data_quality_label, 1, 3)

        stats_group.setLayout(stats_layout)
        top_layout.addWidget(stats_group)

        # Price statistics
        price_stats_group = QGroupBox("가격 통계")
        price_stats_layout = QGridLayout()

        self.current_price_label = QLabel("-")
        self.high_52w_label = QLabel("-")
        self.low_52w_label = QLabel("-")
        self.avg_volume_label = QLabel("-")

        price_stats_layout.addWidget(QLabel("현재가:"), 0, 0)
        price_stats_layout.addWidget(self.current_price_label, 0, 1)
        price_stats_layout.addWidget(QLabel("52주 최고:"), 0, 2)
        price_stats_layout.addWidget(self.high_52w_label, 0, 3)
        price_stats_layout.addWidget(QLabel("52주 최저:"), 1, 0)
        price_stats_layout.addWidget(self.low_52w_label, 1, 1)
        price_stats_layout.addWidget(QLabel("평균 거래량:"), 1, 2)
        price_stats_layout.addWidget(self.avg_volume_label, 1, 3)

        price_stats_group.setLayout(price_stats_layout)
        top_layout.addWidget(price_stats_group)

        splitter.addWidget(top_widget)

        # Middle section: Chart
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)

        chart_header = QHBoxLayout()
        chart_header.addWidget(QLabel("가격 차트"))
        chart_header.addStretch()

        chart_header.addWidget(QLabel("기간:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['1개월', '3개월', '6개월', '1년', '전체'])
        self.period_combo.setCurrentText('6개월')
        self.period_combo.currentTextChanged.connect(self.update_chart)
        chart_header.addWidget(self.period_combo)

        chart_layout.addLayout(chart_header)

        self.chart = ChartWidget()
        chart_layout.addWidget(self.chart)

        splitter.addWidget(chart_widget)

        # Bottom section: Recent price data
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)

        table_header = QHBoxLayout()
        table_header.addWidget(QLabel("최근 가격 데이터"))
        table_header.addStretch()

        self.export_btn = QPushButton("CSV 내보내기")
        self.export_btn.clicked.connect(self.export_to_csv)
        table_header.addWidget(self.export_btn)

        table_layout.addLayout(table_header)

        self.price_table = QTableWidget()
        self.price_table.setColumnCount(7)
        self.price_table.setHorizontalHeaderLabels(
            ['날짜', '시가', '고가', '저가', '종가', '거래량', '거래대금']
        )
        self.price_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.price_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.price_table)

        splitter.addWidget(table_widget)

        # Set splitter sizes
        splitter.setSizes([150, 400, 250])

        layout.addWidget(splitter)

    def load_stock_info(self):
        """Load comprehensive stock information"""
        stock_code = self.stock_input.text().strip()

        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력해주세요")
            return

        self.current_stock_code = stock_code

        try:
            with session_scope() as session:
                # Get stock info
                stock = session.query(Stock).filter_by(code=stock_code).first()

                if not stock:
                    QMessageBox.information(self, "종목 없음",
                                          f"{stock_code} 종목을 찾을 수 없습니다")
                    return

                # Basic info
                self.code_label.setText(stock.code)
                self.name_label.setText(stock.name)
                self.market_label.setText(stock.market or "-")
                self.listing_date_label.setText(
                    stock.listing_date.strftime('%Y-%m-%d') if stock.listing_date else "-"
                )

                # Get price data
                prices = session.query(DailyPrice).filter_by(
                    stock_code=stock_code
                ).order_by(DailyPrice.date.desc()).all()

                if not prices:
                    QMessageBox.information(self, "데이터 없음",
                                          f"{stock_code} 가격 데이터가 없습니다")
                    self._clear_data_display()
                    return

                # Data statistics
                self.daily_count_label.setText(f"{len(prices):,}개")

                oldest_date = min(p.date for p in prices)
                newest_date = max(p.date for p in prices)
                self.data_period_label.setText(
                    f"{oldest_date.strftime('%Y-%m-%d')} ~ {newest_date.strftime('%Y-%m-%d')}"
                )

                latest_price = prices[0]
                self.last_update_label.setText(
                    latest_price.created_at.strftime('%Y-%m-%d %H:%M')
                    if latest_price.created_at else "-"
                )

                # Data quality (simple: check for gaps)
                total_days = (newest_date - oldest_date).days
                expected_days = total_days * 5 / 7  # Rough estimate (weekdays)
                quality_pct = (len(prices) / expected_days * 100) if expected_days > 0 else 0
                self.data_quality_label.setText(f"{quality_pct:.1f}%")

                # Price statistics
                self.current_price_label.setText(f"{latest_price.close:,}원")

                # 52-week high/low
                year_ago = newest_date.replace(year=newest_date.year - 1)
                recent_prices = [p for p in prices if p.date >= year_ago]

                if recent_prices:
                    high_52w = max(p.high for p in recent_prices)
                    low_52w = min(p.low for p in recent_prices)
                    self.high_52w_label.setText(f"{high_52w:,}원")
                    self.low_52w_label.setText(f"{low_52w:,}원")

                    avg_volume = sum(p.volume for p in recent_prices) / len(recent_prices)
                    self.avg_volume_label.setText(f"{avg_volume:,.0f}")
                else:
                    self.high_52w_label.setText("-")
                    self.low_52w_label.setText("-")
                    self.avg_volume_label.setText("-")

                # Update chart
                self.update_chart()

                # Update price table (show recent 50 days)
                self._update_price_table(prices[:50])

        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 로드 실패: {e}")

    def update_chart(self):
        """Update chart based on selected period"""
        if not self.current_stock_code:
            return

        period_text = self.period_combo.currentText()

        # Calculate date range
        from datetime import timedelta
        end_date = datetime.now().date()

        if period_text == '1개월':
            start_date = end_date - timedelta(days=30)
        elif period_text == '3개월':
            start_date = end_date - timedelta(days=90)
        elif period_text == '6개월':
            start_date = end_date - timedelta(days=180)
        elif period_text == '1년':
            start_date = end_date - timedelta(days=365)
        else:  # 전체
            start_date = None

        try:
            with session_scope() as session:
                query = session.query(DailyPrice).filter_by(
                    stock_code=self.current_stock_code
                )

                if start_date:
                    query = query.filter(DailyPrice.date >= start_date)

                prices = query.order_by(DailyPrice.date).all()

                if not prices:
                    return

                # Convert to DataFrame
                data = []
                for p in prices:
                    data.append({
                        'date': p.date,
                        'open': p.open,
                        'high': p.high,
                        'low': p.low,
                        'close': p.close,
                        'volume': p.volume
                    })

                df = pd.DataFrame(data)
                df.set_index('date', inplace=True)

                # Plot candlestick
                stock_name = self.name_label.text()
                self.chart.plot_candlestick(
                    df,
                    title=f"{stock_name} ({self.current_stock_code}) - {period_text}"
                )

        except Exception as e:
            QMessageBox.critical(self, "오류", f"차트 업데이트 실패: {e}")

    def _update_price_table(self, prices):
        """Update price data table"""
        self.price_table.setRowCount(len(prices))

        for row, price in enumerate(prices):
            self.price_table.setItem(row, 0, QTableWidgetItem(
                price.date.strftime('%Y-%m-%d')
            ))
            self.price_table.setItem(row, 1, QTableWidgetItem(f"{price.open:,}"))
            self.price_table.setItem(row, 2, QTableWidgetItem(f"{price.high:,}"))
            self.price_table.setItem(row, 3, QTableWidgetItem(f"{price.low:,}"))
            self.price_table.setItem(row, 4, QTableWidgetItem(f"{price.close:,}"))
            self.price_table.setItem(row, 5, QTableWidgetItem(f"{price.volume:,}"))

            trading_value = price.trading_value if price.trading_value else 0
            self.price_table.setItem(row, 6, QTableWidgetItem(f"{trading_value:,}"))

    def _clear_data_display(self):
        """Clear all data displays"""
        self.daily_count_label.setText("-")
        self.data_period_label.setText("-")
        self.last_update_label.setText("-")
        self.data_quality_label.setText("-")
        self.current_price_label.setText("-")
        self.high_52w_label.setText("-")
        self.low_52w_label.setText("-")
        self.avg_volume_label.setText("-")
        self.price_table.setRowCount(0)
        self.chart.clear()

    def export_to_csv(self):
        """Export price data to CSV"""
        if not self.current_stock_code:
            QMessageBox.warning(self, "경고", "먼저 종목을 조회하세요")
            return

        from PyQt5.QtWidgets import QFileDialog
        import csv

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "CSV 저장",
            f"{self.current_stock_code}_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )

        if not filename:
            return

        try:
            with session_scope() as session:
                prices = session.query(DailyPrice).filter_by(
                    stock_code=self.current_stock_code
                ).order_by(DailyPrice.date.desc()).all()

                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['날짜', '시가', '고가', '저가', '종가', '거래량', '거래대금'])

                    for price in prices:
                        writer.writerow([
                            price.date.strftime('%Y-%m-%d'),
                            price.open,
                            price.high,
                            price.low,
                            price.close,
                            price.volume,
                            price.trading_value or 0
                        ])

            QMessageBox.information(self, "성공", f"CSV 파일로 저장되었습니다:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"CSV 내보내기 실패: {e}")

    def set_stock_code(self, code: str):
        """Set stock code from external source"""
        self.stock_input.setText(code)
        self.load_stock_info()
