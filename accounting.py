import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

import database as db
import styles as st


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sahakari.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def _get_connection():
    """
    Direct SQLite connection.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# TABLE HELPERS
# ============================================================

def _table_exists(table_name):

    conn = _get_connection()

    try:

        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (table_name,)
        ).fetchone()

        return row is not None

    finally:

        conn.close()


def _get_columns(table_name):
    """
    Return the columns that currently exist in a table.
    """

    if not _table_exists(table_name):
        return set()

    conn = _get_connection()

    try:

        rows = conn.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return {
            row["name"]
            for row in rows
        }

    finally:

        conn.close()


def _add_column_if_missing(
    table_name,
    column_name,
    definition
):
    """
    Add a missing column to an existing table.
    """

    columns = _get_columns(table_name)

    if column_name in columns:
        return

    conn = _get_connection()

    try:

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {definition}
            """
        )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# ENSURE ACCOUNTING TABLES
# ============================================================

def _ensure_accounting_tables():
    """
    Create accounting tables and repair older databases.

    IMPORTANT:
    Existing journal_entries tables may contain mandatory
    columns such as total_debit and total_credit.

    Those columns are now supported.
    """

    conn = _get_connection()

    try:

        cur = conn.cursor()

        # ====================================================
        # GL ACCOUNTS
        # ====================================================

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS gl_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                description TEXT DEFAULT ''
            )
            """
        )

        # ====================================================
        # JOURNAL ENTRIES
        # ====================================================

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jv_no TEXT,
                entry_date TEXT,
                dr_account TEXT,
                cr_account TEXT,
                amount REAL DEFAULT 0,
                total_debit REAL NOT NULL DEFAULT 0,
                total_credit REAL NOT NULL DEFAULT 0,
                narration TEXT DEFAULT '',
                reference TEXT DEFAULT '',
                created_by INTEGER
            )
            """
        )

        conn.commit()

    finally:

        conn.close()

    # ========================================================
    # REPAIR EXISTING JOURNAL TABLE
    # ========================================================

    required_columns = {

        "jv_no":
            "TEXT",

        "entry_date":
            "TEXT",

        "dr_account":
            "TEXT",

        "cr_account":
            "TEXT",

        "amount":
            "REAL DEFAULT 0",

        "total_debit":
            "REAL NOT NULL DEFAULT 0",

        "total_credit":
            "REAL NOT NULL DEFAULT 0",

        "narration":
            "TEXT DEFAULT ''",

        "reference":
            "TEXT DEFAULT ''",

        "created_by":
            "INTEGER"
    }

    for column, definition in required_columns.items():

        _add_column_if_missing(
            "journal_entries",
            column,
            definition
        )

    # ========================================================
    # REPAIR NULL VALUES
    # ========================================================

    conn = _get_connection()

    try:

        conn.execute(
            """
            UPDATE journal_entries
            SET
                amount = COALESCE(amount, 0),
                total_debit = COALESCE(total_debit, amount, 0),
                total_credit = COALESCE(total_credit, amount, 0)
            """
        )

        conn.commit()

    finally:

        conn.close()

    # ========================================================
    # REPAIR NULL JV NUMBERS
    # ========================================================

    conn = _get_connection()

    try:

        rows = conn.execute(
            """
            SELECT id
            FROM journal_entries
            WHERE jv_no IS NULL
               OR TRIM(jv_no) = ''
            ORDER BY id
            """
        ).fetchall()

        for row in rows:

            jv_no = _next_jv_no_direct()

            conn.execute(
                """
                UPDATE journal_entries
                SET jv_no=?
                WHERE id=?
                """,
                (
                    jv_no,
                    row["id"]
                )
            )

        conn.commit()

    finally:

        conn.close()

    # ========================================================
    # UNIQUE JV INDEX
    # ========================================================

    conn = _get_connection()

    try:

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_journal_entries_jv_no
            ON journal_entries(jv_no)
            """
        )

        conn.commit()

    except sqlite3.IntegrityError:

        # Existing duplicate JV numbers should not prevent
        # the application from starting.
        pass

    finally:

        conn.close()


# ============================================================
# DATABASE WRAPPERS
# ============================================================

def _fetch_all(sql, params=()):

    try:

        if hasattr(db, "fetch_all"):

            result = db.fetch_all(
                sql,
                params
            )

            return result

    except Exception:

        pass

    conn = _get_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            sql,
            params
        )

        return cur.fetchall()

    finally:

        conn.close()


def _fetch_one(sql, params=()):

    try:

        if hasattr(db, "fetch_one"):

            result = db.fetch_one(
                sql,
                params
            )

            return result

    except Exception:

        pass

    conn = _get_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            sql,
            params
        )

        return cur.fetchone()

    finally:

        conn.close()


def _execute(sql, params=()):

    try:

        if hasattr(db, "execute"):

            return db.execute(
                sql,
                params
            )

    except Exception:

        pass

    conn = _get_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            sql,
            params
        )

        conn.commit()

        return cur.lastrowid

    finally:

        conn.close()


def _execute_atomic(statements):

    try:

        if hasattr(db, "execute_atomic"):

            return db.execute_atomic(
                statements
            )

    except Exception:

        pass

    conn = _get_connection()

    try:

        cur = conn.cursor()

        for sql, params in statements:

            cur.execute(
                sql,
                params
            )

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# JV NUMBER
# ============================================================

def _next_jv_no_direct():
    """
    Generate next journal voucher number.

    JV-00001
    JV-00002
    JV-00003
    """

    conn = _get_connection()

    try:

        row = conn.execute(
            """
            SELECT jv_no
            FROM journal_entries
            WHERE jv_no IS NOT NULL
              AND TRIM(jv_no) != ''
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    except Exception:

        row = None

    finally:

        conn.close()

    if not row:

        return "JV-00001"

    previous = str(
        row["jv_no"]
    )

    try:

        number = int(
            previous.split("-")[-1]
        )

    except (
        ValueError,
        IndexError
    ):

        number = 0

    return f"JV-{number + 1:05d}"


