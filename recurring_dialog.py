"""
CashMonitor – Recurring Transactions Dialog
Manage recurring (fixed) monthly income and expense entries.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QFrame,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QFormLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from data_manager import (
    RecurringManager,
    RecurringItem,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
)


class RecurringItemDialog(QDialog):
    """Dialog to add or edit a single recurring item."""

    def __init__(self, parent=None, item: RecurringItem = None):
        super().__init__(parent)
        self.setWindowTitle("Bearbeiten" if item else "Neuer Dauerauftrag")
        self.setFixedSize(400, 320)
        self.setModal(True)
        self._item = item
        self._setup_ui()
        if item:
            self._populate(item)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 16)

        title_text = "Dauerauftrag bearbeiten" if self._item else "Neuer Dauerauftrag"
        title = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4cc9f0;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(10)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Einnahme", "Ausgabe"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Typ:", self.type_combo)

        # Day
        self.day_spin = QSpinBox()
        self.day_spin.setMinimum(1)
        self.day_spin.setMaximum(28)
        self.day_spin.setValue(1)
        self.day_spin.setToolTip("Tag im Monat (1-28)")
        form.addRow("Tag:", self.day_spin)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self._update_categories()
        form.addRow("Kategorie:", self.category_combo)

        # Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("z.B. 850.00")
        form.addRow("Betrag (EUR):", self.amount_edit)

        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("z.B. Kaltmiete")
        form.addRow("Beschreibung:", self.desc_edit)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Speichern")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #064e3b; border-color: #10b981; "
            "color: #6ee7b7; font-weight: bold; padding: 8px 24px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #065f46; }"
        )
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_type_changed(self):
        self._update_categories()

    def _update_categories(self):
        current = self.category_combo.currentText()
        self.category_combo.clear()
        if self.type_combo.currentIndex() == 0:
            self.category_combo.addItems(INCOME_CATEGORIES)
        else:
            self.category_combo.addItems(EXPENSE_CATEGORIES)
        idx = self.category_combo.findText(current)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

    def _populate(self, item: RecurringItem):
        self.type_combo.setCurrentIndex(0 if item.type == "income" else 1)
        self.day_spin.setValue(item.day)
        self._update_categories()
        idx = self.category_combo.findText(item.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setEditText(item.category)
        self.amount_edit.setText(f"{item.amount:.2f}")
        self.desc_edit.setText(item.description)

    def _on_save(self):
        try:
            amount = float(self.amount_edit.text().replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Bitte einen gueltigen Betrag eingeben.")
            return

        self.accept()

    def get_item(self) -> RecurringItem:
        tx_type = "income" if self.type_combo.currentIndex() == 0 else "expense"
        return RecurringItem(
            day=self.day_spin.value(),
            tx_type=tx_type,
            category=self.category_combo.currentText().strip(),
            amount=float(self.amount_edit.text().replace(",", ".")),
            description=self.desc_edit.text().strip(),
        )


class RecurringDialog(QDialog):
    """Dialog to manage all recurring transaction templates."""

    def __init__(self, parent=None, recurring_manager: RecurringManager = None):
        super().__init__(parent)
        self.rm = recurring_manager
        self.setWindowTitle("Wiederkehrende Eintraege")
        self.setMinimumSize(700, 450)
        self.setModal(True)
        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Wiederkehrende Eintraege")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4cc9f0;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        info = QLabel("Fixkosten und Fixeinnahmen, die jeden Monat automatisch eingetragen werden.")
        info.setStyleSheet("color: #8892b0; font-size: 11px;")
        header_layout.addWidget(info)
        layout.addLayout(header_layout)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Status", "Tag", "Typ", "Kategorie", "Betrag", "Beschreibung"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 70)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("+ Hinzufuegen")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #064e3b; border-color: #10b981; "
            "color: #6ee7b7; font-weight: bold; padding: 8px 16px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #065f46; }"
        )
        add_btn.clicked.connect(self._add_item)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Bearbeiten")
        edit_btn.clicked.connect(self._edit_item)
        btn_layout.addWidget(edit_btn)

        toggle_btn = QPushButton("Aktivieren / Deaktivieren")
        toggle_btn.clicked.connect(self._toggle_item)
        btn_layout.addWidget(toggle_btn)

        btn_layout.addStretch()

        delete_btn = QPushButton("Loeschen")
        delete_btn.setStyleSheet(
            "QPushButton { background-color: #7f1d1d; border-color: #ef4444; "
            "color: #fca5a5; padding: 8px 16px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #991b1b; }"
        )
        delete_btn.clicked.connect(self._delete_item)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

    def _load_table(self):
        self.table.setRowCount(0)
        for item in self.rm.items:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Status
            status = QTableWidgetItem("Aktiv" if item.active else "Pausiert")
            status.setForeground(QColor("#10b981") if item.active else QColor("#6b7280"))
            status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status.setData(Qt.ItemDataRole.UserRole, item.id)
            self.table.setItem(row, 0, status)

            # Day
            day_item = QTableWidgetItem(f"{item.day:02d}.")
            day_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, day_item)

            # Type
            type_text = "Einnahme" if item.type == "income" else "Ausgabe"
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(
                QColor("#10b981") if item.type == "income" else QColor("#ef4444")
            )
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, type_item)

            # Category
            self.table.setItem(row, 3, QTableWidgetItem(item.category))

            # Amount
            amount_item = QTableWidgetItem(f"{item.amount:,.2f} EUR".replace(",", "."))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, amount_item)

            # Description
            self.table.setItem(row, 5, QTableWidgetItem(item.description))

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Hinweis", "Bitte einen Eintrag auswaehlen.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _add_item(self):
        dlg = RecurringItemDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = dlg.get_item()
            self.rm.add(item)
            self._load_table()

    def _edit_item(self):
        item_id = self._selected_id()
        if item_id is None:
            return

        item = None
        for it in self.rm.items:
            if it.id == item_id:
                item = it
                break
        if item is None:
            return

        dlg = RecurringItemDialog(self, item=item)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_item()
            self.rm.update(item_id, updated)
            self._load_table()

    def _toggle_item(self):
        item_id = self._selected_id()
        if item_id is None:
            return
        self.rm.toggle_active(item_id)
        self._load_table()

    def _delete_item(self):
        item_id = self._selected_id()
        if item_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Dauerauftrag loeschen",
            "Diesen wiederkehrenden Eintrag wirklich loeschen?\n"
            "(Bereits eingetragene Transaktionen bleiben erhalten.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.rm.delete(item_id)
            self._load_table()
