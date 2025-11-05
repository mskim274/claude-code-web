"""
Chart viewer widget - view stock price charts
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QDateEdit, QMessageBox,
                             QComboBox, QCheckBox)
from PyQt5.QtCore import QDate
import pandas as pd
from datetime import datetime

from gui.components.chart_widget import ChartWidget
from db.database import session_scope
from db.models import DailyPrice


class ChartViewerWidget(QWidget):
    """Widget for viewing stock price charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("주식 차트 뷰어")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Controls
        control_layout = QHBoxLayout()

        # Stock selection
        control_layout.addWidget(QLabel("종목코드:"))
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("예: 005930")
        control_layout.addWidget(self.stock_input)

        # Date range
        control_layout.addWidget(QLabel("시작:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-6))
        control_layout.addWidget(self.start_date)

        control_layout.addWidget(QLabel("종료:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        control_layout.addWidget(self.end_date)

        # Chart type
        control_layout.addWidget(QLabel("타입:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(['캔들스틱', '라인'])
        control_layout.addWidget(self.chart_type_combo)

        # Load button
        self.load_btn = QPushButton("차트 로드")
        self.load_btn.clicked.connect(self.load_chart)
        control_layout.addWidget(self.load_btn)

        control_layout.addStretch()

        layout.addLayout(control_layout)

        # Options
        options_layout = QHBoxLayout()

        self.show_ma_check = QCheckBox("이동평균선 표시")
        self.show_ma_check.setChecked(True)
        options_layout.addWidget(self.show_ma_check)

        self.show_volume_check = QCheckBox("거래량 표시")
        self.show_volume_check.setChecked(True)
        options_layout.addWidget(self.show_volume_check)

        options_layout.addStretch()

        layout.addLayout(options_layout)

        # Chart
        self.chart = ChartWidget()
        layout.addWidget(self.chart)

    def load_chart(self):
        """Load and display chart"""
        stock_code = self.stock_input.text().strip()

        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력해주세요")
            return

        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        if start_date >= end_date:
            QMessageBox.warning(self, "날짜 오류", "시작일이 종료일보다 빨라야 합니다")
            return

        try:
            # Load data from database
            with session_scope() as session:
                prices = session.query(DailyPrice).filter(
                    DailyPrice.stock_code == stock_code,
                    DailyPrice.date >= start_date,
                    DailyPrice.date <= end_date
                ).order_by(DailyPrice.date).all()

                if not prices:
                    QMessageBox.information(self, "데이터 없음",
                                          f"{stock_code} 가격 데이터를 찾을 수 없습니다")
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

                # Add moving averages if requested
                if self.show_ma_check.isChecked():
                    df['MA20'] = df['close'].rolling(window=20).mean()
                    df['MA60'] = df['close'].rolling(window=60).mean()

                # Plot chart
                chart_type = self.chart_type_combo.currentText()

                if chart_type == '캔들스틱':
                    self.chart.plot_candlestick(df, title=f"{stock_code} 가격 차트")
                else:
                    columns = ['close']
                    if self.show_ma_check.isChecked():
                        columns.extend(['MA20', 'MA60'])
                    self.chart.plot_line(df, columns, title=f"{stock_code} 가격 차트")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"차트 로드 실패: {e}")

    def set_stock_code(self, code: str):
        """Set stock code from external source"""
        self.stock_input.setText(code)
        self.load_chart()
