"""
CashMonitor – Transaction Dialog
Dialog for adding or editing a transaction.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit,
    QPushButton,
    QDialogButtonBox,
    QFrame,
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont

from data_manager import (
    Transaction,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
)


class TransactionDialog(QDialog):
    """Dialog for adding or editing a transaction."""

    def __init__(self, parent=None, tx_type: str = "expense", transaction: Transaction = None):
        super().__init__(parent)
        self.tx_type = tx_type
        self.transaction = transaction
        self._editing = transaction is not None

        if self._editing:
            self.tx_type = transaction.type

        self.setWindowTitle(
            "Transaktion bearbeiten" if self._editing
            else ("Einnahme hinzufügen" if self.tx_type == "income" else "Ausgabe hinzufügen")
        )
        self.setMinimumWidth(420)
        self.setModal(True)

        self._setup_ui()

        if self._editing:
            self._populate(transaction)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QLabel(
            "💰 Einnahme" if self.tx_type == "income" else "💸 Ausgabe"
        )
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet(
            f"color: {'#10b981' if self.tx_type == 'income' else '#ef4444'}; "
            f"padding-bottom: 8px;"
        )
        layout.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Datum:", self.date_edit)

        # Category
        self.category_combo = QComboBox()
        categories = INCOME_CATEGORIES if self.tx_type == "income" else EXPENSE_CATEGORIES
        self.category_combo.addItems(categories)
        self.category_combo.setEditable(True)
        self.category_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        form.addRow("Kategorie:", self.category_combo)

        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" €")
        self.amount_spin.setValue(0.00)
        self.amount_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Betrag:", self.amount_spin)

        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("z.B. Wocheneinkauf Rewe")
        self.desc_edit.setMaxLength(200)
        form.addRow("Beschreibung:", self.desc_edit)

        layout.addLayout(form)

        # Spacer
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Speichern")
        save_btn.setDefault(True)
        save_btn.setStyleSheet(
            "QPushButton { "
            f"  background-color: {'#064e3b' if self.tx_type == 'income' else '#7f1d1d'}; "
            f"  border-color: {'#10b981' if self.tx_type == 'income' else '#ef4444'}; "
            f"  color: {'#6ee7b7' if self.tx_type == 'income' else '#fca5a5'}; "
            "  font-weight: bold; padding: 8px 24px; border-radius: 8px; "
            "} "
            "QPushButton:hover { "
            f"  background-color: {'#065f46' if self.tx_type == 'income' else '#991b1b'}; "
            "}"
        )
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate(self, tx: Transaction):
        """Fill in fields from existing transaction."""
        # Date
        parts = tx.date.split("-")
        self.date_edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))

        # Category
        idx = self.category_combo.findText(tx.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setEditText(tx.category)

        # Amount
        self.amount_spin.setValue(tx.amount)

        # Description
        self.desc_edit.setText(tx.description)

    def _on_save(self):
        """Validate and accept."""
        if self.amount_spin.value() <= 0:
            return

        self.accept()

    def get_transaction(self) -> Transaction:
        """Build a Transaction from current field values."""
        d = self.date_edit.date()
        return Transaction(
            tx_date=f"{d.year():04d}-{d.month():02d}-{d.day():02d}",
            tx_type=self.tx_type,
            category=self.category_combo.currentText().strip(),
            amount=self.amount_spin.value(),
            description=self.desc_edit.text().strip(),
            tx_id=self.transaction.id if self._editing else None,
        )
