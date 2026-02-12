"""
CashMonitor – Main Window
The primary application window with month navigation, transaction table,
summary cards, and a pie chart.
"""

import csv
import locale
from datetime import date
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QAbstractItemView,
    QMessageBox,
    QSizePolicy,
    QSpacerItem,
    QFileDialog,
)
from PySide6.QtCore import Qt, QSize, QMargins
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QAction
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice

from data_manager import DataManager, MonthSheet, Transaction, RecurringManager
from transaction_dialog import TransactionDialog
from about_dialog import AboutDialog
from charts_dialog import ChartsDialog
from pin_manager import require_pin, is_pin_set, PinSetupDialog, PinResetDialog
from recurring_dialog import RecurringDialog


MONTH_NAMES_DE = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

# Pie chart color palette
PIE_COLORS = [
    "#4cc9f0", "#f72585", "#7209b7", "#3a0ca3", "#4361ee",
    "#4895ef", "#06d6a0", "#ffd166", "#ef476f", "#118ab2",
    "#073b4c", "#e76f51", "#2a9d8f", "#e9c46a", "#264653",
]


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CashMonitor – Finanz-Tracker")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self.dm = DataManager()
        self.rm = RecurringManager(self.dm.data_dir)

        # Current month
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month

        # Filter: "all", "income", "expense"
        self.current_filter = "all"

        self._setup_ui()
        self._load_month()

    # ─── UI Setup ────────────────────────────────────────────────

    def _setup_ui(self):
        self._create_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(16)

        # ── Navigation Bar ──
        root.addLayout(self._create_nav_bar())

        # ── Content area: Summary (left) + Table (right) ──
        content = QHBoxLayout()
        content.setSpacing(16)

        # Left sidebar – summary + chart
        sidebar = QVBoxLayout()
        sidebar.setSpacing(12)
        sidebar.addLayout(self._create_summary_cards())
        sidebar.addWidget(self._create_chart_view())
        sidebar.addStretch()

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(340)

        content.addWidget(sidebar_widget)

        # Right – table
        right = QVBoxLayout()
        right.setSpacing(8)
        right.addLayout(self._create_filter_bar())
        right.addLayout(self._create_action_bar())
        right.addWidget(self._create_table())

        content.addLayout(right, 1)
        root.addLayout(content, 1)

    # ── Menu Bar ──

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # Datei menu
        file_menu = menu_bar.addMenu("Datei")

        export_month_action = QAction("📄 Aktuellen Monat exportieren (CSV)", self)
        export_month_action.setStatusTip("Aktuellen Monat als CSV exportieren")
        export_month_action.triggered.connect(self._export_current_month)
        file_menu.addAction(export_month_action)

        export_all_action = QAction("📚 Alle Monate exportieren (CSV)", self)
        export_all_action.setStatusTip("Alle verfügbaren Monate als eine CSV exportieren")
        export_all_action.triggered.connect(self._export_all_months)
        file_menu.addAction(export_all_action)

        file_menu.addSeparator()

        recurring_action = QAction("Wiederkehrende Eintraege", self)
        recurring_action.setStatusTip("Fixkosten und Fixeinnahmen verwalten")
        recurring_action.triggered.connect(self._show_recurring)
        file_menu.addAction(recurring_action)

        # Statistiken menu
        stats_menu = menu_bar.addMenu("Statistiken")

        charts_action = QAction("📊 Charts anzeigen", self)
        charts_action.setStatusTip("Multi-Monats-Statistiken und Diagramme")
        charts_action.triggered.connect(self._show_charts)
        stats_menu.addAction(charts_action)

        # Hilfe menu
        help_menu = menu_bar.addMenu("Hilfe")

        pin_setup_action = QAction("🔒 PIN einrichten", self)
        pin_setup_action.setStatusTip("PIN für Bearbeiten/Löschen setzen")
        pin_setup_action.triggered.connect(self._setup_pin)
        help_menu.addAction(pin_setup_action)

        pin_reset_action = QAction("🔑 PIN zurücksetzen", self)
        pin_reset_action.setStatusTip("PIN mit Reset-Code zurücksetzen")
        pin_reset_action.triggered.connect(self._reset_pin)
        help_menu.addAction(pin_reset_action)

        help_menu.addSeparator()

        about_action = QAction("ℹ️ Über CashMonitor", self)
        about_action.setStatusTip("Informationen über CashMonitor")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_charts(self):
        dlg = ChartsDialog(self, data_manager=self.dm)
        dlg.exec()

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _show_recurring(self):
        dlg = RecurringDialog(self, recurring_manager=self.rm)
        dlg.exec()
        self._load_month()  # refresh to show newly applied recurring items

    def _setup_pin(self):
        dlg = PinSetupDialog(self)
        dlg.exec()

    def _reset_pin(self):
        dlg = PinResetDialog(self)
        dlg.exec()

    # ── Export ──

    def _export_current_month(self):
        """Export current month's transactions to CSV."""
        if not self.sheet.transactions:
            QMessageBox.information(self, "Export", "Keine Transaktionen im aktuellen Monat.")
            return

        default_name = f"CashMonitor_{self.sheet.month_key}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV exportieren", str(Path.home() / default_name),
            "CSV Dateien (*.csv);;Alle Dateien (*)"
        )
        if not path:
            return

        self._write_csv(path, [self.sheet])
        QMessageBox.information(
            self, "Export erfolgreich",
            f"✅ {len(self.sheet.transactions)} Transaktionen exportiert nach:\n{path}"
        )

    def _export_all_months(self):
        """Export all months' transactions to a single CSV."""
        months = self.dm.get_available_months()
        if not months:
            QMessageBox.information(self, "Export", "Keine Daten vorhanden.")
            return

        default_name = "CashMonitor_Alle_Monate.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV exportieren", str(Path.home() / default_name),
            "CSV Dateien (*.csv);;Alle Dateien (*)"
        )
        if not path:
            return

        sheets = [self.dm.load_month(y, m) for y, m in months]
        total = sum(len(s.transactions) for s in sheets)
        self._write_csv(path, sheets)
        QMessageBox.information(
            self, "Export erfolgreich",
            f"✅ {total} Transaktionen aus {len(sheets)} Monaten exportiert nach:\n{path}"
        )

    @staticmethod
    def _write_csv(path: str, sheets: list):
        """Write transactions from one or more sheets to a CSV file."""
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Monat", "Datum", "Typ", "Kategorie", "Betrag", "Beschreibung"])
            for sheet in sheets:
                for tx in sheet.transactions:
                    writer.writerow([
                        sheet.month_key,
                        tx.date,
                        "Einnahme" if tx.type == "income" else "Ausgabe",
                        tx.category,
                        f"{tx.amount:.2f}".replace(".", ","),
                        tx.description,
                    ])

    # ── Nav Bar ──

    def _create_nav_bar(self) -> QHBoxLayout:
        nav = QHBoxLayout()

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setObjectName("navPrev")
        self.prev_btn.setToolTip("Vorheriger Monat")
        self.prev_btn.clicked.connect(self._prev_month)

        self.month_label = QLabel()
        self.month_label.setObjectName("monthLabel")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("▶")
        self.next_btn.setObjectName("navNext")
        self.next_btn.setToolTip("Nächster Monat")
        self.next_btn.clicked.connect(self._next_month)

        nav.addStretch()
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.month_label)
        nav.addWidget(self.next_btn)
        nav.addStretch()

        # App branding – right corner
        app_name_label = QLabel("💰 CashMonitor")
        app_name_label.setStyleSheet(
            "color: #4cc9f0; font-size: 14px; font-weight: 700; "
            "letter-spacing: 1px; padding-right: 4px;"
        )
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        nav.addWidget(app_name_label)

        return nav

    # ── Summary Cards ──

    def _create_summary_cards(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(10)

        # Income card
        self.income_card = self._make_card("incomeCard")
        self.income_title = QLabel("EINNAHMEN")
        self.income_title.setObjectName("summaryTitle")
        self.income_value = QLabel("0,00 €")
        self.income_value.setObjectName("incomeValue")
        ic_layout = QVBoxLayout(self.income_card)
        ic_layout.addWidget(self.income_title)
        ic_layout.addWidget(self.income_value)
        grid.addWidget(self.income_card, 0, 0)

        # Expense card
        self.expense_card = self._make_card("expenseCard")
        self.expense_title = QLabel("AUSGABEN")
        self.expense_title.setObjectName("summaryTitle")
        self.expense_value = QLabel("0,00 €")
        self.expense_value.setObjectName("expenseValue")
        ec_layout = QVBoxLayout(self.expense_card)
        ec_layout.addWidget(self.expense_title)
        ec_layout.addWidget(self.expense_value)
        grid.addWidget(self.expense_card, 0, 1)
        # Balance card (spans both columns)
        self.balance_card = self._make_card("balanceCard")
        self.balance_title = QLabel("BILANZ")
        self.balance_title.setObjectName("summaryTitle")
        self.balance_value = QLabel("0,00 €")
        self.balance_value.setObjectName("balanceValue")
        bc_layout = QVBoxLayout(self.balance_card)
        bc_layout.addWidget(self.balance_title)
        bc_layout.addWidget(self.balance_value)
        grid.addWidget(self.balance_card, 1, 0, 1, 2)

        # Prognose label (spans both columns, hidden by default)
        self.prognose_label = QLabel("")
        self.prognose_label.setObjectName("prognoseLabel")
        self.prognose_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prognose_label.setWordWrap(True)
        self.prognose_label.setStyleSheet(
            "color: #fbbf24; font-size: 12px; padding: 8px 12px; "
            "background-color: rgba(251, 191, 36, 0.08); "
            "border: 1px dashed #fbbf24; border-radius: 8px;"
        )
        self.prognose_label.setVisible(False)
        grid.addWidget(self.prognose_label, 2, 0, 1, 2)

        return grid

    def _make_card(self, object_name: str) -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        return card

    # ── Pie Chart ──

    def _create_chart_view(self) -> QChartView:
        self.chart = QChart()
        self.chart.setTitle("Ausgaben nach Kategorie")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.setBackgroundBrush(QColor("#16213e"))
        self.chart.setTitleBrush(QColor("#8892b0"))
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.chart.setTitleFont(title_font)
        self.chart.legend().setLabelColor(QColor("#8892b0"))
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        legend_font = QFont()
        legend_font.setPointSize(9)
        self.chart.legend().setFont(legend_font)
        self.chart.setMargins(QMargins(4, 4, 4, 4))

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(260)
        self.chart_view.setStyleSheet(
            "background: #16213e; border: 1px solid #0f3460; border-radius: 12px;"
        )

        return self.chart_view

    # ── Filter Bar ──

    def _create_filter_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        self.filter_all = QPushButton("Alle")
        self.filter_all.setObjectName("filterAll")
        self.filter_all.setCheckable(True)
        self.filter_all.setChecked(True)
        self.filter_all.clicked.connect(lambda: self._set_filter("all"))

        self.filter_income = QPushButton("Einnahmen")
        self.filter_income.setObjectName("filterIncome")
        self.filter_income.setCheckable(True)
        self.filter_income.clicked.connect(lambda: self._set_filter("income"))

        self.filter_expense = QPushButton("Ausgaben")
        self.filter_expense.setObjectName("filterExpense")
        self.filter_expense.setCheckable(True)
        self.filter_expense.clicked.connect(lambda: self._set_filter("expense"))

        bar.addWidget(self.filter_all)
        bar.addWidget(self.filter_income)
        bar.addWidget(self.filter_expense)
        bar.addStretch()

        return bar

    # ── Action Bar ──

    def _create_action_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        self.add_income_btn = QPushButton("＋ Einnahme")
        self.add_income_btn.setObjectName("addIncomeBtn")
        self.add_income_btn.setToolTip("Neue Einnahme hinzufügen")
        self.add_income_btn.clicked.connect(lambda: self._add_transaction("income"))

        self.add_expense_btn = QPushButton("＋ Ausgabe")
        self.add_expense_btn.setObjectName("addExpenseBtn")
        self.add_expense_btn.setToolTip("Neue Ausgabe hinzufügen")
        self.add_expense_btn.clicked.connect(lambda: self._add_transaction("expense"))

        self.edit_btn = QPushButton("✏️ Bearbeiten")
        self.edit_btn.setToolTip("Ausgewählte Transaktion bearbeiten")
        self.edit_btn.clicked.connect(self._edit_transaction)

        self.delete_btn = QPushButton("🗑 Löschen")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setToolTip("Ausgewählte Transaktion löschen")
        self.delete_btn.clicked.connect(self._delete_transaction)

        bar.addWidget(self.add_income_btn)
        bar.addWidget(self.add_expense_btn)
        bar.addStretch()
        bar.addWidget(self.edit_btn)
        bar.addWidget(self.delete_btn)

        return bar

    # ── Table ──

    def _create_table(self) -> QTableWidget:
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Datum", "Typ", "Kategorie", "Betrag", "Beschreibung"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.table.doubleClicked.connect(self._edit_transaction)

        return self.table

    # ─── Data Loading ────────────────────────────────────────────

    def _is_future_month(self) -> bool:
        """Check if the currently displayed month is in the future."""
        today = date.today()
        return (self.current_year, self.current_month) > (today.year, today.month)

    def _load_month(self):
        """Load the current month's data, apply recurring items (only for current/past), and refresh UI."""
        self.sheet = self.dm.load_month(self.current_year, self.current_month)
        if not self._is_future_month():
            self.rm.apply_recurring(self.sheet, self.dm)
        self._update_month_label()
        self._update_summary()
        self._update_chart()
        self._update_table()

    def _update_month_label(self):
        name = MONTH_NAMES_DE[self.current_month]
        if self._is_future_month():
            self.month_label.setText(f"{name} {self.current_year}  (Zukunft)")
        else:
            self.month_label.setText(f"{name} {self.current_year}")

    def _update_summary(self):
        income = self.sheet.total_income
        expense = self.sheet.total_expense
        balance = self.sheet.balance

        self.income_value.setText(self._fmt_money(income))
        self.expense_value.setText(self._fmt_money(expense))
        self.balance_value.setText(self._fmt_money(balance))

        # Color-code balance
        if balance >= 0:
            self.balance_value.setObjectName("balancePositive")
        else:
            self.balance_value.setObjectName("balanceNegative")
        # Force style refresh
        self.balance_value.style().unpolish(self.balance_value)
        self.balance_value.style().polish(self.balance_value)

        # Prognose for future months
        if self._is_future_month():
            prog_income, prog_expense = self._get_prognose()
            prog_balance = prog_income - prog_expense
            sign = "+" if prog_balance >= 0 else ""
            self.prognose_label.setText(
                f"Prognose (Fixeintraege):  "
                f"Einnahmen {self._fmt_money(prog_income)}  |  "
                f"Ausgaben {self._fmt_money(prog_expense)}  |  "
                f"Bilanz {sign}{self._fmt_money(prog_balance)}"
            )
            self.prognose_label.setVisible(True)
        else:
            self.prognose_label.setVisible(False)

    def _get_prognose(self) -> tuple[float, float]:
        """Calculate projected income and expenses from active recurring items."""
        prog_income = sum(r.amount for r in self.rm.items if r.active and r.type == "income")
        prog_expense = sum(r.amount for r in self.rm.items if r.active and r.type == "expense")
        return round(prog_income, 2), round(prog_expense, 2)

    def _update_chart(self):
        self.chart.removeAllSeries()

        cats = self.sheet.expense_by_category()
        if not cats:
            self.chart.setTitle("Keine Ausgaben")
            return

        self.chart.setTitle("Ausgaben nach Kategorie")
        series = QPieSeries()
        series.setHoleSize(0.35)

        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        for i, (cat, amount) in enumerate(sorted_cats):
            sl = series.append(f"{cat}: {self._fmt_money(amount)}", amount)
            sl.setBrush(QColor(PIE_COLORS[i % len(PIE_COLORS)]))
            sl.setBorderColor(QColor("#1a1a2e"))
            sl.setBorderWidth(2)

        # Explode the largest slice
        if series.count() > 0:
            biggest = series.slices()[0]
            biggest.setExploded(True)
            biggest.setExplodeDistanceFactor(0.06)
            biggest.setLabelVisible(True)
            biggest.setLabelColor(QColor("#e0e0e0"))
            label_font = QFont()
            label_font.setPointSize(10)
            label_font.setBold(True)
            biggest.setLabelFont(label_font)

        self.chart.addSeries(series)

    def _update_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        # Apply filter
        if self.current_filter == "income":
            txns = self.sheet.incomes
        elif self.current_filter == "expense":
            txns = self.sheet.expenses
        else:
            txns = self.sheet.transactions

        self.table.setRowCount(len(txns))

        for row, tx in enumerate(txns):
            # Date
            date_item = QTableWidgetItem(self._fmt_date(tx.date))
            date_item.setData(Qt.ItemDataRole.UserRole, tx.id)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, date_item)

            # Type
            type_text = "Einnahme" if tx.type == "income" else "Ausgabe"
            if tx.recurring_id:
                type_text = "\u21bb " + type_text
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_color = QColor("#10b981") if tx.type == "income" else QColor("#ef4444")
            type_item.setForeground(type_color)
            font = QFont()
            font.setBold(True)
            type_item.setFont(font)
            self.table.setItem(row, 1, type_item)

            # Category
            cat_item = QTableWidgetItem(tx.category)
            self.table.setItem(row, 2, cat_item)

            # Amount
            prefix = "+" if tx.type == "income" else "−"
            amount_item = QTableWidgetItem(f"{prefix} {self._fmt_money(tx.amount)}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            amount_color = QColor("#10b981") if tx.type == "income" else QColor("#ef4444")
            amount_item.setForeground(amount_color)
            bold_font = QFont()
            bold_font.setBold(True)
            amount_item.setFont(bold_font)
            self.table.setItem(row, 3, amount_item)

            # Description
            desc_item = QTableWidgetItem(tx.description)
            desc_item.setForeground(QColor("#8892b0"))
            self.table.setItem(row, 4, desc_item)

        self.table.setSortingEnabled(True)

    # ─── Actions ─────────────────────────────────────────────────

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._load_month()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._load_month()

    def _set_filter(self, f: str):
        self.current_filter = f
        # Update button states
        self.filter_all.setChecked(f == "all")
        self.filter_income.setChecked(f == "income")
        self.filter_expense.setChecked(f == "expense")
        self._update_table()

    def _add_transaction(self, tx_type: str):
        dlg = TransactionDialog(self, tx_type=tx_type)
        if dlg.exec() == TransactionDialog.DialogCode.Accepted:
            tx = dlg.get_transaction()
            self.dm.add_transaction(self.sheet, tx)
            self._refresh_after_change()

    def _edit_transaction(self):
        tx_id = self._selected_tx_id()
        if tx_id is None:
            return

        if not require_pin(self):
            return

        # Find the transaction
        tx = None
        for t in self.sheet.transactions:
            if t.id == tx_id:
                tx = t
                break
        if tx is None:
            return

        dlg = TransactionDialog(self, transaction=tx)
        if dlg.exec() == TransactionDialog.DialogCode.Accepted:
            updated = dlg.get_transaction()
            self.dm.update_transaction(self.sheet, tx_id, updated)
            self._refresh_after_change()

    def _delete_transaction(self):
        tx_id = self._selected_tx_id()
        if tx_id is None:
            return

        if not require_pin(self):
            return

        reply = QMessageBox.question(
            self,
            "Transaktion löschen",
            "Möchtest du diese Transaktion wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.dm.delete_transaction(self.sheet, tx_id)
            self._refresh_after_change()

    # ─── Helpers ─────────────────────────────────────────────────

    def _selected_tx_id(self) -> str | None:
        """Get the transaction ID from the selected table row."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _refresh_after_change(self):
        """Reload data and refresh all UI elements."""
        self.sheet = self.dm.load_month(self.current_year, self.current_month)
        self._update_summary()
        self._update_chart()
        self._update_table()

    @staticmethod
    def _fmt_money(value: float) -> str:
        """Format a monetary value: 1234.56 → '1.234,56 €'."""
        # Manual German format
        sign = "-" if value < 0 else ""
        value = abs(value)
        integer_part = int(value)
        decimal_part = round((value - integer_part) * 100)
        # Thousands separator
        int_str = f"{integer_part:,}".replace(",", ".")
        return f"{sign}{int_str},{decimal_part:02d} €"

    @staticmethod
    def _fmt_date(iso_date: str) -> str:
        """Format ISO date to German: 2026-02-05 → 05.02.2026."""
        parts = iso_date.split("-")
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
        return iso_date
