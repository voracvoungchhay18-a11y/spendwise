"""SQLite data layer: schema, CRUD helpers and settings. No dummy data is ever inserted."""
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "tracker.db"

DEFAULT_CATEGORIES = [
    "Food & Drinks", "Transportation", "Shopping", "Entertainment", "Education",
    "Bills & Utilities", "Healthcare", "Travel", "Other",
]
INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other Income"]
PAYMENT_METHODS = ["Cash", "Debit Card", "Credit Card", "Bank Transfer", "Mobile Wallet", "QR Payment", "Other"]
COLUMNS = ["id", "type", "amount", "category", "date", "payment_method", "description"]


@contextmanager
def connect():
    """Open a connection that commits on success and rolls back on error."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    """Create tables (if missing) and seed the built-in category names."""
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('expense','income')),
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            description TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS categories(
            name TEXT PRIMARY KEY, is_custom INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS budgets(category TEXT PRIMARY KEY, amount REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS goals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, target REAL NOT NULL, saved REAL NOT NULL DEFAULT 0);
        """)
        con.executemany("INSERT OR IGNORE INTO categories(name,is_custom) VALUES(?,0)",
                        [(c,) for c in DEFAULT_CATEGORIES])


# ---------- settings ----------
def get_setting(key, default=None):
    with connect() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    with connect() as con:
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))


# ---------- transactions ----------
def _validate(kind, amount, category, method):
    if kind not in ("expense", "income"):
        raise ValueError("Type must be expense or income.")
    if amount is None or float(amount) <= 0:
        raise ValueError("Amount must be greater than 0.")
    if not category or not method:
        raise ValueError("Category and payment method are required.")


def add_transaction(kind, amount, category, tx_date, method, description=""):
    _validate(kind, amount, category, method)
    with connect() as con:
        con.execute("INSERT INTO transactions(type,amount,category,date,payment_method,description) "
                    "VALUES(?,?,?,?,?,?)",
                    (kind, float(amount), category, str(tx_date), method, description.strip()))


def update_transaction(tid, kind, amount, category, tx_date, method, description=""):
    _validate(kind, amount, category, method)
    with connect() as con:
        con.execute("UPDATE transactions SET type=?,amount=?,category=?,date=?,payment_method=?,description=? "
                    "WHERE id=?", (kind, float(amount), category, str(tx_date), method, description.strip(), tid))


def delete_transaction(tid):
    with connect() as con:
        con.execute("DELETE FROM transactions WHERE id=?", (tid,))


def load_transactions() -> pd.DataFrame:
    with connect() as con:
        df = pd.read_sql_query("SELECT * FROM transactions", con)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS).astype({"date": "datetime64[ns]", "amount": "float"})
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------- categories & budgets ----------
def get_categories():
    with connect() as con:
        return [r["name"] for r in con.execute("SELECT name FROM categories ORDER BY is_custom, rowid")]


def get_custom_categories():
    with connect() as con:
        return [r["name"] for r in con.execute("SELECT name FROM categories WHERE is_custom=1 ORDER BY name")]


def add_category(name):
    name = name.strip()
    if not name:
        raise ValueError("Category name cannot be empty.")
    if name.lower() in [c.lower() for c in get_categories() + INCOME_CATEGORIES]:
        raise ValueError(f"'{name}' already exists.")
    with connect() as con:
        con.execute("INSERT INTO categories(name,is_custom) VALUES(?,1)", (name,))


def delete_category(name):
    """Delete a custom category; its transactions move to 'Other'."""
    with connect() as con:
        con.execute("UPDATE transactions SET category='Other' WHERE category=? AND type='expense'", (name,))
        con.execute("DELETE FROM budgets WHERE category=?", (name,))
        con.execute("DELETE FROM categories WHERE name=? AND is_custom=1", (name,))


def get_budgets() -> dict:
    with connect() as con:
        return {r["category"]: r["amount"] for r in con.execute("SELECT * FROM budgets")}


def set_budget(category, amount):
    """Store a budget; amount <= 0 removes it. Use category '__monthly__' for the overall budget."""
    with connect() as con:
        if amount and amount > 0:
            con.execute("INSERT OR REPLACE INTO budgets(category,amount) VALUES(?,?)", (category, float(amount)))
        else:
            con.execute("DELETE FROM budgets WHERE category=?", (category,))


# ---------- savings goals ----------
def get_goals() -> pd.DataFrame:
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM goals ORDER BY id", con)


def add_goal(name, target, saved=0.0):
    if not name.strip() or target <= 0:
        raise ValueError("Give the goal a name and a target above 0.")
    with connect() as con:
        con.execute("INSERT INTO goals(name,target,saved) VALUES(?,?,?)", (name.strip(), float(target), float(saved)))


def add_to_goal(gid, amount):
    with connect() as con:
        con.execute("UPDATE goals SET saved=MAX(saved+?,0) WHERE id=?", (float(amount), gid))


def delete_goal(gid):
    with connect() as con:
        con.execute("DELETE FROM goals WHERE id=?", (gid,))
