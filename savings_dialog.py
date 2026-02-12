"""
CashMonitor – Savings Goals Dialog
Manage savings goals and track progress.
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
    QFormLayout,
    QMessageBox,
    QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from data_manager import (
    SavingsManager,
    SavingsGoal,
    DataManager,
    EXPENSE_CATEGORIES,
)
from transaction_dialog import TransactionDialog

class SavingsGoalDialog(QDialog):
    """Dialog to add or edit a single savings goal."""

    def __init__(self, parent=None, goal: SavingsGoal = None):
        super().__init__(parent)
        self.setWindowTitle("Ziel bearbeiten" if goal else "Neues Sparziel")
        self.setFixedSize(400, 300)
        self.setModal(True)
        self._goal = goal
        self._setup_ui()
        if goal:
            self._populate(goal)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 16)

        title_text = "Sparziel bearbeiten" if self._goal else "Neues Sparziel"
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

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. Urlaub 2026")
        form.addRow("Name:", self.name_edit)

        # Target Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("z.B. 3000.00")
        form.addRow("Zielbetrag (EUR):", self.amount_edit)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        # Pre-fill with existing expense categories, but intended for "Sparen: ..."
        self.category_combo.addItems([c for c in EXPENSE_CATEGORIES if c.startswith("Sparen")])
        self.category_combo.addItems(EXPENSE_CATEGORIES)
        form.addRow("Kategorie:", self.category_combo)

        # Icon (Simple text for now)
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("z.B. ✈️")
        self.icon_edit.setText("💰")
        form.addRow("Icon:", self.icon_edit)

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

    def _populate(self, goal: SavingsGoal):
        self.name_edit.setText(goal.name)
        self.amount_edit.setText(f"{goal.target_amount:.2f}")
        idx = self.category_combo.findText(goal.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setEditText(goal.category)
        self.icon_edit.setText(goal.icon)

    def _on_save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Fehler", "Bitte einen Namen eingeben.")
            return
        try:
            amount = float(self.amount_edit.text().replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Bitte einen gueltigen Zielbetrag eingeben.")
            return

        self.accept()

    def get_goal(self) -> SavingsGoal:
        return SavingsGoal(
            name=self.name_edit.text().strip(),
            target_amount=float(self.amount_edit.text().replace(",", ".")),
            category=self.category_combo.currentText().strip(),
            icon=self.icon_edit.text().strip() or "💰",
            color="#10b981" # Default green for now
        )


class SavingsDialog(QDialog):
    """Dialog to manage savings goals."""

    def __init__(self, parent=None, savings_manager: SavingsManager = None, data_manager: DataManager = None, year: int = None, month: int = None, on_change=None):
        super().__init__(parent)
        self.sm = savings_manager
        self.dm = data_manager
        self.current_year = year
        self.current_month = month
        self.on_change = on_change
        
        self.setWindowTitle("Sparziele verwalten")
        self.setMinimumSize(800, 500)
        self.setModal(True)
        self._setup_ui()
        self._load_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Sparziele (Savings Goals)")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4cc9f0;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        info = QLabel(
            "Definiere Ziele und verknuepfe sie mit einer Kategorie. "
            "Alle Ausgaben in dieser Kategorie (ueber alle Monate) zaehlen als Fortschritt."
        )
        info.setStyleSheet("color: #8892b0; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Icon", "Name", "Kategorie", "Fortschritt / Ziel", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("+ Neues Ziel")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #064e3b; border-color: #10b981; "
            "color: #6ee7b7; font-weight: bold; padding: 8px 16px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #065f46; }"
        )
        add_btn.clicked.connect(self._add_goal)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Bearbeiten")
        edit_btn.clicked.connect(self._edit_goal)
        btn_layout.addWidget(edit_btn)

        deposit_btn = QPushButton("💰 Einzahlen...")
        deposit_btn.setToolTip("Erstellt eine Ausgabe in der Ziel-Kategorie im aktuellen Monat")
        deposit_btn.clicked.connect(self._deposit)
        deposit_btn.setStyleSheet(
            "QPushButton { background-color: #1e3a8a; border-color: #3b82f6; "
            "color: #93c5fd; font-weight: bold; padding: 8px 16px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #1e40af; }"
        )
        btn_layout.addWidget(deposit_btn)

        btn_layout.addStretch()

        delete_btn = QPushButton("Loeschen")
        delete_btn.setStyleSheet(
            "QPushButton { background-color: #7f1d1d; border-color: #ef4444; "
            "color: #fca5a5; padding: 8px 16px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #991b1b; }"
        )
        delete_btn.clicked.connect(self._delete_goal)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

    def _load_table(self):
        self.table.setRowCount(0)
        for goal in self.sm.goals:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Icon
            icon_item = QTableWidgetItem(goal.icon)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_item.setData(Qt.ItemDataRole.UserRole, goal.id)
            self.table.setItem(row, 0, icon_item)

            # Name
            self.table.setItem(row, 1, QTableWidgetItem(goal.name))

            # Category
            self.table.setItem(row, 2, QTableWidgetItem(goal.category))

            # Progress
            # Calculate current amount
            current = self.dm.get_total_expenses_for_category(goal.category)
            percent = 0
            if goal.target_amount > 0:
                percent = int((current / goal.target_amount) * 100)
            
            # Use a custom widget for progress bar + text
            prog_widget = QFrame()
            prog_layout = QVBoxLayout(prog_widget)
            prog_layout.setContentsMargins(4, 4, 4, 4)
            prog_layout.setSpacing(2)
            
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(min(100, percent))
            pbar.setTextVisible(False)
            pbar.setFixedHeight(8)
            # Style the chunk
            pbar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {goal.color}; border-radius: 2px; }}")
            
            label = QLabel(f"{current:,.2f} / {goal.target_amount:,.2f} EUR ({percent}%)".replace(",", "X").replace(".", ",").replace("X", "."))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 10px; color: #cbd5e1;")
            
            prog_layout.addWidget(pbar)
            prog_layout.addWidget(label)
            
            self.table.setCellWidget(row, 3, prog_widget)

            # Status (Completed?)
            status_text = "Erreicht! 🎉" if current >= goal.target_amount else "Laeuft"
            status_item = QTableWidgetItem(status_text)
            if current >= goal.target_amount:
                status_item.setForeground(QColor("#fbbf24")) # Gold
            else:
                status_item.setForeground(QColor("#94a3b8"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, status_item)
            
        self.table.setRowHeight(row, 50) 

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Hinweis", "Bitte ein Ziel auswaehlen.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _add_goal(self):
        dlg = SavingsGoalDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.sm.add(dlg.get_goal())
            self._load_table()

    def _edit_goal(self):
        goal_id = self._selected_id()
        if not goal_id: return
        
        goal = next((g for g in self.sm.goals if g.id == goal_id), None)
        if not goal: return

        dlg = SavingsGoalDialog(self, goal)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_goal()
            self.sm.update(goal_id, updated)
            self._load_table()

    def _delete_goal(self):
        goal_id = self._selected_id()
        if not goal_id: return
        
        reply = QMessageBox.question(
            self, "Loeschen", "Sparziel wirklich loeschen?\n(Die Kategorien/Ausgaben bleiben erhalten.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.sm.delete(goal_id)
            self._load_table()

    def _deposit(self):
        goal_id = self._selected_id()
        if not goal_id: return
        
        goal = next((g for g in self.sm.goals if g.id == goal_id), None)
        if not goal: return
        
        # Open Transaction Dialog presetting the category
        dlg = TransactionDialog(self, tx_type="expense")
        # Pre-fill category
        idx = dlg.category_combo.findText(goal.category)
        if idx >= 0:
            dlg.category_combo.setCurrentIndex(idx)
        else:
            dlg.category_combo.setEditText(goal.category)
            
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_tx = dlg.get_transaction()
            # If date was changed in dialog, we should respect it?
            # But we want to add it to the CURRENT viewed month in MainWindow?
            # User might change date to another month.
            # DataManager.add_transaction handles saving to the correct file based on date?
            # Let's check DataManager.add_transaction.
            # It takes 'sheet' as argument.
            
            # If we want to support any date, we should determine the correct sheet.
            # But here we probably want to deposit "now" or for the "current month".
            
            # Let's check new_tx.date
            y, m, d = map(int, new_tx.date.split("-"))
            
            # Load the sheet for that date
            sheet = self.dm.load_month(y, m)
            self.dm.add_transaction(sheet, new_tx)
            
            # Reload table to show progress
            self._load_table()
            
            # Notify parent if the changed month is the one currently viewed
            if self.on_change and y == self.current_year and m == self.current_month:
                self.on_change()
            elif self.on_change and (y, m) != (self.current_year, self.current_month):
                # We might want to refresh anyway just in case rollover affects things?
                # Rollover propagates forward.
                # If we add expense to past, current month rollover changes.
                self.on_change()