def _next_jv_no():

    try:

        if hasattr(db, "next_jv_no"):

            value = db.next_jv_no()

            if value:

                return value

    except Exception:

        pass

    return _next_jv_no_direct()


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def create_frame(parent, user=None):

    _ensure_accounting_tables()

    frame = tk.Frame(
        parent,
        bg=st.BG_MAIN
    )

    AccountingPage(
        frame,
        user or {}
    )

    return frame


# ============================================================
# ACCOUNTING PAGE
# ============================================================

class AccountingPage:

    def __init__(
        self,
        parent,
        user=None
    ):

        self.parent = parent
        self.user = user or {}

        self._sel_code = None

        _ensure_accounting_tables()

        self._build()

    # ========================================================
    # MAIN BUILD
    # ========================================================

    def _build(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        hdr = tk.Frame(
            self.parent,
            bg=st.BG_CARD,
            height=58
        )

        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="Accounting (General Ledger)",
            font=st.FONT_HEADING,
            bg=st.BG_CARD,
            fg=st.PRIMARY
        ).pack(
            side="left",
            padx=20,
            pady=14
        )

        tk.Frame(
            self.parent,
            bg=st.BORDER,
            height=1
        ).pack(fill="x")

        # ----------------------------------------------------
        # NOTEBOOK
        # ----------------------------------------------------

        nb = ttk.Notebook(
            self.parent
        )

        nb.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=10
        )

        # ----------------------------------------------------
        # ACCOUNTS
        # ----------------------------------------------------

        t1 = tk.Frame(
            nb,
            bg=st.BG_MAIN
        )

        nb.add(
            t1,
            text="  Chart of Accounts  "
        )

        self._build_accounts(t1)

        # ----------------------------------------------------
        # JOURNAL
        # ----------------------------------------------------

        t2 = tk.Frame(
            nb,
            bg=st.BG_MAIN
        )

        nb.add(
            t2,
            text="  Journal Entries  "
        )

        self._build_journal(t2)

        # ----------------------------------------------------
        # TRIAL BALANCE
        # ----------------------------------------------------

        t3 = tk.Frame(
            nb,
            bg=st.BG_MAIN
        )

        nb.add(
            t3,
            text="  Trial Balance  "
        )

        self._build_trial(t3)

        # ----------------------------------------------------
        # PROFIT & LOSS
        # ----------------------------------------------------

        t4 = tk.Frame(
            nb,
            bg=st.BG_MAIN
        )

        nb.add(
            t4,
            text="  Profit & Loss  "
        )

        self._build_pl(t4)

    # ========================================================
    # CHART OF ACCOUNTS
    # ========================================================

    def _build_accounts(self, parent):

        toolbar = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        toolbar.pack(
            fill="x",
            padx=8,
            pady=8
        )

        ttk.Button(
            toolbar,
            text="➕  Add Account",
            style="Success.TButton",
            command=self._add_account
        ).pack(
            side="left",
            padx=(0, 6)
        )

        ttk.Button(
            toolbar,
            text="✏️  Edit Account",
            style="Info.TButton",
            command=self._edit_account
        ).pack(
            side="left",
            padx=(0, 6)
        )

        ttk.Button(
            toolbar,
            text="🔄  Refresh",
            style="Warning.TButton",
            command=self._load_accounts
        ).pack(
            side="right"
        )

        # ----------------------------------------------------
        # TREE
        # ----------------------------------------------------

        tf = tk.Frame(
            parent,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        tf.pack(
            fill="both",
            expand=True,
            padx=8
        )

        cols = (
            "Code",
            "Account Name",
            "Type",
            "Balance (Rs)",
            "Description"
        )

        self.acc_tree = ttk.Treeview(
            tf,
            columns=cols,
            show="headings"
        )

        vsb = ttk.Scrollbar(
            tf,
            orient="vertical",
            command=self.acc_tree.yview
        )

        self.acc_tree.configure(
            yscrollcommand=vsb.set
        )

        vsb.pack(
            side="right",
            fill="y"
        )

        self.acc_tree.pack(
            fill="both",
            expand=True
        )

        widths = [
            80,
            220,
            120,
            130,
            300
        ]

        for col, width in zip(
            cols,
            widths
        ):

            self.acc_tree.heading(
                col,
                text=col
            )

            self.acc_tree.column(
                col,
                width=width,
                anchor=(
                    "center"
                    if width <= 130
                    else "w"
                )
            )

        self.acc_tree.bind(
            "<<TreeviewSelect>>",
            self._on_acc_sel
        )

        self._load_accounts()

    # ========================================================
    # ACCOUNT SELECTION
    # ========================================================

    def _on_acc_sel(self, event=None):

        selection = self.acc_tree.selection()

        self._sel_code = (
            selection[0]
            if selection
            else None
        )

    # ========================================================
    # LOAD ACCOUNTS
    # ========================================================

    def _load_accounts(self):

        if not hasattr(
            self,
            "acc_tree"
        ):

            return

        try:

            self.acc_tree.delete(
                *self.acc_tree.get_children()
            )

            rows = _fetch_all(
                """
                SELECT
                    code,
                    name,
                    type,
                    balance,
                    description
                FROM gl_accounts
                ORDER BY code
                """
            )

            for index, row in enumerate(
                rows,
                1
            ):

                tag = (
                    "even"
                    if index % 2 == 0
                    else "odd"
                )

                balance = float(
                    row["balance"] or 0
                )

                self.acc_tree.insert(
                    "",
                    "end",
                    iid=str(row["code"]),
                    values=(
                        row["code"],
                        row["name"],
                        str(
                            row["type"]
                        ).title(),
                        f"{balance:,.2f}",
                        row["description"] or "-"
                    ),
                    tags=(tag,)
                )

            self.acc_tree.tag_configure(
                "even",
                background=st.ALT_ROW
            )

            self.acc_tree.tag_configure(
                "odd",
                background=st.BG_CARD
            )

        except Exception as e:

            messagebox.showerror(
                "Accounting Error",
                "Unable to load accounts.\n\n"
                f"{e}",
                parent=self.parent
            )

    # ========================================================
    # ADD ACCOUNT
    # ========================================================

    def _add_account(self):

        GLAccountDialog(
            self.parent,
            None,
            self._load_accounts
        )

    # ========================================================
    # EDIT ACCOUNT
    # ========================================================

    def _edit_account(self):

        if not self._sel_code:

            messagebox.showwarning(
                "Select Account",
                "Please select an account first.",
                parent=self.parent
            )

            return

        row = _fetch_one(
            """
            SELECT *
            FROM gl_accounts
            WHERE code=?
            """,
            (
                self._sel_code,
            )
        )

        if not row:

            messagebox.showerror(
                "Error",
                "Selected account was not found.",
                parent=self.parent
            )

            return

        GLAccountDialog(
            self.parent,
            row,
            self._load_accounts
        )

    # ========================================================
    # JOURNAL TAB
    # ========================================================

    def _build_journal(self, parent):

        je_card = tk.Frame(
            parent,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        je_card.pack(
            fill="x",
            padx=8,
            pady=(8, 4)
        )

        tk.Label(
            je_card,
            text="New Journal Entry",
            font=st.FONT_SUB,
            bg=st.BG_CARD,
            fg=st.PRIMARY
        ).pack(
            anchor="w",
            padx=12,
            pady=(10, 4)
        )

        tk.Frame(
            je_card,
            bg=st.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=12
        )

        je_form = tk.Frame(
            je_card,
            bg=st.BG_CARD
        )

        je_form.pack(
            fill="x",
            padx=12,
            pady=8
        )

        for column in (
            1,
            3,
            5
        ):

            je_form.columnconfigure(
                column,
                weight=1
            )

        self.je_vars = {}

        # ----------------------------------------------------
        # ACCOUNT CHOICES
        # ----------------------------------------------------

        accs = _fetch_all(
            """
            SELECT code, name
            FROM gl_accounts
            ORDER BY code
            """
        )

        choices = [
            f"{a['code']} - {a['name']}"
            for a in accs
        ]

        # ----------------------------------------------------
        # ROW 0
        # ----------------------------------------------------

        row0_fields = [
            (
                0,
                "Date *",
                "je_date",
                "entry"
            ),
            (
                2,
                "Debit Account *",
                "je_dr_acc",
                "combo"
            ),
            (
                4,
                "Credit Account *",
                "je_cr_acc",
                "combo"
            )
        ]

        for (
            col,
            label,
            key,
            widget_type
        ) in row0_fields:

            tk.Label(
                je_form,
                text=label,
                font=st.FONT_SMALL,
                bg=st.BG_CARD,
                fg=st.TEXT_MUTED
            ).grid(
                row=0,
                column=col,
                sticky="w",
                pady=4
            )

            self.je_vars[key] = tk.StringVar()

            if widget_type == "combo":

                widget = ttk.Combobox(
                    je_form,
                    textvariable=self.je_vars[key],
                    values=choices,
                    font=st.FONT_NORMAL,
                    width=24,
                    state="readonly"
                )

            else:

                widget = ttk.Entry(
                    je_form,
                    textvariable=self.je_vars[key],
                    font=st.FONT_NORMAL,
                    width=20
                )

            widget.grid(
                row=0,
                column=col + 1,
                sticky="ew",
                padx=(0, 12),
                pady=4
            )

        # ----------------------------------------------------
        # ROW 1
        # ----------------------------------------------------

        row1_fields = [
            (
                0,
                "Amount (Rs) *",
                "je_amount"
            ),
            (
                2,
                "Narration",
                "je_narration"
            ),
            (
                4,
                "Reference",
                "je_reference"
            )
        ]

        for (
            col,
            label,
            key
        ) in row1_fields:

            tk.Label(
                je_form,
                text=label,
                font=st.FONT_SMALL,
                bg=st.BG_CARD,
                fg=st.TEXT_MUTED
            ).grid(
                row=1,
                column=col,
                sticky="w",
                pady=4
            )

            self.je_vars[key] = tk.StringVar()

            widget = ttk.Entry(
                je_form,
                textvariable=self.je_vars[key],
                font=st.FONT_NORMAL,
                width=24
            )

            widget.grid(
                row=1,
                column=col + 1,
                sticky="ew",
                padx=(0, 12),
                pady=4
            )

        self.je_vars["je_date"].set(
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )

        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        je_bf = tk.Frame(
            je_card,
            bg=st.BG_CARD
        )

        je_bf.pack(
            anchor="w",
            padx=12,
            pady=(0, 10)
        )

        ttk.Button(
            je_bf,
            text="💾  Post Entry",
            style="Primary.TButton",
            command=self._post_je
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ttk.Button(
            je_bf,
            text="🔄  Reset",
            style="Warning.TButton",
            command=self._reset_je
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # JOURNAL HISTORY
        # ----------------------------------------------------

        tf = tk.Frame(
            parent,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        tf.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(0, 8)
        )

        cols = (
            "JV No",
            "Date",
            "Debit Account",
            "Credit Account",
            "Amount",
            "Narration",
            "Reference",
            "Posted By"
        )

        self.je_tree = ttk.Treeview(
            tf,
            columns=cols,
            show="headings"
        )

        vsb = ttk.Scrollbar(
            tf,
            orient="vertical",
            command=self.je_tree.yview
        )

        hsb = ttk.Scrollbar(
            tf,
            orient="horizontal",
            command=self.je_tree.xview
        )

        self.je_tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.pack(
            side="right",
            fill="y"
        )

        hsb.pack(
            side="bottom",
            fill="x"
        )

        self.je_tree.pack(
            fill="both",
            expand=True
        )

        widths = [
            90,
            100,
            180,
            180,
            120,
            180,
            120,
            140
        ]

        for col, width in zip(
            cols,
            widths
        ):

            self.je_tree.heading(
                col,
                text=col
            )

            self.je_tree.column(
                col,
                width=width,
                anchor=(
                    "center"
                    if width <= 120
                    else "w"
                )
            )

        self._load_journal()

    # ========================================================
    # RESET JOURNAL
    # ========================================================

    def _reset_je(self):

        for variable in self.je_vars.values():

            variable.set("")

        self.je_vars["je_date"].set(
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )

    # ========================================================
    # POST JOURNAL ENTRY
    # ========================================================

    def _post_je(self):

        # ====================================================
        # READ FORM
        # ====================================================

        date_s = (
            self.je_vars["je_date"]
            .get()
            .strip()
        )

        dr_raw = (
            self.je_vars["je_dr_acc"]
            .get()
            .strip()
        )

        cr_raw = (
            self.je_vars["je_cr_acc"]
            .get()
            .strip()
        )

        amount_raw = (
            self.je_vars["je_amount"]
            .get()
            .strip()
        )

        narration = (
            self.je_vars["je_narration"]
            .get()
            .strip()
        )

        reference = (
            self.je_vars["je_reference"]
            .get()
            .strip()
        )

        # ====================================================
        # DATE VALIDATION
        # ====================================================

        if not date_s:

            messagebox.showerror(
                "Error",
                "Date is required.",
                parent=self.parent
            )

            return

        try:

            datetime.strptime(
                date_s,
                "%Y-%m-%d"
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Date",
                "Date must be in YYYY-MM-DD format.",
                parent=self.parent
            )

            return

        # ====================================================
        # ACCOUNT VALIDATION
        # ====================================================

        if not dr_raw:

            messagebox.showerror(
                "Error",
                "Debit account is required.",
                parent=self.parent
            )

            return

        if not cr_raw:

            messagebox.showerror(
                "Error",
                "Credit account is required.",
                parent=self.parent
            )

            return

        # ====================================================
        # AMOUNT VALIDATION
        # ====================================================

        if not amount_raw:

            messagebox.showerror(
                "Invalid Amount",
                "Amount is required.",
                parent=self.parent
            )

            return

        try:

            amount = float(
                amount_raw.replace(
                    ",",
                    ""
                )
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Amount",
                "Please enter a valid amount.",
                parent=self.parent
            )

            return

        if amount <= 0:

            messagebox.showerror(
                "Invalid Amount",
                "Amount must be greater than zero.",
                parent=self.parent
            )

            return

        # ====================================================
        # PARSE DEBIT CODE
        # ====================================================

        if " - " in dr_raw:

            dr_code = dr_raw.split(
                " - ",
                1
            )[0].strip()

        elif "–" in dr_raw:

            dr_code = dr_raw.split(
                "–",
                1
            )[0].strip()

        else:

            dr_code = dr_raw.strip()

        # ====================================================
        # PARSE CREDIT CODE
        # ====================================================

        if " - " in cr_raw:

            cr_code = cr_raw.split(
                " - ",
                1
            )[0].strip()

        elif "–" in cr_raw:

            cr_code = cr_raw.split(
                "–",
                1
            )[0].strip()

        else:

            cr_code = cr_raw.strip()

        # ====================================================
        # FETCH DEBIT ACCOUNT
        # ====================================================

        dr_acc = _fetch_one(
            """
            SELECT *
            FROM gl_accounts
            WHERE code=?
            """,
            (
                dr_code,
            )
        )

        if not dr_acc:

            messagebox.showerror(
                "Error",
                f"Debit account '{dr_code}' not found.",
                parent=self.parent
            )

            return

        # ====================================================
        # FETCH CREDIT ACCOUNT
        # ====================================================

        cr_acc = _fetch_one(
            """
            SELECT *
            FROM gl_accounts
            WHERE code=?
            """,
            (
                cr_code,
            )
        )

        if not cr_acc:

            messagebox.showerror(
                "Error",
                f"Credit account '{cr_code}' not found.",
                parent=self.parent
            )

            return

        # ====================================================
        # SAME ACCOUNT
        # ====================================================

        if dr_code == cr_code:

            messagebox.showerror(
                "Error",
                "Debit and credit accounts cannot be the same.",
                parent=self.parent
            )

            return

        # ====================================================
        # USER ID
        # ====================================================

        user_id = None

        if isinstance(
            self.user,
            dict
        ):

            user_id = self.user.get(
                "id"
            )

        else:

            try:

                user_id = self.user["id"]

            except Exception:

                user_id = None

        # ====================================================
        # JV NUMBER
        # ====================================================

        jv_no = _next_jv_no()

        # ====================================================
        # ACCOUNT TYPES
        # ====================================================

        dr_type = str(
            dr_acc["type"]
        ).lower()

        cr_type = str(
            cr_acc["type"]
        ).lower()

        # ====================================================
        # DEBIT BALANCE SIGN
        # ====================================================

        if dr_type in (
            "asset",
            "expense"
        ):

            dr_sign = 1

        else:

            dr_sign = -1

        # ====================================================
        # CREDIT BALANCE SIGN
        # ====================================================

        if cr_type in (
            "liability",
            "equity",
            "income"
        ):

            cr_sign = 1

        else:

            cr_sign = -1

        # ====================================================
        # IMPORTANT
        #
        # A DOUBLE ENTRY JOURNAL HAS:
        #
        # total_debit  = amount
        # total_credit = amount
        #
        # This fixes:
        #
        # NOT NULL constraint failed:
        # journal_entries.total_debit
        # ====================================================

        total_debit = amount
        total_credit = amount

        # ====================================================
        # POST TRANSACTION
        # ====================================================

        try:

            _execute_atomic(
                [

                    # ----------------------------------------
                    # UPDATE DEBIT ACCOUNT
                    # ----------------------------------------

                    (
                        """
                        UPDATE gl_accounts
                        SET balance = balance + ?
                        WHERE code=?
                        """,
                        (
                            amount * dr_sign,
                            dr_code
                        )
                    ),

                    # ----------------------------------------
                    # UPDATE CREDIT ACCOUNT
                    # ----------------------------------------

                    (
                        """
                        UPDATE gl_accounts
                        SET balance = balance + ?
                        WHERE code=?
                        """,
                        (
                            amount * cr_sign,
                            cr_code
                        )
                    ),

                    # ----------------------------------------
                    # INSERT JOURNAL ENTRY
                    #
                    # total_debit and total_credit are
                    # explicitly included here.
                    # ----------------------------------------

                    (
                        """
                        INSERT INTO journal_entries
                        (
                            jv_no,
                            entry_date,
                            dr_account,
                            cr_account,
                            amount,
                            total_debit,
                            total_credit,
                            narration,
                            reference,
                            created_by
                        )
                        VALUES
                        (
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?
                        )
                        """,
                        (
                            jv_no,
                            date_s,
                            dr_code,
                            cr_code,
                            amount,
                            total_debit,
                            total_credit,
                            narration,
                            reference,
                            user_id
                        )
                    )

                ]
            )

        except Exception as e:

            messagebox.showerror(
                "Posting Error",
                "Unable to post journal entry.\n\n"
                f"{e}",
                parent=self.parent
            )

            return

        # ====================================================
        # SUCCESS
        # ====================================================

        messagebox.showinfo(
            "Posted Successfully",
            "Journal entry posted successfully.\n\n"
            f"JV No: {jv_no}\n"
            f"Debit: {dr_code}\n"
            f"Credit: {cr_code}\n"
            f"Amount: Rs {amount:,.2f}",
            parent=self.parent
        )

        # ====================================================
        # RESET
        # ====================================================

        self._reset_je()

        # ====================================================
        # REFRESH
        # ====================================================

        self._load_journal()
        self._load_accounts()
        self._load_trial()
        self._load_pl()

    # ========================================================
    # LOAD JOURNAL
    # ========================================================

    def _load_journal(self):

        if not hasattr(
            self,
            "je_tree"
        ):

            return

        try:

            self.je_tree.delete(
                *self.je_tree.get_children()
            )

            # ------------------------------------------------
            # USERS TABLE
            # ------------------------------------------------

            users_exists = _table_exists(
                "users"
            )

            if users_exists:

                user_columns = _get_columns(
                    "users"
                )

                if (
                    "full_name" in user_columns
                    and
                    "username" in user_columns
                ):

                    posted_by_sql = """
                        COALESCE(
                            u.full_name,
                            u.username,
                            '-'
                        )
                    """

                elif "username" in user_columns:

                    posted_by_sql = """
                        COALESCE(
                            u.username,
                            '-'
                        )
                    """

                elif "full_name" in user_columns:

                    posted_by_sql = """
                        COALESCE(
                            u.full_name,
                            '-'
                        )
                    """

                else:

                    posted_by_sql = "'-'"

                join_sql = """
                    LEFT JOIN users u
                        ON je.created_by = u.id
                """

            else:

                posted_by_sql = "'-'"
                join_sql = ""

            # ------------------------------------------------
            # QUERY
            # ------------------------------------------------

            sql = f"""
                SELECT
                    je.jv_no,
                    je.entry_date,
                    da.name AS dr_name,
                    ca.name AS cr_name,
                    je.amount,
                    je.narration,
                    je.reference,
                    {posted_by_sql} AS posted_by

                FROM journal_entries je

                LEFT JOIN gl_accounts da
                    ON je.dr_account = da.code

                LEFT JOIN gl_accounts ca
                    ON je.cr_account = ca.code

                {join_sql}

                ORDER BY je.id DESC

                LIMIT 500
            """

            rows = _fetch_all(
                sql
            )

            for index, row in enumerate(
                rows,
                1
            ):

                tag = (
                    "even"
                    if index % 2 == 0
                    else "odd"
                )

                amount = float(
                    row["amount"] or 0
                )

                self.je_tree.insert(
                    "",
                    "end",
                    values=(
                        row["jv_no"] or "-",
                        row["entry_date"] or "-",
                        row["dr_name"] or "-",
                        row["cr_name"] or "-",
                        f"Rs {amount:,.2f}",
                        row["narration"] or "-",
                        row["reference"] or "-",
                        row["posted_by"] or "-"
                    ),
                    tags=(tag,)
                )

            self.je_tree.tag_configure(
                "even",
                background=st.ALT_ROW
            )

            self.je_tree.tag_configure(
                "odd",
                background=st.BG_CARD
            )

        except Exception as e:

            messagebox.showerror(
                "Journal Error",
                "Unable to load journal entries.\n\n"
                f"{e}",
                parent=self.parent
            )

    # ========================================================
    # TRIAL BALANCE
    # ========================================================

    def _build_trial(self, parent):

        toolbar = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        toolbar.pack(
            fill="x",
            padx=8,
            pady=8
        )

        ttk.Button(
            toolbar,
            text="🔄  Refresh",
            style="Warning.TButton",
            command=self._load_trial
        ).pack(
            side="right"
        )

        tk.Label(
            parent,
            text="Trial Balance – Current Period",
            font=st.FONT_SUB,
            bg=st.BG_MAIN,
            fg=st.PRIMARY
        ).pack(
            anchor="w",
            padx=8,
            pady=(0, 4)
        )

        tf = tk.Frame(
            parent,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        tf.pack(
            fill="both",
            expand=True,
            padx=8
        )

        cols = (
            "Code",
            "Account Name",
            "Type",
            "Debit (Rs)",
            "Credit (Rs)"
        )

        self.trial_tree = ttk.Treeview(
            tf,
            columns=cols,
            show="headings"
        )

        vsb = ttk.Scrollbar(
            tf,
            orient="vertical",
            command=self.trial_tree.yview
        )

        self.trial_tree.configure(
            yscrollcommand=vsb.set
        )

        vsb.pack(
            side="right",
            fill="y"
        )

        self.trial_tree.pack(
            fill="both",
            expand=True
        )

        widths = [
            80,
            220,
            120,
            140,
            140
        ]

        for col, width in zip(
            cols,
            widths
        ):

            self.trial_tree.heading(
                col,
                text=col
            )

            self.trial_tree.column(
                col,
                width=width,
                anchor=(
                    "center"
                    if width <= 140
                    else "w"
                )
            )

        self._load_trial()

    # ========================================================
    # LOAD TRIAL BALANCE
    # ========================================================

    def _load_trial(self):

        if not hasattr(
            self,
            "trial_tree"
        ):

            return

        try:

            self.trial_tree.delete(
                *self.trial_tree.get_children()
            )

            rows = _fetch_all(
                """
                SELECT
                    code,
                    name,
                    type,
                    balance
                FROM gl_accounts
                ORDER BY code
                """
            )

            total_dr = 0.0
            total_cr = 0.0

            for index, row in enumerate(
                rows,
                1
            ):

                balance = float(
                    row["balance"] or 0
                )

                account_type = str(
                    row["type"]
                ).lower()

                if account_type in (
                    "asset",
                    "expense"
                ):

                    debit = max(
                        balance,
                        0
                    )

                    credit = max(
                        -balance,
                        0
                    )

                else:

                    credit = max(
                        balance,
                        0
                    )

                    debit = max(
                        -balance,
                        0
                    )

                total_dr += debit
                total_cr += credit

                tag = (
                    "even"
                    if index % 2 == 0
                    else "odd"
                )

                self.trial_tree.insert(
                    "",
                    "end",
                    values=(
                        row["code"],
                        row["name"],
                        str(
                            row["type"]
                        ).title(),
                        (
                            f"{debit:,.2f}"
                            if debit
                            else "-"
                        ),
                        (
                            f"{credit:,.2f}"
                            if credit
                            else "-"
                        )
                    ),
                    tags=(tag,)
                )

            self.trial_tree.tag_configure(
                "even",
                background=st.ALT_ROW
            )

            self.trial_tree.tag_configure(
                "odd",
                background=st.BG_CARD
            )

            # ------------------------------------------------
            # TOTAL
            # ------------------------------------------------

            self.trial_tree.insert(
                "",
                "end",
                values=(
                    "",
                    "TOTAL",
                    "",
                    f"{total_dr:,.2f}",
                    f"{total_cr:,.2f}"
                ),
                tags=("total",)
            )

            self.trial_tree.tag_configure(
                "total",
                background=st.PRIMARY,
                foreground=st.TEXT_LIGHT
            )

        except Exception as e:

            messagebox.showerror(
                "Trial Balance Error",
                "Unable to load trial balance.\n\n"
                f"{e}",
                parent=self.parent
            )

    # ========================================================
    # PROFIT & LOSS
    # ========================================================

    def _build_pl(self, parent):

        toolbar = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        toolbar.pack(
            fill="x",
            padx=8,
            pady=8
        )

        ttk.Button(
            toolbar,
            text="🔄  Refresh",
            style="Warning.TButton",
            command=self._load_pl
        ).pack(
            side="right"
        )

        tk.Label(
            parent,
            text="Profit & Loss Statement – Current Period",
            font=st.FONT_SUB,
            bg=st.BG_MAIN,
            fg=st.PRIMARY
        ).pack(
            anchor="w",
            padx=8,
            pady=(0, 4)
        )

        self.pl_frame = tk.Frame(
            parent,
            bg=st.BG_CARD
        )

        self.pl_frame.pack(
            fill="both",
            expand=True,
            padx=8
        )

        self._load_pl()

    # ========================================================
    # LOAD PROFIT & LOSS
    # ========================================================

    def _load_pl(self):

        if not hasattr(
            self,
            "pl_frame"
        ):

            return

        try:

            for widget in (
                self.pl_frame.winfo_children()
            ):

                widget.destroy()

            # ------------------------------------------------
            # INCOME
            # ------------------------------------------------

            income_rows = _fetch_all(
                """
                SELECT
                    code,
                    name,
                    balance
                FROM gl_accounts
                WHERE LOWER(type)='income'
                ORDER BY code
                """
            )

            # ------------------------------------------------
            # EXPENSE
            # ------------------------------------------------

            expense_rows = _fetch_all(
                """
                SELECT
                    code,
                    name,
                    balance
                FROM gl_accounts
                WHERE LOWER(type)='expense'
                ORDER BY code
                """
            )

            total_income = sum(
                float(
                    row["balance"] or 0
                )
                for row in income_rows
            )

            total_expense = sum(
                float(
                    row["balance"] or 0
                )
                for row in expense_rows
            )

            net = (
                total_income
                - total_expense
            )

            # ------------------------------------------------
            # SECTION
            # ------------------------------------------------

            def section(
                title,
                rows,
                total,
                section_color
            ):

                header = tk.Frame(
                    self.pl_frame,
                    bg=section_color
                )

                header.pack(
                    fill="x",
                    padx=16,
                    pady=(12, 0)
                )

                tk.Label(
                    header,
                    text=title,
                    font=st.FONT_SUB,
                    bg=section_color,
                    fg=st.TEXT_LIGHT,
                    padx=8,
                    pady=4
                ).pack(
                    side="left"
                )

                for row_data in rows:

                    row_frame = tk.Frame(
                        self.pl_frame,
                        bg=st.BG_CARD
                    )

                    row_frame.pack(
                        fill="x",
                        padx=16
                    )

                    tk.Label(
                        row_frame,
                        text=row_data["name"],
                        font=st.FONT_NORMAL,
                        bg=st.BG_CARD,
                        fg=st.TEXT_DARK,
                        width=30,
                        anchor="w"
                    ).pack(
                        side="left",
                        padx=16,
                        pady=5
                    )

                    value = float(
                        row_data["balance"] or 0
                    )

                    tk.Label(
                        row_frame,
                        text=f"Rs {value:,.2f}",
                        font=st.FONT_NORMAL,
                        bg=st.BG_CARD,
                        fg=st.TEXT_DARK
                    ).pack(
                        side="right",
                        padx=16
                    )

                total_row = tk.Frame(
                    self.pl_frame,
                    bg=st.ALT_ROW
                )

                total_row.pack(
                    fill="x",
                    padx=16
                )

                tk.Label(
                    total_row,
                    text=f"Total {title}",
                    font=st.FONT_SUB,
                    bg=st.ALT_ROW,
                    fg=st.TEXT_DARK,
                    width=30,
                    anchor="w"
                ).pack(
                    side="left",
                    padx=16,
                    pady=6
                )

                tk.Label(
                    total_row,
                    text=f"Rs {total:,.2f}",
                    font=st.FONT_SUB,
                    bg=st.ALT_ROW,
                    fg=section_color
                ).pack(
                    side="right",
                    padx=16
                )

            # ------------------------------------------------
            # INCOME
            # ------------------------------------------------

            section(
                "Income",
                income_rows,
                total_income,
                st.SUCCESS
            )

            # ------------------------------------------------
            # EXPENSES
            # ------------------------------------------------

            section(
                "Expenses",
                expense_rows,
                total_expense,
                st.DANGER
            )

            tk.Frame(
                self.pl_frame,
                bg=st.BORDER,
                height=2
            ).pack(
                fill="x",
                padx=16,
                pady=12
            )

            # ------------------------------------------------
            # NET
            # ------------------------------------------------

            net_color = (
                st.SUCCESS
                if net >= 0
                else st.DANGER
            )

            net_label = (
                "Net Profit"
                if net >= 0
                else "Net Loss"
            )

            net_frame = tk.Frame(
                self.pl_frame,
                bg=net_color
            )

            net_frame.pack(
                fill="x",
                padx=16,
                pady=(0, 16)
            )

            tk.Label(
                net_frame,
                text=net_label,
                font=st.FONT_HEADING,
                bg=net_color,
                fg=st.TEXT_LIGHT,
                padx=12,
                pady=8
            ).pack(
                side="left"
            )

            tk.Label(
                net_frame,
                text=f"Rs {abs(net):,.2f}",
                font=st.FONT_HEADING,
                bg=net_color,
                fg=st.TEXT_LIGHT,
                padx=12,
                pady=8
            ).pack(
                side="right"
            )

        except Exception as e:

            messagebox.showerror(
                "Profit & Loss Error",
                "Unable to load Profit & Loss.\n\n"
                f"{e}",
                parent=self.parent
            )


# ============================================================
# GL ACCOUNT DIALOG
# ============================================================

class GLAccountDialog(tk.Toplevel):

    def __init__(
        self,
        parent,
        row=None,
        callback=None
    ):

        super().__init__(
            parent
        )

        self.row = row
        self.callback = callback

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = (
            "Add GL Account"
            if row is None
            else "Edit GL Account"
        )

        self.title(
            title
        )

        self.resizable(
            False,
            False
        )

        self.configure(
            bg=st.BG_MAIN
        )

        self.transient(
            parent.winfo_toplevel()
        )

        self.grab_set()

        self._center(
            450,
            430
        )

        self._build()

    # ========================================================
    # CENTER
    # ========================================================

    def _center(
        self,
        width,
        height
    ):

        self.update_idletasks()

        screen_width = (
            self.winfo_screenwidth()
        )

        screen_height = (
            self.winfo_screenheight()
        )

        x = (
            screen_width - width
        ) // 2

        y = (
            screen_height - height
        ) // 2

        self.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # ========================================================
    # BUILD
    # ========================================================

    def _build(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = tk.Frame(
            self,
            bg=st.PRIMARY,
            height=52
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        tk.Label(
            header,
            text=self.title(),
            font=st.FONT_HEADING,
            bg=st.PRIMARY,
            fg=st.TEXT_LIGHT
        ).pack(
            side="left",
            padx=14,
            pady=8
        )

        # ----------------------------------------------------
        # CARD
        # ----------------------------------------------------

        card = tk.Frame(
            self,
            bg=st.BG_CARD
        )

        card.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=10
        )

        self.v = {}

        fields = [
            (
                "Account Code *",
                "code",
                "entry"
            ),
            (
                "Account Name *",
                "name",
                "entry"
            ),
            (
                "Type *",
                "type",
                "combo"
            ),
            (
                "Opening Balance",
                "balance",
                "entry"
            ),
            (
                "Description",
                "description",
                "entry"
            )
        ]

        for (
            label,
            key,
            widget_type
        ) in fields:

            frame = tk.Frame(
                card,
                bg=st.BG_CARD
            )

            frame.pack(
                fill="x",
                pady=5,
                padx=10
            )

            tk.Label(
                frame,
                text=label,
                font=st.FONT_SMALL,
                bg=st.BG_CARD,
                fg=st.TEXT_MUTED
            ).pack(
                anchor="w"
            )

            self.v[key] = tk.StringVar()

            if widget_type == "combo":

                widget = ttk.Combobox(
                    frame,
                    textvariable=self.v[key],
                    values=[
                        "asset",
                        "liability",
                        "equity",
                        "income",
                        "expense"
                    ],
                    state="readonly",
                    font=st.FONT_NORMAL
                )

                widget.set(
                    "asset"
                )

            else:

                widget = ttk.Entry(
                    frame,
                    textvariable=self.v[key],
                    font=st.FONT_NORMAL
                )

            widget.pack(
                fill="x",
                ipady=3
            )

        # ----------------------------------------------------
        # LOAD EXISTING
        # ----------------------------------------------------

        if self.row is not None:

            for key in self.v:

                try:

                    value = self.row[key]

                except Exception:

                    value = ""

                if value is None:

                    value = ""

                self.v[key].set(
                    str(value)
                )

        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        button_frame = tk.Frame(
            self,
            bg=st.BG_MAIN
        )

        button_frame.pack(
            fill="x",
            padx=14,
            pady=(0, 12)
        )

        # ----------------------------------------------------
        # SUBMIT
        # ----------------------------------------------------

        ttk.Button(
            button_frame,
            text="✅  Submit",
            style="Success.TButton",
            command=self._save
        ).pack(
            side="left",
            padx=(0, 8)
        )

        # ----------------------------------------------------
        # CANCEL
        # ----------------------------------------------------

        ttk.Button(
            button_frame,
            text="❌  Cancel",
            style="Danger.TButton",
            command=self.destroy
        ).pack(
            side="left"
        )

    # ========================================================
    # SAVE ACCOUNT
    # ========================================================

    def _save(self):

        code = (
            self.v["code"]
            .get()
            .strip()
            .upper()
        )

        name = (
            self.v["name"]
            .get()
            .strip()
        )

        account_type = (
            self.v["type"]
            .get()
            .strip()
            .lower()
        )

        balance_text = (
            self.v["balance"]
            .get()
            .strip()
        )

        description = (
            self.v["description"]
            .get()
            .strip()
        )

        # ----------------------------------------------------
        # REQUIRED
        # ----------------------------------------------------

        if not code:

            messagebox.showerror(
                "Error",
                "Account code is required.",
                parent=self
            )

            return

        if not name:

            messagebox.showerror(
                "Error",
                "Account name is required.",
                parent=self
            )

            return

        valid_types = (
            "asset",
            "liability",
            "equity",
            "income",
            "expense"
        )

        if account_type not in valid_types:

            messagebox.showerror(
                "Error",
                "Please select a valid account type.",
                parent=self
            )

            return

        # ----------------------------------------------------
        # BALANCE
        # ----------------------------------------------------

        if not balance_text:

            balance = 0.0

        else:

            try:

                balance = float(
                    balance_text.replace(
                        ",",
                        ""
                    )
                )

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Invalid opening balance.",
                    parent=self
                )

                return

        # ----------------------------------------------------
        # EDIT
        # ----------------------------------------------------

        if self.row is not None:

            old_code = self.row["code"]

            try:

                _execute(
                    """
                    UPDATE gl_accounts
                    SET
                        name=?,
                        type=?,
                        balance=?,
                        description=?
                    WHERE code=?
                    """,
                    (
                        name,
                        account_type,
                        balance,
                        description,
                        old_code
                    )
                )

            except Exception as e:

                messagebox.showerror(
                    "Error",
                    "Unable to update account.\n\n"
                    f"{e}",
                    parent=self
                )

                return

        # ----------------------------------------------------
        # ADD
        # ----------------------------------------------------

        else:

            existing = _fetch_one(
                """
                SELECT id
                FROM gl_accounts
                WHERE code=?
                """,
                (
                    code,
                )
            )

            if existing:

                messagebox.showerror(
                    "Duplicate Account",
                    f"Account code '{code}' already exists.",
                    parent=self
                )

                return

            try:

                _execute(
                    """
                    INSERT INTO gl_accounts
                    (
                        code,
                        name,
                        type,
                        balance,
                        description
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        code,
                        name,
                        account_type,
                        balance,
                        description
                    )
                )

            except Exception as e:

                messagebox.showerror(
                    "Error",
                    "Unable to save account.\n\n"
                    f"{e}",
                    parent=self
                )

                return

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        messagebox.showinfo(
            "Saved",
            "Account saved successfully.",
            parent=self
        )

        if self.callback:

            self.callback()

        self.destroy()


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    _ensure_accounting_tables()

    print(
        "Accounting module is ready."
    )