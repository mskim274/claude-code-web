"""
Progress dialog for long-running operations
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QProgressBar, QTextEdit,
                             QPushButton, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt


class ProgressDialog(QDialog):
    """Dialog showing progress of long-running operations"""

    def __init__(self, title="Processing", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 400)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel("초기화 중...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Log output
        log_label = QLabel("로그:")
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def set_progress(self, value: int, message: str = ""):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def add_log(self, message: str):
        """Add log message"""
        self.log_output.append(message)

    def on_cancel(self):
        """Handle cancel button"""
        self.reject()

    def on_complete(self, success=True):
        """Handle completion"""
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

        if success:
            self.status_label.setText("성공적으로 완료되었습니다!")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText("실패했습니다!")

    def on_error(self, error_msg: str):
        """Handle error"""
        self.add_log(f"오류: {error_msg}")
        self.on_complete(success=False)
