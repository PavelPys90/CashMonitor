"""
CashMonitor – PIN Manager
Handles PIN setup, verification, and reset for edit/delete protection.
The PIN is stored as a SHA-256 hash in a config file.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


from utils import get_app_dir

CONFIG_FILE = get_app_dir() / "config.json"
RESET_CODE = "CASHMONITOR-RESET-2026"


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def is_pin_set() -> bool:
    """Check if a PIN has been configured."""
    config = _load_config()
    return "pin_hash" in config


def verify_pin(pin: str) -> bool:
    """Verify a PIN against the stored hash."""
    config = _load_config()
    stored = config.get("pin_hash", "")
    return _hash_pin(pin) == stored


def set_pin(pin: str):
    """Set or overwrite the PIN."""
    config = _load_config()
    config["pin_hash"] = _hash_pin(pin)
    _save_config(config)


def reset_pin():
    """Remove the stored PIN."""
    config = _load_config()
    config.pop("pin_hash", None)
    _save_config(config)


# ─── Dialogs ─────────────────────────────────────────────────


class PinSetupDialog(QDialog):
    """Dialog to set up a new PIN (first time or after reset)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔒 PIN einrichten")
        self.require_old = is_pin_set()
        
        height = 360 if self.require_old else 280
        self.setFixedSize(380, height)
        
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 24, 28, 20)

        title = QLabel("🔒 PIN einrichten")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4cc9f0;")
        layout.addWidget(title)

        info = QLabel("Wähle eine 4-6 stellige PIN zum Schutz von\nBearbeiten und Löschen.")
        info.setStyleSheet("color: #8892b0; font-size: 12px;")
        layout.addWidget(info)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        # Old PIN (if exists)
        if self.require_old:
            self.old_pin_edit = QLineEdit()
            self.old_pin_edit.setPlaceholderText("Alte PIN eingeben")
            self.old_pin_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.old_pin_edit.setMaxLength(6)
            self.old_pin_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.old_pin_edit.setStyleSheet("font-size: 14px; padding: 8px; border: 1px solid #f59e0b;")
            layout.addWidget(self.old_pin_edit)

        # PIN input
        self.pin_edit = QLineEdit()
        self.pin_edit.setPlaceholderText("PIN eingeben (4-6 Ziffern)")
        self.pin_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_edit.setMaxLength(6)
        self.pin_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_edit.setStyleSheet("font-size: 18px; letter-spacing: 8px; padding: 8px;")
        layout.addWidget(self.pin_edit)

        # Confirm input
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("PIN bestätigen")
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setMaxLength(6)
        self.confirm_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirm_edit.setStyleSheet("font-size: 18px; letter-spacing: 8px; padding: 8px;")
        layout.addWidget(self.confirm_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        skip_btn = QPushButton("Überspringen")
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)

        save_btn = QPushButton("💾 PIN setzen")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #064e3b; border-color: #10b981; "
            "color: #6ee7b7; font-weight: bold; padding: 8px 24px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #065f46; }"
        )
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        # Verify old PIN first
        if self.require_old:
            old_pin = self.old_pin_edit.text().strip()
            if not verify_pin(old_pin):
                self.error_label.setText("Alte PIN ist falsch!")
                return

        pin = self.pin_edit.text().strip()
        confirm = self.confirm_edit.text().strip()

        if not pin.isdigit() or len(pin) < 4:
            self.error_label.setText("PIN muss 4-6 Ziffern enthalten.")
            return

        if pin != confirm:
            self.error_label.setText("PINs stimmen nicht überein.")
            return

        set_pin(pin)
        self.accept()


class PinVerifyDialog(QDialog):
    """Dialog to verify the PIN before edit/delete."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔒 PIN eingeben")
        self.setFixedSize(360, 220)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 24, 28, 20)

        title = QLabel("🔒 PIN erforderlich")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #fbbf24;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        info = QLabel("Bitte PIN eingeben um fortzufahren.")
        info.setStyleSheet("color: #8892b0; font-size: 12px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        self.pin_edit = QLineEdit()
        self.pin_edit.setPlaceholderText("PIN")
        self.pin_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_edit.setMaxLength(6)
        self.pin_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_edit.setStyleSheet("font-size: 20px; letter-spacing: 10px; padding: 8px;")
        self.pin_edit.returnPressed.connect(self._on_check)
        layout.addWidget(self.pin_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("🔓 Bestätigen")
        ok_btn.setStyleSheet(
            "QPushButton { background-color: #0f3460; border-color: #4cc9f0; "
            "color: #4cc9f0; font-weight: bold; padding: 8px 24px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #16213e; }"
        )
        ok_btn.clicked.connect(self._on_check)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _on_check(self):
        pin = self.pin_edit.text().strip()
        if verify_pin(pin):
            self.accept()
        else:
            self.error_label.setText("Falsche PIN!")
            self.pin_edit.clear()
            self.pin_edit.setFocus()


class PinResetDialog(QDialog):
    """Dialog to reset the PIN using a master reset code."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 PIN zurücksetzen")
        self.setFixedSize(420, 260)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 24, 28, 20)

        title = QLabel("🔑 PIN zurücksetzen")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #f59e0b;")
        layout.addWidget(title)

        info = QLabel(
            f"Gib den Reset-Code ein um die PIN zu löschen.\n"
            f"Code: {RESET_CODE}"
        )
        info.setStyleSheet("color: #8892b0; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Reset-Code eingeben")
        self.code_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_edit.setStyleSheet("font-size: 14px; padding: 8px;")
        self.code_edit.returnPressed.connect(self._on_reset)
        layout.addWidget(self.code_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        reset_btn = QPushButton("🔑 Zurücksetzen")
        reset_btn.setStyleSheet(
            "QPushButton { background-color: #7f1d1d; border-color: #ef4444; "
            "color: #fca5a5; font-weight: bold; padding: 8px 24px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #991b1b; }"
        )
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)

        layout.addLayout(btn_layout)

    def _on_reset(self):
        code = self.code_edit.text().strip()
        if code == RESET_CODE:
            reset_pin()
            QMessageBox.information(
                self,
                "PIN zurückgesetzt",
                "Die PIN wurde gelöscht.\n"
                "Du kannst jetzt eine neue PIN einrichten\n"
                "über Hilfe → 🔒 PIN einrichten.",
            )
            self.accept()
        else:
            self.error_label.setText("Falscher Reset-Code!")
            self.code_edit.clear()
            self.code_edit.setFocus()


def require_pin(parent) -> bool:
    """
    Check PIN before edit/delete.
    Returns True if action is allowed (PIN verified or no PIN set).
    """
    if not is_pin_set():
        return True

    dlg = PinVerifyDialog(parent)
    return dlg.exec() == QDialog.DialogCode.Accepted
