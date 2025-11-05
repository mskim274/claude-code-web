"""
Backtest panel widget - run and view backtest results
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QLineEdit, QDateEdit, QSpinBox,
                             QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
                             QSplitter, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta
import pandas as pd

from gui.components.chart_widget import ChartWidget
from gui.utils.worker import BacktestWorker
from gui.components.progress_dialog import ProgressDialog
from backtest.engine import BacktestEngine
from backtest.strategy import MovingAverageCrossStrategy


class BacktestPanelWidget(QWidget):
    """Widget for running backtests"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.current_results = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("백테스트")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Configuration panel
        config_group = QGroupBox("백테스트 설정")
        config_layout = QVBoxLayout()

        # Stock selection
        stock_layout = QHBoxLayout()
        stock_layout.addWidget(QLabel("종목코드:"))
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("예: 005930")
        stock_layout.addWidget(self.stock_input)
        stock_layout.addStretch()
        config_layout.addLayout(stock_layout)

        # Date range
        date_layout = QHBoxLayout()

        date_layout.addWidget(QLabel("시작일:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("종료일:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)

        date_layout.addStretch()
        config_layout.addLayout(date_layout)

        # Strategy selection
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("전략:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['이동평균 교차'])
        strategy_layout.addWidget(self.strategy_combo)
        strategy_layout.addStretch()
        config_layout.addLayout(strategy_layout)

        # Strategy parameters
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("단기 이동평균:"))
        self.short_window_spin = QSpinBox()
        self.short_window_spin.setMinimum(5)
        self.short_window_spin.setMaximum(200)
        self.short_window_spin.setValue(20)
        params_layout.addWidget(self.short_window_spin)

        params_layout.addWidget(QLabel("장기 이동평균:"))
        self.long_window_spin = QSpinBox()
        self.long_window_spin.setMinimum(20)
        self.long_window_spin.setMaximum(500)
        self.long_window_spin.setValue(60)
        params_layout.addWidget(self.long_window_spin)

        params_layout.addStretch()
        config_layout.addLayout(params_layout)

        # Capital
        capital_layout = QHBoxLayout()
        capital_layout.addWidget(QLabel("초기 자본금:"))
        self.capital_spin = QSpinBox()
        self.capital_spin.setMinimum(1000000)
        self.capital_spin.setMaximum(1000000000)
        self.capital_spin.setSingleStep(1000000)
        self.capital_spin.setValue(10000000)
        capital_layout.addWidget(self.capital_spin)
        capital_layout.addStretch()
        config_layout.addLayout(capital_layout)

        # Run button
        self.run_btn = QPushButton("백테스트 실행")
        self.run_btn.clicked.connect(self.run_backtest)
        config_layout.addWidget(self.run_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Results panel
        splitter = QSplitter(Qt.Vertical)

        # Summary table
        summary_group = QGroupBox("결과 요약")
        summary_layout = QVBoxLayout()

        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(['지표', '값'])
        self.summary_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.summary_table.setMaximumHeight(200)
        summary_layout.addWidget(self.summary_table)

        summary_group.setLayout(summary_layout)
        splitter.addWidget(summary_group)

        # Chart
        chart_group = QGroupBox("자산 곡선")
        chart_layout = QVBoxLayout()

        self.chart = ChartWidget()
        chart_layout.addWidget(self.chart)

        chart_group.setLayout(chart_layout)
        splitter.addWidget(chart_group)

        layout.addWidget(splitter)

    def run_backtest(self):
        """Run backtest with current configuration"""
        stock_code = self.stock_input.text().strip()

        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목코드를 입력해주세요")
            return

        # Get dates
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        if start_date >= end_date:
            QMessageBox.warning(self, "날짜 오류", "시작일이 종료일보다 빨라야 합니다")
            return

        # Get parameters
        short_window = self.short_window_spin.value()
        long_window = self.long_window_spin.value()
        capital = self.capital_spin.value()

        if short_window >= long_window:
            QMessageBox.warning(self, "파라미터 오류",
                              "단기 이동평균이 장기 이동평균보다 작아야 합니다")
            return

        # Create strategy
        strategy = MovingAverageCrossStrategy(
            short_window=short_window,
            long_window=long_window
        )

        # Create engine
        engine = BacktestEngine(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital
        )

        # Run in worker thread
        self.run_btn.setEnabled(False)

        progress = ProgressDialog("백테스트 실행 중", self)
        progress.set_progress(10, f"{stock_code} 백테스트 초기화 중...")

        self.worker = BacktestWorker(engine, stock_code)
        self.worker.progress.connect(progress.set_progress)
        self.worker.finished.connect(lambda r: self.on_backtest_finished(progress, r))
        self.worker.error.connect(lambda e: self.on_backtest_error(progress, e))

        self.worker.start()
        progress.exec_()

    def on_backtest_finished(self, dialog, results):
        """Handle backtest completion"""
        dialog.on_complete(success=True)
        self.run_btn.setEnabled(True)
        self.current_results = results

        # Display results
        self.display_results(results)

    def on_backtest_error(self, dialog, error):
        """Handle backtest error"""
        dialog.on_error(error)
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "백테스트 오류", error)

    def display_results(self, results):
        """Display backtest results"""
        if not results:
            return

        # Summary table
        metrics = [
            ('초기 자본금', f"{results['initial_capital']:,.0f}"),
            ('최종 자산', f"{results['final_value']:,.0f}"),
            ('총 수익률', f"{results['total_return']:.2f}%"),
            ('총 거래 횟수', str(results['total_trades'])),
            ('수익 거래', str(results['winning_trades'])),
            ('손실 거래', str(results['losing_trades'])),
            ('승률', f"{results['win_rate']:.2f}%"),
            ('최대 낙폭(MDD)', f"{results['max_drawdown']:.2f}%"),
            ('샤프 비율', f"{results.get('sharpe_ratio', 0):.2f}"),
        ]

        self.summary_table.setRowCount(len(metrics))
        for i, (metric, value) in enumerate(metrics):
            self.summary_table.setItem(i, 0, QTableWidgetItem(metric))
            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(i, 1, value_item)

        # Chart
        self.chart.plot_backtest_results(results)

    def set_stock_code(self, code: str):
        """Set stock code from external source"""
        self.stock_input.setText(code)
