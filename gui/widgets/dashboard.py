"""
Dashboard widget - main overview of the application
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from db.database import session_scope
from db.models import Stock, DailyPrice, CollectionLog
from sqlalchemy import func
from datetime import datetime


class DashboardWidget(QWidget):
    """Dashboard showing system overview and quick actions"""

    collect_stocks_clicked = pyqtSignal()
    collect_data_clicked = pyqtSignal()
    run_backtest_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_stats()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("키움증권 백테스팅 대시보드")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Stats section
        stats_group = QGroupBox("시스템 통계")
        stats_layout = QGridLayout()

        self.stock_count_label = QLabel("0")
        self.stock_count_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1976D2;")
        self.stock_count_label.setAlignment(Qt.AlignCenter)

        self.kospi_count_label = QLabel("KOSPI: 0")
        self.kospi_count_label.setAlignment(Qt.AlignCenter)

        self.kosdaq_count_label = QLabel("코스닥: 0")
        self.kosdaq_count_label.setAlignment(Qt.AlignCenter)

        stats_layout.addWidget(QLabel("전체 종목:"), 0, 0)
        stats_layout.addWidget(self.stock_count_label, 0, 1)
        stats_layout.addWidget(self.kospi_count_label, 1, 0)
        stats_layout.addWidget(self.kosdaq_count_label, 1, 1)

        self.data_count_label = QLabel("0")
        self.data_count_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        self.data_count_label.setAlignment(Qt.AlignCenter)

        stats_layout.addWidget(QLabel("가격 레코드:"), 0, 2)
        stats_layout.addWidget(self.data_count_label, 0, 3)

        self.last_update_label = QLabel("없음")
        self.last_update_label.setAlignment(Qt.AlignCenter)

        stats_layout.addWidget(QLabel("최근 업데이트:"), 1, 2)
        stats_layout.addWidget(self.last_update_label, 1, 3)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Recent activity
        activity_group = QGroupBox("최근 활동")
        activity_layout = QVBoxLayout()

        self.activity_text = QLabel("최근 활동이 없습니다")
        self.activity_text.setWordWrap(True)
        activity_layout.addWidget(self.activity_text)

        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)

        # Quick actions
        actions_group = QGroupBox("빠른 실행")
        actions_layout = QHBoxLayout()

        self.collect_stocks_btn = QPushButton("종목 리스트 수집")
        self.collect_stocks_btn.clicked.connect(self.collect_stocks_clicked.emit)
        actions_layout.addWidget(self.collect_stocks_btn)

        self.collect_data_btn = QPushButton("가격 데이터 수집")
        self.collect_data_btn.clicked.connect(self.collect_data_clicked.emit)
        actions_layout.addWidget(self.collect_data_btn)

        self.backtest_btn = QPushButton("백테스트 실행")
        self.backtest_btn.clicked.connect(self.run_backtest_clicked.emit)
        actions_layout.addWidget(self.backtest_btn)

        self.refresh_btn = QPushButton("통계 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_stats)
        actions_layout.addWidget(self.refresh_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()

    def refresh_stats(self):
        """Refresh statistics from database"""
        try:
            with session_scope() as session:
                # Stock counts
                total_stocks = session.query(Stock).count()
                kospi_stocks = session.query(Stock).filter_by(market='KOSPI').count()
                kosdaq_stocks = session.query(Stock).filter_by(market='KOSDAQ').count()

                self.stock_count_label.setText(str(total_stocks))
                self.kospi_count_label.setText(f"코스피: {kospi_stocks}")
                self.kosdaq_count_label.setText(f"코스닥: {kosdaq_stocks}")

                # Price data count
                price_count = session.query(DailyPrice).count()
                self.data_count_label.setText(f"{price_count:,}")

                # Last update
                last_stock = session.query(Stock).order_by(Stock.updated_at.desc()).first()
                if last_stock and last_stock.updated_at:
                    last_update = last_stock.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    self.last_update_label.setText(last_update)

                # Recent activity
                recent_logs = session.query(CollectionLog).order_by(
                    CollectionLog.started_at.desc()
                ).limit(5).all()

                if recent_logs:
                    activity_html = "<ul>"
                    for log in recent_logs:
                        status_color = 'green' if log.status == 'success' else 'red'
                        activity_html += f"<li><span style='color: {status_color};'>{log.collection_type}</span> - {log.started_at.strftime('%Y-%m-%d %H:%M')}</li>"
                    activity_html += "</ul>"
                    self.activity_text.setText(activity_html)

        except Exception as e:
            print(f"Error refreshing stats: {e}")
