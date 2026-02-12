"""
CashMonitor – Charts / Statistics Dialog
Multi-month visualizations: bar charts, trends, and category breakdowns.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
    QLineSeries,
    QPieSeries,
    QStackedBarSeries,
)

from data_manager import DataManager

MONTH_NAMES_SHORT = [
    "", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
]

CHART_COLORS = {
    "income": "#10b981",
    "expense": "#ef4444",
    "balance": "#4cc9f0",
    "savings": "#a78bfa",
}

CATEGORY_COLORS = [
    "#4cc9f0", "#f72585", "#7209b7", "#3a0ca3", "#4361ee",
    "#4895ef", "#06d6a0", "#ffd166", "#ef476f", "#118ab2",
    "#073b4c", "#e76f51", "#2a9d8f", "#e9c46a", "#264653",
]


class ChartsDialog(QDialog):
    """Statistics dialog with multiple chart views."""

    def __init__(self, parent=None, data_manager: DataManager = None):
        super().__init__(parent)
        self.dm = data_manager or DataManager()
        self.setWindowTitle("📊 Statistiken – CashMonitor")
        self.setMinimumSize(900, 620)
        self.resize(1000, 700)
        self.setModal(True)

        self._available_months = self.dm.get_available_months()
        self._setup_ui()

        # Show first chart by default
        if self._available_months:
            self._on_chart_selected(0)
        else:
            self._show_no_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # ── Header ──
        header_layout = QHBoxLayout()

        title = QLabel("📊 Statistiken")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4cc9f0;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Chart selector
        selector_label = QLabel("Diagramm:")
        selector_label.setStyleSheet("color: #8892b0; font-weight: 600;")
        header_layout.addWidget(selector_label)

        self.chart_selector = QComboBox()
        self.chart_selector.addItems([
            "Einnahmen vs. Ausgaben",
            "Bilanz-Verlauf",
            "Sparquote",
            "Ausgaben nach Kategorie (Gesamt)",
            "Top 5 Ausgaben-Kategorien",
        ])
        self.chart_selector.setMinimumWidth(250)
        self.chart_selector.currentIndexChanged.connect(self._on_chart_selected)
        header_layout.addWidget(self.chart_selector)

        layout.addLayout(header_layout)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #0f3460;")
        layout.addWidget(sep)

        # ── Chart View ──
        self.chart = QChart()
        self._style_chart(self.chart)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setStyleSheet(
            "background: #16213e; border: 1px solid #0f3460; border-radius: 12px;"
        )
        self.chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.chart_view, 1)

        # ── Info label ──
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #8892b0; font-size: 12px; padding: 4px;")
        layout.addWidget(self.info_label)

        # ── Close button ──
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

    def _style_chart(self, chart: QChart):
        """Apply consistent dark styling to a chart."""
        chart.setBackgroundBrush(QColor("#16213e"))
        chart.setTitleBrush(QColor("#ccd6f6"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.legend().setLabelColor(QColor("#8892b0"))
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        legend_font = QFont()
        legend_font.setPointSize(10)
        chart.legend().setFont(legend_font)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

    def _style_axis(self, axis, color="#8892b0"):
        """Style an axis for the dark theme."""
        axis.setLabelsColor(QColor(color))
        axis.setGridLineColor(QColor("#233554"))
        axis.setLinePenColor(QColor("#0f3460"))
        label_font = QFont()
        label_font.setPointSize(9)
        axis.setLabelsFont(label_font)

    def _load_all_data(self):
        """Load all available months and return sorted list of (label, sheet)."""
        results = []
        for year, month in self._available_months:
            sheet = self.dm.load_month(year, month)
            label = f"{MONTH_NAMES_SHORT[month]} {year}"
            results.append((label, sheet))
        return results

    # ─── Chart Builders ──────────────────────────────────────────

    def _on_chart_selected(self, index: int):
        if not self._available_months:
            self._show_no_data()
            return

        builders = [
            self._build_income_vs_expense,
            self._build_balance_trend,
            self._build_savings_rate,
            self._build_total_categories,
            self._build_top5_categories,
        ]

        if 0 <= index < len(builders):
            builders[index]()

    def _show_no_data(self):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        self.chart.setTitle("Keine Daten vorhanden")
        self.info_label.setText(
            "Füge zuerst Transaktionen hinzu, um Statistiken zu sehen."
        )

    # 1. Income vs Expense Bar Chart
    def _build_income_vs_expense(self):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        data = self._load_all_data()
        self.chart.setTitle("Einnahmen vs. Ausgaben pro Monat")

        income_set = QBarSet("Einnahmen")
        income_set.setColor(QColor(CHART_COLORS["income"]))
        income_set.setBorderColor(QColor("#16213e"))

        expense_set = QBarSet("Ausgaben")
        expense_set.setColor(QColor(CHART_COLORS["expense"]))
        expense_set.setBorderColor(QColor("#16213e"))

        categories = []
        max_val = 0.0
        for label, sheet in data:
            categories.append(label)
            income_set.append(sheet.total_income)
            expense_set.append(sheet.total_expense)
            max_val = max(max_val, sheet.total_income, sheet.total_expense)

        series = QBarSeries()
        series.append(income_set)
        series.append(expense_set)
        self.chart.addSeries(series)

        # X axis
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self._style_axis(axis_x)
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y axis
        axis_y = QValueAxis()
        axis_y.setRange(0, max_val * 1.15 if max_val > 0 else 100)
        axis_y.setLabelFormat("%.0f €")
        self._style_axis(axis_y)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        total_income = sum(s.total_income for _, s in data)
        total_expense = sum(s.total_expense for _, s in data)
        self.info_label.setText(
            f"Gesamt: Einnahmen {self._fmt(total_income)} · "
            f"Ausgaben {self._fmt(total_expense)} · "
            f"Bilanz {self._fmt(total_income - total_expense)}"
        )

    # 2. Balance Trend Line Chart
    def _build_balance_trend(self):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        data = self._load_all_data()
        self.chart.setTitle("Monatliche Bilanz im Verlauf")

        series = QLineSeries()
        series.setName("Bilanz")
        series.setColor(QColor(CHART_COLORS["balance"]))
        pen = series.pen()
        pen.setWidth(3)
        series.setPen(pen)

        categories = []
        min_val = 0.0
        max_val = 0.0
        for i, (label, sheet) in enumerate(data):
            categories.append(label)
            balance = sheet.balance
            series.append(i, balance)
            min_val = min(min_val, balance)
            max_val = max(max_val, balance)

        self.chart.addSeries(series)

        # X axis
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self._style_axis(axis_x)
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y axis
        margin = max(abs(max_val), abs(min_val)) * 0.15
        axis_y = QValueAxis()
        axis_y.setRange(min_val - margin if min_val - margin < 0 else 0, max_val + margin if max_val > 0 else 100)
        axis_y.setLabelFormat("%.0f €")
        self._style_axis(axis_y)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        avg_balance = sum(s.balance for _, s in data) / len(data) if data else 0
        self.info_label.setText(
            f"Durchschnittliche monatl. Bilanz: {self._fmt(avg_balance)}"
        )

    # 3. Savings Rate
    def _build_savings_rate(self):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        data = self._load_all_data()
        self.chart.setTitle("Sparquote pro Monat")

        series = QLineSeries()
        series.setName("Sparquote (%)")
        series.setColor(QColor(CHART_COLORS["savings"]))
        pen = series.pen()
        pen.setWidth(3)
        series.setPen(pen)

        categories = []
        max_rate = 0.0
        min_rate = 0.0
        rates = []
        for i, (label, sheet) in enumerate(data):
            categories.append(label)
            if sheet.total_income > 0:
                rate = ((sheet.total_income - sheet.total_expense) / sheet.total_income) * 100
            else:
                rate = 0.0
            rates.append(rate)
            series.append(i, rate)
            max_rate = max(max_rate, rate)
            min_rate = min(min_rate, rate)

        self.chart.addSeries(series)

        # X axis
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self._style_axis(axis_x)
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y axis
        axis_y = QValueAxis()
        axis_y.setRange(min(min_rate - 10, -10), max(max_rate + 10, 110))
        axis_y.setLabelFormat("%.0f %%")
        self._style_axis(axis_y)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        avg_rate = sum(rates) / len(rates) if rates else 0
        self.info_label.setText(f"Durchschnittliche Sparquote: {avg_rate:.1f} %")

    # 4. Total categories pie
    def _build_total_categories(self):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        data = self._load_all_data()
        self.chart.setTitle("Ausgaben nach Kategorie (alle Monate)")

        # Aggregate categories
        cats: dict[str, float] = {}
        for _, sheet in data:
            for cat, amount in sheet.expense_by_category().items():
                cats[cat] = cats.get(cat, 0.0) + amount

        if not cats:
            self.chart.setTitle("Keine Ausgaben vorhanden")
            self.info_label.setText("")
            return

        series = QPieSeries()
        series.setHoleSize(0.35)
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)

        for i, (cat, amount) in enumerate(sorted_cats):
            sl = series.append(f"{cat}: {self._fmt(amount)}", amount)
            sl.setBrush(QColor(CATEGORY_COLORS[i % len(CATEGORY_COLORS)]))
            sl.setBorderColor(QColor("#16213e"))
            sl.setBorderWidth(2)

        if series.count() > 0:
            biggest = series.slices()[0]
            biggest.setExploded(True)
            biggest.setExplodeDistanceFactor(0.06)
            biggest.setLabelVisible(True)
            biggest.setLabelColor(QColor("#e0e0e0"))
            lf = QFont()
            lf.setPointSize(10)
            lf.setBold(True)
            biggest.setLabelFont(lf)

        self.chart.addSeries(series)

        total = sum(cats.values())
        self.info_label.setText(
            f"Gesamtausgaben: {self._fmt(total)} in {len(cats)} Kategorien "
            f"über {len(data)} Monate"
        )

    # 5. Top 5 categories stacked bar
    def _build_top5_categories(self):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        data = self._load_all_data()
        self.chart.setTitle("Top 5 Ausgaben-Kategorien pro Monat")

        # Find top 5 categories globally
        global_cats: dict[str, float] = {}
        for _, sheet in data:
            for cat, amount in sheet.expense_by_category().items():
                global_cats[cat] = global_cats.get(cat, 0.0) + amount

        top5 = [c for c, _ in sorted(global_cats.items(), key=lambda x: x[1], reverse=True)[:5]]

        if not top5:
            self.chart.setTitle("Keine Ausgaben vorhanden")
            self.info_label.setText("")
            return

        bar_sets = {}
        for i, cat in enumerate(top5):
            bs = QBarSet(cat)
            bs.setColor(QColor(CATEGORY_COLORS[i % len(CATEGORY_COLORS)]))
            bs.setBorderColor(QColor("#16213e"))
            bar_sets[cat] = bs

        categories = []
        max_val = 0.0
        for label, sheet in data:
            categories.append(label)
            month_cats = sheet.expense_by_category()
            month_total = 0.0
            for cat in top5:
                val = month_cats.get(cat, 0.0)
                bar_sets[cat].append(val)
                month_total += val
            max_val = max(max_val, month_total)

        series = QStackedBarSeries()
        for cat in top5:
            series.append(bar_sets[cat])
        self.chart.addSeries(series)

        # X axis
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self._style_axis(axis_x)
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y axis
        axis_y = QValueAxis()
        axis_y.setRange(0, max_val * 1.15 if max_val > 0 else 100)
        axis_y.setLabelFormat("%.0f €")
        self._style_axis(axis_y)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.info_label.setText(
            f"Top 5: {', '.join(top5)}"
        )

    # ─── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _fmt(value: float) -> str:
        sign = "-" if value < 0 else ""
        value = abs(value)
        integer_part = int(value)
        decimal_part = round((value - integer_part) * 100)
        int_str = f"{integer_part:,}".replace(",", ".")
        return f"{sign}{int_str},{decimal_part:02d} €"
