"""
Theme management for the GUI application
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt


class Theme:
    """Theme manager for light and dark modes"""

    LIGHT_THEME = {
        'background': '#FFFFFF',
        'surface': '#F5F5F5',
        'primary': '#1976D2',
        'secondary': '#424242',
        'text': '#212121',
        'text_secondary': '#757575',
        'border': '#E0E0E0',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336',
        'chart_bg': '#FFFFFF',
    }

    DARK_THEME = {
        'background': '#1E1E1E',
        'surface': '#2D2D2D',
        'primary': '#2196F3',
        'secondary': '#90CAF9',
        'text': '#E0E0E0',
        'text_secondary': '#A0A0A0',
        'border': '#404040',
        'success': '#66BB6A',
        'warning': '#FFA726',
        'error': '#EF5350',
        'chart_bg': '#2D2D2D',
    }

    @staticmethod
    def apply_light_theme(app: QApplication):
        """Apply light theme to the application"""
        app.setStyle("Fusion")
        palette = QPalette()

        palette.setColor(QPalette.Window, QColor(Theme.LIGHT_THEME['background']))
        palette.setColor(QPalette.WindowText, QColor(Theme.LIGHT_THEME['text']))
        palette.setColor(QPalette.Base, QColor(Theme.LIGHT_THEME['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(Theme.LIGHT_THEME['background']))
        palette.setColor(QPalette.ToolTipBase, QColor(Theme.LIGHT_THEME['surface']))
        palette.setColor(QPalette.ToolTipText, QColor(Theme.LIGHT_THEME['text']))
        palette.setColor(QPalette.Text, QColor(Theme.LIGHT_THEME['text']))
        palette.setColor(QPalette.Button, QColor(Theme.LIGHT_THEME['surface']))
        palette.setColor(QPalette.ButtonText, QColor(Theme.LIGHT_THEME['text']))
        palette.setColor(QPalette.Link, QColor(Theme.LIGHT_THEME['primary']))
        palette.setColor(QPalette.Highlight, QColor(Theme.LIGHT_THEME['primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)

        app.setPalette(palette)

    @staticmethod
    def apply_dark_theme(app: QApplication):
        """Apply dark theme to the application"""
        app.setStyle("Fusion")
        palette = QPalette()

        palette.setColor(QPalette.Window, QColor(Theme.DARK_THEME['background']))
        palette.setColor(QPalette.WindowText, QColor(Theme.DARK_THEME['text']))
        palette.setColor(QPalette.Base, QColor(Theme.DARK_THEME['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(Theme.DARK_THEME['background']))
        palette.setColor(QPalette.ToolTipBase, QColor(Theme.DARK_THEME['surface']))
        palette.setColor(QPalette.ToolTipText, QColor(Theme.DARK_THEME['text']))
        palette.setColor(QPalette.Text, QColor(Theme.DARK_THEME['text']))
        palette.setColor(QPalette.Button, QColor(Theme.DARK_THEME['surface']))
        palette.setColor(QPalette.ButtonText, QColor(Theme.DARK_THEME['text']))
        palette.setColor(QPalette.Link, QColor(Theme.DARK_THEME['primary']))
        palette.setColor(QPalette.Highlight, QColor(Theme.DARK_THEME['primary']))
        palette.setColor(QPalette.HighlightedText, Qt.black)

        app.setPalette(palette)

    @staticmethod
    def get_stylesheet(is_dark=False):
        """Get custom stylesheet for widgets"""
        theme = Theme.DARK_THEME if is_dark else Theme.LIGHT_THEME

        return f"""
        QMainWindow {{
            background-color: {theme['background']};
        }}

        QTabWidget::pane {{
            border: 1px solid {theme['border']};
            background-color: {theme['surface']};
        }}

        QTabBar::tab {{
            background-color: {theme['surface']};
            color: {theme['text']};
            padding: 8px 16px;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {theme['primary']};
            color: white;
        }}

        QPushButton {{
            background-color: {theme['primary']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {theme['secondary']};
        }}

        QPushButton:pressed {{
            background-color: {theme['border']};
        }}

        QPushButton:disabled {{
            background-color: {theme['border']};
            color: {theme['text_secondary']};
        }}

        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {theme['surface']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: 4px;
            border-radius: 2px;
        }}

        QTableWidget {{
            background-color: {theme['surface']};
            alternate-background-color: {theme['background']};
            gridline-color: {theme['border']};
        }}

        QHeaderView::section {{
            background-color: {theme['primary']};
            color: white;
            padding: 4px;
            border: none;
            font-weight: bold;
        }}

        QProgressBar {{
            border: 1px solid {theme['border']};
            border-radius: 4px;
            text-align: center;
            background-color: {theme['surface']};
        }}

        QProgressBar::chunk {{
            background-color: {theme['success']};
            border-radius: 3px;
        }}
        """
