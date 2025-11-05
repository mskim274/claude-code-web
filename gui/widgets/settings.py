"""
Settings widget - application settings
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QLineEdit, QComboBox,
                             QSpinBox, QCheckBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import pyqtSignal
import os
from config.kiwoom_config import KiwoomConfig


class SettingsWidget(QWidget):
    """Widget for application settings"""

    theme_changed = pyqtSignal(bool)  # is_dark

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("설정")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Database settings
        db_group = QGroupBox("데이터베이스 설정")
        db_layout = QVBoxLayout()

        db_type_layout = QHBoxLayout()
        db_type_layout.addWidget(QLabel("데이터베이스 타입:"))
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(['SQLite', 'PostgreSQL'])
        db_type_layout.addWidget(self.db_type_combo)
        db_type_layout.addStretch()
        db_layout.addLayout(db_type_layout)

        # PostgreSQL settings
        self.pg_host_input = QLineEdit()
        self.pg_port_input = QLineEdit()
        self.pg_user_input = QLineEdit()
        self.pg_pass_input = QLineEdit()
        self.pg_pass_input.setEchoMode(QLineEdit.Password)
        self.pg_db_input = QLineEdit()

        pg_layout = QHBoxLayout()
        pg_layout.addWidget(QLabel("호스트:"))
        pg_layout.addWidget(self.pg_host_input)
        pg_layout.addWidget(QLabel("포트:"))
        pg_layout.addWidget(self.pg_port_input)
        db_layout.addLayout(pg_layout)

        pg_layout2 = QHBoxLayout()
        pg_layout2.addWidget(QLabel("사용자:"))
        pg_layout2.addWidget(self.pg_user_input)
        pg_layout2.addWidget(QLabel("비밀번호:"))
        pg_layout2.addWidget(self.pg_pass_input)
        db_layout.addLayout(pg_layout2)

        pg_layout3 = QHBoxLayout()
        pg_layout3.addWidget(QLabel("데이터베이스:"))
        pg_layout3.addWidget(self.pg_db_input)
        pg_layout3.addStretch()
        db_layout.addLayout(pg_layout3)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Logging settings
        log_group = QGroupBox("로깅")
        log_layout = QVBoxLayout()

        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("로그 레벨:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        log_layout.addLayout(log_level_layout)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Data collection settings
        collection_group = QGroupBox("데이터 수집")
        collection_layout = QVBoxLayout()

        years_layout = QHBoxLayout()
        years_layout.addWidget(QLabel("기본 수집 기간(년):"))
        self.years_spin = QSpinBox()
        self.years_spin.setMinimum(1)
        self.years_spin.setMaximum(20)
        self.years_spin.setValue(5)
        years_layout.addWidget(self.years_spin)
        years_layout.addStretch()
        collection_layout.addLayout(years_layout)

        collection_group.setLayout(collection_layout)
        layout.addWidget(collection_group)

        # Appearance settings
        appearance_group = QGroupBox("외관")
        appearance_layout = QVBoxLayout()

        self.dark_mode_check = QCheckBox("다크 모드")
        self.dark_mode_check.stateChanged.connect(
            lambda state: self.theme_changed.emit(state == 2)
        )
        appearance_layout.addWidget(self.dark_mode_check)

        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("설정 저장")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("기본값으로 초기화")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        layout.addStretch()

    def load_settings(self):
        """Load current settings"""
        # Database
        db_type = os.getenv('DB_TYPE', 'sqlite')
        if db_type.lower() == 'sqlite':
            self.db_type_combo.setCurrentText('SQLite')
        else:
            self.db_type_combo.setCurrentText('PostgreSQL')

        self.pg_host_input.setText(os.getenv('POSTGRES_HOST', 'localhost'))
        self.pg_port_input.setText(os.getenv('POSTGRES_PORT', '5432'))
        self.pg_user_input.setText(os.getenv('POSTGRES_USER', 'postgres'))
        self.pg_db_input.setText(os.getenv('POSTGRES_DB', 'stock_backtest'))

        # Logging
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_level_combo.setCurrentText(log_level)

        # Data collection
        years = int(os.getenv('YEARS_TO_COLLECT', '5'))
        self.years_spin.setValue(years)

    def save_settings(self):
        """Save settings to .env file"""
        try:
            settings = []

            # Database
            db_type = 'sqlite' if self.db_type_combo.currentText() == 'SQLite' else 'postgresql'
            settings.append(f"DB_TYPE={db_type}")

            if db_type == 'postgresql':
                settings.append(f"POSTGRES_HOST={self.pg_host_input.text()}")
                settings.append(f"POSTGRES_PORT={self.pg_port_input.text()}")
                settings.append(f"POSTGRES_USER={self.pg_user_input.text()}")
                if self.pg_pass_input.text():
                    settings.append(f"POSTGRES_PASSWORD={self.pg_pass_input.text()}")
                settings.append(f"POSTGRES_DB={self.pg_db_input.text()}")

            # Logging
            settings.append(f"LOG_LEVEL={self.log_level_combo.currentText()}")

            # Data collection
            settings.append(f"YEARS_TO_COLLECT={self.years_spin.value()}")

            # Write to .env file
            with open('.env', 'w') as f:
                f.write('\n'.join(settings))

            QMessageBox.information(self, "성공",
                                  "설정이 성공적으로 저장되었습니다!\n변경사항 적용을 위해 프로그램을 재시작해주세요.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패: {e}")

    def reset_settings(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self, '초기화 확인',
            '모든 설정을 기본값으로 초기화하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.db_type_combo.setCurrentText('SQLite')
            self.pg_host_input.setText('localhost')
            self.pg_port_input.setText('5432')
            self.pg_user_input.setText('postgres')
            self.pg_pass_input.clear()
            self.pg_db_input.setText('stock_backtest')
            self.log_level_combo.setCurrentText('INFO')
            self.years_spin.setValue(5)
            self.dark_mode_check.setChecked(False)
