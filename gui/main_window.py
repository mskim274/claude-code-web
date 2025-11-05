"""
Main window for the Kiwoom Stock Backtesting Application
"""

from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QAction, QMessageBox,
                             QApplication, QMenuBar, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from gui.widgets.dashboard import DashboardWidget
from gui.widgets.stock_manager import StockManagerWidget
from gui.widgets.data_collector import DataCollectorWidget
from gui.widgets.backtest_panel import BacktestPanelWidget
from gui.widgets.chart_viewer import ChartViewerWidget
from gui.widgets.settings import SettingsWidget
from gui.utils.theme import Theme
from db.database import init_db


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.is_dark_mode = False
        self.init_database()
        self.init_ui()
        self.apply_theme()

    def init_database(self):
        """Initialize database"""
        try:
            init_db()
        except Exception as e:
            QMessageBox.critical(self, "데이터베이스 오류",
                               f"데이터베이스 초기화 실패: {e}")

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("키움증권 주식 백테스팅 시스템")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create widgets
        self.dashboard = DashboardWidget()
        self.stock_manager = StockManagerWidget()
        self.data_collector = DataCollectorWidget()
        self.backtest_panel = BacktestPanelWidget()
        self.chart_viewer = ChartViewerWidget()
        self.settings = SettingsWidget()

        # Add tabs
        self.tabs.addTab(self.dashboard, "대시보드")
        self.tabs.addTab(self.stock_manager, "종목 관리")
        self.tabs.addTab(self.data_collector, "데이터 수집")
        self.tabs.addTab(self.backtest_panel, "백테스트")
        self.tabs.addTab(self.chart_viewer, "차트 뷰어")
        self.tabs.addTab(self.settings, "설정")

        # Connect signals
        self.connect_signals()

        # Create menu bar (after widgets are created)
        self.create_menu_bar()

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("준비 완료")

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('파일')

        exit_action = QAction('종료', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('보기')

        refresh_action = QAction('대시보드 새로고침', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.dashboard.refresh_stats)
        view_menu.addAction(refresh_action)

        view_menu.addSeparator()

        theme_action = QAction('다크모드 전환', self)
        theme_action.setShortcut('Ctrl+T')
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

        # Tools menu
        tools_menu = menubar.addMenu('도구')

        collect_stocks_action = QAction('종목 리스트 수집', self)
        collect_stocks_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.data_collector))
        tools_menu.addAction(collect_stocks_action)

        collect_data_action = QAction('가격 데이터 수집', self)
        collect_data_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.data_collector))
        tools_menu.addAction(collect_data_action)

        run_backtest_action = QAction('백테스트 실행', self)
        run_backtest_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.backtest_panel))
        tools_menu.addAction(run_backtest_action)

        # Help menu
        help_menu = menubar.addMenu('도움말')

        about_action = QAction('정보', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def connect_signals(self):
        """Connect widget signals"""
        # Dashboard quick actions
        self.dashboard.collect_stocks_clicked.connect(
            lambda: self.tabs.setCurrentWidget(self.data_collector)
        )
        self.dashboard.collect_data_clicked.connect(
            lambda: self.tabs.setCurrentWidget(self.data_collector)
        )
        self.dashboard.run_backtest_clicked.connect(
            lambda: self.tabs.setCurrentWidget(self.backtest_panel)
        )

        # Stock manager actions
        self.stock_manager.collect_stock_data.connect(self.collect_single_stock)

        # Settings theme change
        self.settings.theme_changed.connect(self.on_theme_changed)

    def collect_single_stock(self, stock_code: str):
        """Collect data for a single stock"""
        self.tabs.setCurrentWidget(self.data_collector)
        self.data_collector.stock_code_input.setText(stock_code)
        self.statusBar.showMessage(f"{stock_code} 데이터 수집 준비 완료")

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def on_theme_changed(self, is_dark: bool):
        """Handle theme change from settings"""
        self.is_dark_mode = is_dark
        self.apply_theme()

    def apply_theme(self):
        """Apply current theme"""
        app = QApplication.instance()

        if self.is_dark_mode:
            Theme.apply_dark_theme(app)
        else:
            Theme.apply_light_theme(app)

        stylesheet = Theme.get_stylesheet(self.is_dark_mode)
        self.setStyleSheet(stylesheet)

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>키움증권 주식 백테스팅 시스템</h2>
        <p>버전 1.0.0</p>
        <p>키움 API를 통해 주식 데이터를 수집하고
        다양한 트레이딩 전략으로 백테스팅을 수행하는 종합 시스템입니다.</p>
        <p><b>주요 기능:</b></p>
        <ul>
            <li>키움 API를 통한 주식 데이터 수집</li>
            <li>과거 가격 데이터 저장</li>
            <li>다양한 백테스팅 전략</li>
            <li>성과 분석 및 차트</li>
            <li>커스터마이징 가능한 파라미터</li>
        </ul>
        <p><b>사용 기술:</b> Python, PyQt5, SQLAlchemy, Matplotlib</p>
        """

        QMessageBox.about(self, "프로그램 정보", about_text)

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, '종료 확인',
            '정말로 종료하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
