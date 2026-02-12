"""
CashMonitor – Personal Finance Tracker
Entry point for the PySide6 application.
"""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from main_window import MainWindow


def get_resource_path(relative_path: str) -> Path:
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


def load_stylesheet() -> str:
    """Load the QSS stylesheet."""
    qss_path = get_resource_path("style.qss")
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""


def main():
    app = QApplication(sys.argv)

    # Set default font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply dark stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
