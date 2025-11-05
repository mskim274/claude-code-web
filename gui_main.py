"""
GUI Launcher for Kiwoom Stock Backtesting System
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.main_window import MainWindow
from utils.logger import setup_logger

logger = setup_logger('gui')


def main():
    """Main entry point for GUI application"""
    try:
        # Enable high DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Kiwoom Stock Backtesting")
        app.setOrganizationName("KiwoomBacktest")

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.info("GUI application started")

        # Run event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"Failed to start GUI: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
