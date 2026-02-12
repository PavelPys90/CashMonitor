
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from license_manager import LicenseManager

class LicenseDialog(QDialog):
    def __init__(self, license_manager: LicenseManager, parent=None):
        super().__init__(parent)
        self.lm = license_manager
        self.setWindowTitle("Lizenzprüfung")
        self.setFixedSize(400, 250)
        self.setModal(True)
        # Remove close button to force valid choice or exit
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🔒 Lizenz erforderlich")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ef4444;") # Red color
        layout.addWidget(title)

        info = QLabel(
            "Bitte wähle eine gültige Lizenzdatei (license.dat) aus, "
            "um CashMonitor zu starten."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(info)

        btn_load = QPushButton("📂 Lizenzdatei laden...")
        btn_load.setStyleSheet(
            "QPushButton { background-color: #0f3460; color: #4cc9f0; padding: 10px; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover { background-color: #16213e; }"
        )
        btn_load.clicked.connect(self._select_file)
        layout.addWidget(btn_load)

        btn_exit = QPushButton("Beenden")
        btn_exit.clicked.connect(self.reject)
        btn_exit.setStyleSheet("color: #8892b0; border: none;")
        layout.addWidget(btn_exit)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Lizenzdatei auswählen", "", "License Files (*.dat *.json);;All Files (*)"
        )
        if path:
            from pathlib import Path
            if self.lm.install_license(Path(path)):
                QMessageBox.information(self, "Erfolg", "Lizenz erfolgreich installiert!")
                self.accept()
            else:
                msg = f"Fehler bei der Lizenzprüfung:\n{self.lm.last_error}"
                QMessageBox.critical(self, "Fehler", msg)
