"""
CashMonitor – Data Manager
Handles CRUD operations on monthly JSON transaction files.
"""

import json
import os
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from utils import get_app_dir


# Default categories
EXPENSE_CATEGORIES = [
    "Einkauf",
    "Miete",
    "Strom/Gas/Wasser",
    "Internet/Telefon",
    "Versicherung",
    "Transport",
    "Freizeit",
    "Restaurant/Café",
    "Kleidung",
    "Gesundheit",
    "Bildung",
    "Abonnements",
    "Haushalt",
    "Geschenke",
    "Sonstiges",
]

INCOME_CATEGORIES = [
    "Gehalt",
    "Freelance",
    "Nebenjob",
    "Zinsen",
    "Dividenden",
    "Verkauf",
    "Geschenk",
    "Erstattung",
    "Sonstiges",
]


class Transaction:
    """Represents a single financial transaction."""

    def __init__(
        self,
        tx_date: str,
        tx_type: str,
        category: str,
        amount: float,
        description: str = "",
        tx_id: Optional[str] = None,
        recurring_id: Optional[str] = None,
        is_rollover: bool = False,
    ):
        self.id = tx_id or str(uuid.uuid4())
        self.date = tx_date  # "YYYY-MM-DD"
        self.type = tx_type  # "income" or "expense"
        self.category = category
        self.amount = round(amount, 2)
        self.description = description
        self.recurring_id = recurring_id  # links to RecurringItem.id if auto-generated
        self.is_rollover = is_rollover

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "date": self.date,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
        }
        if self.recurring_id:
            d["recurring_id"] = self.recurring_id
        if self.is_rollover:
            d["is_rollover"] = True
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            tx_id=data.get("id"),
            tx_date=data["date"],
            tx_type=data["type"],
            category=data["category"],
            amount=data["amount"],
            description=data.get("description", ""),
            recurring_id=data.get("recurring_id"),
            is_rollover=data.get("is_rollover", False),
        )


