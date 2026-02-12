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
    ):
        self.id = tx_id or str(uuid.uuid4())
        self.date = tx_date  # "YYYY-MM-DD"
        self.type = tx_type  # "income" or "expense"
        self.category = category
        self.amount = round(amount, 2)
        self.description = description

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            tx_id=data.get("id"),
            tx_date=data["date"],
            tx_type=data["type"],
            category=data["category"],
            amount=data["amount"],
            description=data.get("description", ""),
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
            base = Path(__file__).parent
            self.data_dir = base / "data"
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
            try:
                parts = f.stem.split("-")
                months.append((int(parts[0]), int(parts[1])))
            except (ValueError, IndexError):
                continue
        return sorted(months)
