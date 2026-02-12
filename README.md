# 💰 CashMonitor

**Persönlicher Finanz-Tracker** – Eine Desktop-Anwendung zur Verwaltung monatlicher Ein- und Ausgaben.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.6+-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 📅 **Monatliche Übersicht** – Navigation zwischen Monaten mit ◀ / ▶
- ➕ **Einnahmen & Ausgaben** – Datum, Kategorie, Betrag, Beschreibung
- 📊 **Pie-Chart** – Ausgaben nach Kategorie visualisiert
- 📈 **Statistiken** – Multi-Monats-Charts (Bilanz-Verlauf, Sparquote, Top-Kategorien)
- � **CSV-Export** – Für Excel, LibreCalc oder weitere Analyse
- 🔄 **Wiederkehrende Einträge** – Fixkosten & Daueraufträge automatisch
- � **Sparziele & Rollover** – Ziele verfolgen & automatischer Saldo-Übertrag
- 🔮 **Prognose** – Vorschau auf kommende Monate und ausstehende Fixkosten
- 🔒 **PIN-Schutz** – Bearbeiten/Löschen nur mit PIN (inkl. Reset-Code)
- 🌙 **Dark Theme** – Modernes, dunkles Design

## 🚀 Installation

### Voraussetzungen
- Python 3.10 oder neuer

### Setup
```bash
git clone https://github.com/PavelPys90/CashMonitor.git
cd CashMonitor
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# oder: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Starten
```bash
source venv/bin/activate
python main.py
```

### Windows Release
Unter [Releases](../../releases) findest du vorgefertigte `.exe`-Dateien – kein Python nötig!

## 📁 Projektstruktur

```
CashMonitor/
├── main.py                 ← Einstiegspunkt
├── main_window.py          ← Hauptfenster (Navigation, Tabelle, Summary)
├── transaction_dialog.py   ← Dialog: Transaktion hinzufügen/bearbeiten
├── charts_dialog.py        ← Statistik-Diagramme
├── about_dialog.py         ← Info-Dialog
├── pin_manager.py          ← PIN-Schutz
├── data_manager.py         ← JSON-Datenverwaltung
├── style.qss               ← Dark Theme
├── requirements.txt        ← Dependencies
└── data/                   ← Monatsdaten (YYYY-MM.json)
```

## 🛠️ Entwicklung

### Pull Requests
Änderungen am `main`-Branch dürfen nur über **Pull Requests** erfolgen.
1.  Erstelle einen neuen Branch (`feature/xyz` oder `fix/abc`).
2.  Mache deine Änderungen.
3.  Erstelle einen Pull Request auf GitHub.
4.  Nach Review und Tests wird gemerged.

## 📊 Datenformat

Pro Monat eine JSON-Datei (`data/2026-02.json`):
```json
{
  "month": "2026-02",
  "transactions": [
    {
      "id": "uuid",
      "date": "2026-02-05",
      "type": "expense",
      "category": "Einkauf",
      "amount": 45.99,
      "description": "Wocheneinkauf Rewe"
    }
  ]
}
```