class MonthSheet:
    """Represents all transactions for a single month."""

    def __init__(self, year: int, month: int):
        self.year = year
        self.month = month
        self.transactions: list[Transaction] = []

    @property
    def month_key(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def incomes(self) -> list[Transaction]:
        return [t for t in self.transactions if t.type == "income"]

    @property
    def expenses(self) -> list[Transaction]:
        return [t for t in self.transactions if t.type == "expense"]

    @property
    def total_income(self) -> float:
        return round(sum(t.amount for t in self.incomes), 2)

    @property
    def total_expense(self) -> float:
        return round(sum(t.amount for t in self.expenses), 2)

    @property
    def balance(self) -> float:
        return round(self.total_income - self.total_expense, 2)

    def expense_by_category(self) -> dict[str, float]:
        cats: dict[str, float] = {}
        for t in self.expenses:
            cats[t.category] = round(cats.get(t.category, 0.0) + t.amount, 2)
        return cats

    def income_by_category(self) -> dict[str, float]:
        cats: dict[str, float] = {}
        for t in self.incomes:
            cats[t.category] = round(cats.get(t.category, 0.0) + t.amount, 2)
        return cats

    def to_dict(self) -> dict:
        return {
            "month": self.month_key,
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonthSheet":
        parts = data["month"].split("-")
        sheet = cls(int(parts[0]), int(parts[1]))
        sheet.transactions = [
            Transaction.from_dict(t) for t in data.get("transactions", [])
        ]
        return sheet


class DataManager:
    """Manages loading/saving of monthly JSON sheets."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            self.data_dir = get_app_dir() / "data"
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, year: int, month: int) -> Path:
        return self.data_dir / f"{year:04d}-{month:02d}.json"

    def load_month(self, year: int, month: int) -> MonthSheet:
        """Load a monthly sheet from JSON. Creates empty sheet if file doesn't exist."""
        path = self._file_path(year, month)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return MonthSheet.from_dict(data)
        return MonthSheet(year, month)

    def save_month(self, sheet: MonthSheet) -> None:
        """Save a monthly sheet to JSON."""
        path = self._file_path(sheet.year, sheet.month)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sheet.to_dict(), f, ensure_ascii=False, indent=2)

    def add_transaction(self, sheet: MonthSheet, transaction: Transaction) -> None:
        """Add a transaction to a sheet and save."""
        sheet.transactions.append(transaction)
        # Sort by date
        sheet.transactions.sort(key=lambda t: t.date)
        self.save_month(sheet)

    def delete_transaction(self, sheet: MonthSheet, tx_id: str) -> bool:
        """Delete a transaction by ID. Returns True if found and deleted."""
        for i, t in enumerate(sheet.transactions):
            if t.id == tx_id:
                sheet.transactions.pop(i)
                self.save_month(sheet)
                return True
        return False

    def update_transaction(
        self, sheet: MonthSheet, tx_id: str, updated: Transaction
    ) -> bool:
        """Update a transaction by ID. Returns True if found and updated."""
        for i, t in enumerate(sheet.transactions):
            if t.id == tx_id:
                updated.id = tx_id
                sheet.transactions[i] = updated
                sheet.transactions.sort(key=lambda t: t.date)
                self.save_month(sheet)
                return True
        return False

    def get_available_months(self) -> list[tuple[int, int]]:
        """Return a sorted list of (year, month) tuples for which data exists."""
        months = []
        for f in self.data_dir.glob("*.json"):
            if f.stem == "recurring":
                continue
            try:
                parts = f.stem.split("-")
                months.append((int(parts[0]), int(parts[1])))
            except (ValueError, IndexError):
                continue
        return sorted(months)

    def get_total_expenses_for_category(self, category: str) -> float:
        """Calculate total expenses for a given category across all available months."""
        total = 0.0
        for year, month in self.get_available_months():
            sheet = self.load_month(year, month)
            # Find expenses with this category
            # Note: Category matching should be exact or startswith?
            # User might use "Sparen: Urlaub" vs "Urlaub".
            # Let's assume exact match for now, or maybe the goal IS the category.
            # "Sparen: Japan" -> Category is "Sparen: Japan".
            for tx in sheet.expenses:
                if tx.category == category:
                    total += tx.amount
        return round(total, 2)

    def _get_previous_month(self, year: int, month: int) -> tuple[int, int]:
        """Return the previous month as (year, month)."""
        if month == 1:
            return year - 1, 12
        return year, month - 1

    def update_rollover(self, sheet: MonthSheet):
        """Calculate previous month's balance and insert/update rollover transaction."""
        prev_year, prev_month = self._get_previous_month(sheet.year, sheet.month)
        
        available = self.get_available_months()
        if (prev_year, prev_month) not in available:
            # No previous data -> Remove any existing rollover
            self._remove_rollover(sheet)
            self.save_month(sheet)
            return

        # Load real data
        prev_sheet = self.load_month(prev_year, prev_month)
        
        balance = prev_sheet.balance
        
        # Remove old rollover
        self._remove_rollover(sheet)
        
        if abs(balance) > 0.001:
            # Create new rollover
            tx_type = "income" if balance > 0 else "expense"
            # Rollover is always on the 1st of the month
            tx_date = f"{sheet.year:04d}-{sheet.month:02d}-01"
            
            tx = Transaction(
                tx_date=tx_date,
                tx_type=tx_type,
                category="Startguthaben" if balance > 0 else "Vorjahresdefizit",
                amount=abs(balance),
                description=f"Übertrag aus {prev_year:04d}-{prev_month:02d}",
                is_rollover=True
            )
            sheet.transactions.insert(0, tx) # Put at top
        
        self.save_month(sheet)

    def _remove_rollover(self, sheet: MonthSheet):
        """Remove any transaction marked as rollover."""
        sheet.transactions = [t for t in sheet.transactions if not getattr(t, 'is_rollover', False)]


class RecurringItem:
    """A recurring transaction template."""

    def __init__(
        self,
        day: int,
        tx_type: str,
        category: str,
        amount: float,
        description: str = "",
        item_id: Optional[str] = None,
        active: bool = True,
    ):
        self.id = item_id or str(uuid.uuid4())
        self.day = min(max(day, 1), 28)  # clamp to 1-28
        self.type = tx_type
        self.category = category
        self.amount = round(amount, 2)
        self.description = description
        self.active = active

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day": self.day,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringItem":
        return cls(
            item_id=data.get("id"),
            day=data.get("day", 1),
            tx_type=data["type"],
            category=data["category"],
            amount=data["amount"],
            description=data.get("description", ""),
            active=data.get("active", True),
        )


class RecurringManager:
    """Manages recurring transaction templates."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.items: list[RecurringItem] = []
        self._load()

    @property
    def _file_path(self) -> Path:
        return self.data_dir / "recurring.json"

    def _load(self):
        if self._file_path.exists():
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.items = [
                RecurringItem.from_dict(r) for r in data.get("recurring", [])
            ]
        else:
            self.items = []

    def _save(self):
        data = {"recurring": [item.to_dict() for item in self.items]}
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, item: RecurringItem):
        self.items.append(item)
        self._save()

    def delete(self, item_id: str) -> bool:
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self._save()
                return True
        return False

    def update(self, item_id: str, updated: RecurringItem) -> bool:
        for i, item in enumerate(self.items):
            if item.id == item_id:
                updated.id = item_id
                self.items[i] = updated
                self._save()
                return True
        return False

    def toggle_active(self, item_id: str) -> bool:
        for item in self.items:
            if item.id == item_id:
                item.active = not item.active
                self._save()
                return True
        return False

    def apply_recurring(self, sheet: MonthSheet, dm: "DataManager"):
        """Apply all active recurring items to a month sheet if not already present."""
        existing_recurring_ids = {
            t.recurring_id for t in sheet.transactions if t.recurring_id
        }

        added = False
        for item in self.items:
            if not item.active:
                continue
            if item.id in existing_recurring_ids:
                continue

            # For current month: only apply if day <= today
            today = date.today()
            if sheet.year == today.year and sheet.month == today.month:
                if item.day > today.day:
                    continue

            tx_date = f"{sheet.year:04d}-{sheet.month:02d}-{item.day:02d}"
            tx = Transaction(
                tx_date=tx_date,
                tx_type=item.type,
                category=item.category,
                amount=item.amount,
                description=item.description,
                recurring_id=item.id,
            )
            sheet.transactions.append(tx)
            added = True

        if added:
            sheet.transactions.sort(key=lambda t: t.date)
            dm.save_month(sheet)


class SavingsGoal:
    """A savings goal linked to a specific category."""

    def __init__(
        self,
        name: str,
        target_amount: float,
        category: str,
        icon: str = "💰",
        color: str = "#10b981",
        goal_id: Optional[str] = None,
    ):
        self.id = goal_id or str(uuid.uuid4())
        self.name = name
        self.target_amount = target_amount
        self.category = category
        self.icon = icon
        self.color = color

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": self.target_amount,
            "category": self.category,
            "icon": self.icon,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SavingsGoal":
        return cls(
            goal_id=data.get("id"),
            name=data["name"],
            target_amount=data["target_amount"],
            category=data["category"],
            icon=data.get("icon", "💰"),
            color=data.get("color", "#10b981"),
        )


class SavingsManager:
    """Manages savings goals in savings.json."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
             self.file_path = get_app_dir() / "data" / "savings.json"
        else:
            self.file_path = data_dir / "savings.json"
        
        self.goals: list[SavingsGoal] = []
        self._load()

    def _load(self):
        if not self.file_path.exists():
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.goals = [SavingsGoal.from_dict(item) for item in data.get("goals", [])]
        except (json.JSONDecodeError, OSError):
            self.goals = []

    def _save(self):
        data = {"goals": [g.to_dict() for g in self.goals]}
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def add(self, goal: SavingsGoal):
        self.goals.append(goal)
        self._save()

    def update(self, goal_id: str, updated: SavingsGoal) -> bool:
        for i, g in enumerate(self.goals):
            if g.id == goal_id:
                updated.id = goal_id
                self.goals[i] = updated
                self._save()
                return True
        return False

    def delete(self, goal_id: str):
        self.goals = [g for g in self.goals if g.id != goal_id]
        self._save()


