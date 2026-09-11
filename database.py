import sqlite3
import os
import shutil
import hashlib
from datetime import datetime

DB_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sahakari.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def copy_to_uploads(src_path, prefix=""):
    """Copy a file into the uploads folder and return the destination path."""
    ensure_upload_dir()
    ext      = os.path.splitext(src_path)[1]
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_name = f"{prefix}_{stamp}{ext}"
    dst_path = os.path.join(UPLOAD_DIR, dst_name)
    shutil.copy2(src_path, dst_path)
    return dst_path


# ─── Schema creation ──────────────────────────────────────────────────────────

def initialize_database():
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            full_name TEXT NOT NULL,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_no TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            citizenship_no TEXT,
            dob TEXT,
            join_date TEXT NOT NULL,
            photo_path TEXT,
            doc_path TEXT,
            occupation TEXT,
            nominee_name TEXT,
            nominee_relation TEXT,
            status TEXT DEFAULT 'active',
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            share_no INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            rate REAL NOT NULL DEFAULT 100.0,
            amount REAL NOT NULL,
            purchase_date TEXT NOT NULL,
            certificate_no TEXT,
            type TEXT DEFAULT 'purchase',
            transferred_to INTEGER,
            narration TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS savings_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no TEXT UNIQUE NOT NULL,
            member_id INTEGER NOT NULL,
            account_type TEXT NOT NULL DEFAULT 'Regular',
            balance REAL NOT NULL DEFAULT 0.0,
            interest_rate REAL NOT NULL DEFAULT 6.0,
            opened_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS savings_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            narration TEXT,
            voucher_no TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES savings_accounts(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_no TEXT UNIQUE NOT NULL,
            member_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL DEFAULT 'Personal',
            applied_amount REAL NOT NULL,
            approved_amount REAL,
            interest_rate REAL NOT NULL DEFAULT 12.0,
            duration_months INTEGER NOT NULL,
            emi REAL,
            purpose TEXT,
            collateral TEXT,
            application_date TEXT NOT NULL,
            approved_date TEXT,
            issue_date TEXT,
            status TEXT DEFAULT 'applied',
            approved_by INTEGER,
            total_paid REAL DEFAULT 0.0,
            outstanding REAL DEFAULT 0.0,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS loan_repayments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            principal_paid REAL NOT NULL DEFAULT 0.0,
            interest_paid REAL NOT NULL DEFAULT 0.0,
            total_paid REAL NOT NULL,
            outstanding_balance REAL NOT NULL,
            voucher_no TEXT,
            narration TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES loans(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT UNIQUE NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_no TEXT UNIQUE NOT NULL,
            entry_date TEXT NOT NULL,
            narration TEXT NOT NULL,
            total_debit REAL NOT NULL,
            total_credit REAL NOT NULL,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit REAL DEFAULT 0.0,
            credit REAL DEFAULT 0.0,
            narration TEXT,
            FOREIGN KEY (entry_id) REFERENCES journal_entries(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            income_date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            narration TEXT,
            voucher_no TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            narration TEXT,
            voucher_no TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cur.execute("SELECT id FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username,password,role,full_name,phone) VALUES (?,?,'admin','System Administrator','9800000000')",
            ("admin", hash_password("admin123"))
        )

    _insert_default_accounts(cur)
    conn.commit()
    conn.close()

    _migrate_db()
    ensure_upload_dir()


def _migrate_db():
    """Add any missing columns to existing databases (upgrade path)."""
    conn = get_connection()
    cur  = conn.cursor()
    migrations = [
        "ALTER TABLE members ADD COLUMN photo_path TEXT",
        "ALTER TABLE members ADD COLUMN doc_path TEXT",
    ]
    for sql in migrations:
        try:
            cur.execute(sql)
        except Exception:
            pass
    conn.commit()
    conn.close()


def _insert_default_accounts(cur):
    accs = [
        ("1100", "Cash in Hand",        "asset"),
        ("1200", "Bank Account",         "asset"),
        ("1300", "Loans Receivable",     "asset"),
        ("1400", "Interest Receivable",  "asset"),
        ("2100", "Member Deposits",      "liability"),
        ("2200", "Share Capital",        "liability"),
        ("2300", "Borrowings",           "liability"),
        ("3100", "Interest on Loans",    "income"),
        ("3200", "Membership Fee",       "income"),
        ("3300", "Service Charges",      "income"),
        ("3400", "Other Income",         "income"),
        ("4100", "Staff Salary",         "expense"),
        ("4200", "Office Rent",          "expense"),
        ("4300", "Stationery",           "expense"),
        ("4400", "Utilities",            "expense"),
        ("4500", "Interest on Deposits", "expense"),
        ("4600", "Miscellaneous",        "expense"),
    ]
    for code, name, atype in accs:
        cur.execute(
            "INSERT OR IGNORE INTO accounts (account_code,account_name,account_type) VALUES (?,?,?)",
            (code, name, atype)
        )


# ─── Generic helpers ──────────────────────────────────────────────────────────

def fetch_all(query, params=()):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def fetch_one(query, params=()):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def execute(query, params=()):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def execute_atomic(queries_and_params):
    """Execute multiple (query, params) pairs in a single transaction."""
    conn = get_connection()
    cur  = conn.cursor()
    try:
        for query, params in queries_and_params:
            cur.execute(query, params)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()


# ─── Business helpers ─────────────────────────────────────────────────────────

def next_member_no():
    row = fetch_one("SELECT MAX(CAST(SUBSTR(member_no,2) AS INTEGER)) AS mx FROM members")
    mx  = row["mx"] if row and row["mx"] else 0
    return f"M{mx+1:05d}"


def next_share_no():
    """
    Returns the next available share number.
    Accounts for the quantity of the last purchase so blocks don't overlap.
    E.g. if last record has share_no=19001, quantity=5, the next is 19006.
    """
    row = fetch_one(
        "SELECT share_no, quantity FROM shares ORDER BY CAST(share_no AS INTEGER) DESC LIMIT 1"
    )
    if row and row["share_no"]:
        return int(row["share_no"]) + int(row["quantity"])
    return 19001


def share_range_label(share_no, quantity):
    """Returns a human-readable share number range string."""
    sn = int(share_no)
    qty = int(quantity)
    if qty == 1:
        return str(sn)
    return f"{sn}–{sn + qty - 1}"


def next_cert_no():
    row = fetch_one(
        "SELECT MAX(CAST(SUBSTR(certificate_no,5) AS INTEGER)) AS mx FROM shares WHERE certificate_no IS NOT NULL"
    )
    mx = row["mx"] if row and row["mx"] else 0
    return f"CERT{mx+1:05d}"


def next_account_no():
    row = fetch_one("SELECT MAX(CAST(SUBSTR(account_no,3) AS INTEGER)) AS mx FROM savings_accounts")
    mx  = row["mx"] if row and row["mx"] else 0
    return f"SA{mx+1:06d}"


def next_loan_no():
    row = fetch_one("SELECT MAX(CAST(SUBSTR(loan_no,2) AS INTEGER)) AS mx FROM loans")
    mx  = row["mx"] if row and row["mx"] else 0
    return f"L{mx+1:05d}"


def next_entry_no():
    row = fetch_one("SELECT MAX(CAST(SUBSTR(entry_no,3) AS INTEGER)) AS mx FROM journal_entries")
    mx  = row["mx"] if row and row["mx"] else 0
    return f"JE{mx+1:05d}"


def next_voucher_no(prefix="V"):
    row = fetch_one(
        "SELECT MAX(CAST(SUBSTR(voucher_no,2) AS INTEGER)) AS mx FROM savings_transactions WHERE voucher_no IS NOT NULL"
    )
    mx = row["mx"] if row and row["mx"] else 0
    return f"{prefix}{mx+1:06d}"


def calculate_emi(principal, annual_rate, months):
    if months <= 0:
        return 0.0
    if annual_rate == 0:
        return round(principal / months, 2)
    r   = annual_rate / 12 / 100
    emi = principal * r * ((1 + r) ** months) / (((1 + r) ** months) - 1)
    return round(emi, 2)


def get_dashboard_stats():
    s = {}
    s["total_members"]    = (fetch_one("SELECT COUNT(*) AS c FROM members WHERE status='active'") or {}).get("c", 0)
    s["male_members"]     = (fetch_one("SELECT COUNT(*) AS c FROM members WHERE gender='Male'  AND status='active'") or {}).get("c", 0)
    s["female_members"]   = (fetch_one("SELECT COUNT(*) AS c FROM members WHERE gender='Female' AND status='active'") or {}).get("c", 0)
    s["other_members"]    = (fetch_one("SELECT COUNT(*) AS c FROM members WHERE gender='Other' AND status='active'") or {}).get("c", 0)
    s["total_shares"]     = (fetch_one("SELECT COALESCE(SUM(quantity),0) AS v FROM shares") or {}).get("v", 0)
    s["share_value"]      = (fetch_one("SELECT COALESCE(SUM(amount),0)   AS v FROM shares") or {}).get("v", 0)
    s["total_savings"]    = (fetch_one("SELECT COALESCE(SUM(balance),0)  AS v FROM savings_accounts WHERE status='active'") or {}).get("v", 0)
    s["active_loans"]     = (fetch_one("SELECT COUNT(*) AS c FROM loans WHERE status='issued'") or {}).get("c", 0)
    s["loan_outstanding"] = (fetch_one("SELECT COALESCE(SUM(outstanding),0) AS v FROM loans WHERE status='issued'") or {}).get("v", 0)
    today = datetime.now().strftime("%Y-%m-%d")
    s["today_income"]  = (fetch_one("SELECT COALESCE(SUM(amount),0) AS v FROM daily_income  WHERE income_date=?",  (today,)) or {}).get("v", 0)
    s["today_expense"] = (fetch_one("SELECT COALESCE(SUM(amount),0) AS v FROM daily_expense WHERE expense_date=?", (today,)) or {}).get("v", 0)
    return s
