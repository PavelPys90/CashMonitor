"""
CashMonitor – About Dialog
Displays application information, version, and credits.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


APP_NAME = "CashMonitor"
APP_VERSION = "1.4.1"
APP_AUTHOR = "Pavel Pys"
APP_YEAR = "2026"
APP_DESCRIPTION = "Persönlicher Finanz-Tracker zur Verwaltung monatlicher Ein- und Ausgaben."
APP_TECH = "Python · PySide6 · QtCharts · JSON"
APP_LICENSE = "MIT License"


class AboutDialog(QDialog):
    """About / Info dialog for CashMonitor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Über {APP_NAME}")
        self.setFixedSize(460, 420)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(32, 28, 32, 24)

        # ── App Icon / Title ──
        icon_label = QLabel("💰")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(40)
        icon_label.setFont(icon_font)
        layout.addWidget(icon_label)

        # App Name
        name_label = QLabel(APP_NAME)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_font = QFont()
        name_font.setPointSize(22)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #4cc9f0;")
        layout.addWidget(name_label)

        # Version
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #8892b0; font-size: 13px;")
        layout.addWidget(version_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        # Description
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #ccd6f6; font-size: 13px; padding: 4px 0;")
        layout.addWidget(desc_label)

        # ── Info Grid ──
        info_frame = QFrame()
        info_frame.setObjectName("summaryCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(16, 12, 16, 12)

        info_layout.addLayout(self._info_row("Entwickler", APP_AUTHOR))
        info_layout.addLayout(self._info_row("Technologie", APP_TECH))
        info_layout.addLayout(self._info_row("Lizenz", APP_LICENSE))
        info_layout.addLayout(self._info_row("Jahr", APP_YEAR))

        layout.addWidget(info_frame)

        layout.addStretch()

        # ── Copyright ──
        copy_label = QLabel(f"© {APP_YEAR} {APP_AUTHOR}. Alle Rechte vorbehalten.")
        copy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy_label.setStyleSheet("color: #4a5568; font-size: 11px;")
        layout.addWidget(copy_label)

        # ── Close Button ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Schließen")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #0f3460; border-color: #4cc9f0; "
            "color: #4cc9f0; font-weight: bold; padding: 8px 28px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #16213e; }"
        )
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    @staticmethod
    def _info_row(label_text: str, value_text: str) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel(f"{label_text}:")
        label.setStyleSheet("color: #8892b0; font-weight: 600; font-size: 12px;")
        label.setFixedWidth(100)
        value = QLabel(value_text)
        value.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        row.addWidget(label)
        row.addWidget(value)
        row.addStretch()
        return row
