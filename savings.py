
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db
import styles as st


# ============================================================
# SAFE STYLE HELPERS
# Works with your existing styles.py
# ============================================================

def style_value(name, default):
    return getattr(st, name, default)


BG_MAIN = style_value("BG_MAIN", "#F5F7FA")
BG_CARD = style_value("BG_CARD", "#FFFFFF")
PRIMARY = style_value("PRIMARY", "#2563EB")
TEXT_DARK = style_value("TEXT_DARK", "#1F2937")
TEXT_LIGHT = style_value("TEXT_LIGHT", "#FFFFFF")
TEXT_MUTED = style_value("TEXT_MUTED", "#6B7280")
DANGER = style_value("DANGER", "#DC2626")
SUCCESS = style_value("SUCCESS", "#16A34A")
BORDER = style_value("BORDER", "#D1D5DB")

FONT_NORMAL = style_value("FONT_NORMAL", ("Segoe UI", 10))
FONT_SMALL = style_value("FONT_SMALL", ("Segoe UI", 9))
FONT_SUB = style_value("FONT_SUB", ("Segoe UI", 10))
FONT_HEADING = style_value("FONT_HEADING", ("Segoe UI", 16, "bold"))


# ============================================================
# PUBLIC ENTRY POINT
# main.py expects create_frame(parent, user=None)
# ============================================================

def create_frame(parent, user=None):
    return SavingsPage(parent, user)


# ============================================================
# MAIN SAVINGS PAGE
# ============================================================

class SavingsPage(tk.Frame):

    def __init__(self, parent, user=None):
        super().__init__(parent, bg=BG_MAIN)

        self.user = user or {}
        self._build_ui()

        self.load_accounts()
        self.load_history()

    # --------------------------------------------------------
    # USER ID
    # --------------------------------------------------------

    def get_user_id(self):
        if isinstance(self.user, dict):
            return self.user.get("id")

        try:
            return self.user["id"]
        except Exception:
            return None

    # --------------------------------------------------------
    # MAIN UI
    # --------------------------------------------------------

    def _build_ui(self):

        header = tk.Frame(self, bg=BG_MAIN)
        header.pack(fill="x", padx=20, pady=(18, 10))

        tk.Label(
            header,
            text="Savings Management",
            font=FONT_HEADING,
            bg=BG_MAIN,
            fg=TEXT_DARK
        ).pack(side="left")

        tk.Button(
            header,
            text="↻ Refresh",
            command=self.refresh_all,
            bg=PRIMARY,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=15,
            pady=7,
            cursor="hand2"
        ).pack(side="right")

        # ----------------------------------------------------
        # Notebook
        # ----------------------------------------------------

        notebook_frame = tk.Frame(
            self,
            bg=BG_CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        notebook_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.accounts_tab = tk.Frame(
            self.notebook,
            bg=BG_CARD
        )

        self.transaction_tab = tk.Frame(
            self.notebook,
            bg=BG_CARD
        )

        self.history_tab = tk.Frame(
            self.notebook,
            bg=BG_CARD
        )

        self.interest_tab = tk.Frame(
            self.notebook,
            bg=BG_CARD
        )

        self.notebook.add(
            self.accounts_tab,
            text="  Accounts  "
        )

        self.notebook.add(
            self.transaction_tab,
            text="  Deposit / Withdraw  "
        )

        self.notebook.add(
            self.history_tab,
            text="  Transaction History  "
        )

        self.notebook.add(
            self.interest_tab,
            text="  Interest Calculator  "
        )

        self._build_accounts_tab()
        self._build_transaction_tab()
        self._build_history_tab()
        self._build_interest_tab()

    # ========================================================
    # ACCOUNTS TAB
    # ========================================================

    def _build_accounts_tab(self):

        top = tk.Frame(
            self.accounts_tab,
            bg=BG_CARD
        )
        top.pack(fill="x", padx=15, pady=15)

        tk.Label(
            top,
            text="Savings Accounts",
            font=("Segoe UI", 13, "bold"),
            bg=BG_CARD,
            fg=TEXT_DARK
        ).pack(side="left")

        tk.Button(
            top,
            text="+ Open New Account",
            command=self.open_account,
            bg=SUCCESS,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=15,
            pady=7,
            cursor="hand2"
        ).pack(side="right")

        # Search

        search_frame = tk.Frame(
            self.accounts_tab,
            bg=BG_CARD
        )
        search_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            search_frame,
            text="Search:",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=FONT_NORMAL
        ).pack(side="left")

        self.account_search = tk.StringVar()

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.account_search,
            width=40
        )
        search_entry.pack(side="left", padx=8)

        search_entry.bind(
            "<KeyRelease>",
            lambda event: self.load_accounts()
        )

        tk.Button(
            search_frame,
            text="Clear",
            command=lambda: (
                self.account_search.set(""),
                self.load_accounts()
            ),
            relief="flat",
            padx=10
        ).pack(side="left")

        # Table

        table_frame = tk.Frame(
            self.accounts_tab,
            bg=BG_CARD
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        columns = (
            "id",
            "account_no",
            "member_no",
            "full_name",
            "account_type",
            "balance",
            "interest_rate",
            "opened_date",
            "status"
        )

        self.account_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "account_no": "Account No.",
            "member_no": "Member No.",
            "full_name": "Member Name",
            "account_type": "Type",
            "balance": "Balance",
            "interest_rate": "Interest %",
            "opened_date": "Opened Date",
            "status": "Status"
        }

        widths = {
            "id": 50,
            "account_no": 110,
            "member_no": 100,
            "full_name": 180,
            "account_type": 120,
            "balance": 120,
            "interest_rate": 90,
            "opened_date": 110,
            "status": 90
        }

        for col in columns:
            self.account_tree.heading(
                col,
                text=headings[col]
            )

            self.account_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.account_tree.yview
        )

        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.account_tree.xview
        )

        self.account_tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.account_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        self.account_tree.bind(
            "<Double-1>",
            lambda event: self.account_details()
        )

        bottom = tk.Frame(
            self.accounts_tab,
            bg=BG_CARD
        )
        bottom.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        tk.Button(
            bottom,
            text="View Details",
            command=self.account_details,
            relief="flat",
            padx=12,
            pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            bottom,
            text="Close Account",
            command=self.close_account,
            bg=DANGER,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=12,
            pady=6
        ).pack(side="left")

    # ========================================================
    # LOAD ACCOUNTS
    # ========================================================

    def load_accounts(self):

        if not hasattr(self, "account_tree"):
            return

        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        search = self.account_search.get().strip()

        try:

            if search:

                rows = db.fetch_all(
                    """
                    SELECT
                        sa.id,
                        sa.account_no,
                        m.member_no,
                        m.full_name,
                        sa.account_type,
                        sa.balance,
                        sa.interest_rate,
                        sa.opened_date,
                        sa.status
                    FROM savings_accounts sa
                    JOIN members m
                        ON sa.member_id = m.id
                    WHERE
                        m.full_name LIKE ?
                        OR sa.account_no LIKE ?
                        OR m.member_no LIKE ?
                    ORDER BY sa.id DESC
                    """,
                    (
                        f"%{search}%",
                        f"%{search}%",
                        f"%{search}%"
                    )
                )

            else:

                rows = db.fetch_all(
                    """
                    SELECT
                        sa.id,
                        sa.account_no,
                        m.member_no,
                        m.full_name,
                        sa.account_type,
                        sa.balance,
                        sa.interest_rate,
                        sa.opened_date,
                        sa.status
                    FROM savings_accounts sa
                    JOIN members m
                        ON sa.member_id = m.id
                    ORDER BY sa.id DESC
                    """
                )

            for row in rows:

                balance = float(row.get("balance") or 0)

                self.account_tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("id"),
                        row.get("account_no"),
                        row.get("member_no"),
                        row.get("full_name"),
                        row.get("account_type"),
                        f"Rs {balance:,.2f}",
                        f"{float(row.get('interest_rate') or 0):.2f}%",
                        row.get("opened_date"),
                        row.get("status")
                    )
                )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to load savings accounts.\n\n{e}",
                parent=self
            )

    # ========================================================
    # TRANSACTION TAB
    # ========================================================

    def _build_transaction_tab(self):

        container = tk.Frame(
            self.transaction_tab,
            bg=BG_CARD
        )
        container.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=25
        )

        tk.Label(
            container,
            text="Deposit / Withdraw",
            font=("Segoe UI", 15, "bold"),
            bg=BG_CARD,
            fg=TEXT_DARK
        ).pack(anchor="w", pady=(0, 20))

        form = tk.Frame(
            container,
            bg=BG_CARD
        )
        form.pack(anchor="w")

        self.tx_account = tk.StringVar()
        self.tx_type = tk.StringVar(value="Deposit")
        self.tx_amount = tk.StringVar()
        self.tx_date = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )
        self.tx_narration = tk.StringVar()

        # Account number

        tk.Label(
            form,
            text="Account No.",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=FONT_NORMAL
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        self.account_combo = ttk.Combobox(
            form,
            textvariable=self.tx_account,
            width=30,
            state="normal"
        )

        self.account_combo.grid(
            row=0,
            column=1,
            padx=10,
            pady=8
        )

        self.load_account_numbers()

        tk.Button(
            form,
            text="Check",
            command=self.check_account,
            bg=PRIMARY,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=10
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        # Member information

        self.tx_member_label = tk.Label(
            form,
            text="Member: -",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        )

        self.tx_member_label.grid(
            row=1,
            column=1,
            sticky="w",
            padx=10,
            pady=3
        )

        self.tx_balance_label = tk.Label(
            form,
            text="Current Balance: Rs 0.00",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        )

        self.tx_balance_label.grid(
            row=2,
            column=1,
            sticky="w",
            padx=10,
            pady=3
        )

        # Type

        tk.Label(
            form,
            text="Transaction Type",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=FONT_NORMAL
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        ttk.Combobox(
            form,
            textvariable=self.tx_type,
            values=("Deposit", "Withdraw"),
            state="readonly",
            width=28
        ).grid(
            row=3,
            column=1,
            sticky="w",
            padx=10,
            pady=8
        )

        # Amount

        tk.Label(
            form,
            text="Amount (Rs)",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=FONT_NORMAL
        ).grid(
            row=4,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        ttk.Entry(
            form,
            textvariable=self.tx_amount,
            width=31
        ).grid(
            row=4,
            column=1,
            padx=10,
            pady=8
        )

        # Date

        tk.Label(
            form,
            text="Date",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=FONT_NORMAL
        ).grid(
            row=5,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        ttk.Entry(
            form,
            textvariable=self.tx_date,
            width=31
        ).grid(
            row=5,
            column=1,
            padx=10,
            pady=8
        )

        # Narration

        tk.Label(
            form,
            text="Narration",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=FONT_NORMAL
        ).grid(
            row=6,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        ttk.Entry(
            form,
            textvariable=self.tx_narration,
            width=50
        ).grid(
            row=6,
            column=1,
            columnspan=2,
            sticky="w",
            padx=10,
            pady=8
        )

        # Submit

        tk.Button(
            form,
            text="Process Transaction",
            command=self.process_transaction,
            bg=SUCCESS,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).grid(
            row=7,
            column=1,
            sticky="w",
            padx=10,
            pady=20
        )

        tk.Button(
            form,
            text="Clear",
            command=self.clear_transaction_form,
            relief="flat",
            padx=20,
            pady=10
        ).grid(
            row=7,
            column=2,
            sticky="w",
            padx=5,
            pady=20
        )

    # ========================================================
    # LOAD ACCOUNT NUMBERS
    # ========================================================

    def load_account_numbers(self):

        try:

            rows = db.fetch_all(
                """
                SELECT account_no
                FROM savings_accounts
                WHERE status='active'
                ORDER BY account_no
                """
            )

            self.account_combo["values"] = [
                row["account_no"]
                for row in rows
            ]

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to load account numbers.\n\n{e}",
                parent=self
            )

    # ========================================================
    # CHECK ACCOUNT
    # ========================================================

    def check_account(self):

        account_no = self.tx_account.get().strip()

        if not account_no:
            messagebox.showwarning(
                "Account Required",
                "Please enter or select an account number.",
                parent=self
            )
            return

        try:

            row = db.fetch_one(
                """
                SELECT
                    sa.id,
                    sa.account_no,
                    sa.balance,
                    sa.status,
                    m.member_no,
                    m.full_name
                FROM savings_accounts sa
                JOIN members m
                    ON sa.member_id = m.id
                WHERE sa.account_no=?
                """,
                (account_no,)
            )

            if not row:

                self.tx_member_label.config(
                    text="Member: -"
                )

                self.tx_balance_label.config(
                    text="Current Balance: Rs 0.00"
                )

                messagebox.showerror(
                    "Not Found",
                    "Savings account was not found.",
                    parent=self
                )
                return

            self.tx_member_label.config(
                text=(
                    f"Member: {row['member_no']} - "
                    f"{row['full_name']}"
                ),
                fg=TEXT_DARK
            )

            self.tx_balance_label.config(
                text=(
                    f"Current Balance: "
                    f"Rs {float(row['balance'] or 0):,.2f}"
                ),
                fg=TEXT_DARK
            )

            if row["status"] != "active":

                messagebox.showwarning(
                    "Inactive Account",
                    "This savings account is not active.",
                    parent=self
                )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to check account.\n\n{e}",
                parent=self
            )

    # ========================================================
    # PROCESS DEPOSIT / WITHDRAW
    # ========================================================

    def process_transaction(self):

        account_no = self.tx_account.get().strip()
        tx_type = self.tx_type.get().strip()
        amount_text = self.tx_amount.get().strip()
        tx_date = self.tx_date.get().strip()
        narration = self.tx_narration.get().strip()

        if not account_no:
            messagebox.showwarning(
                "Required",
                "Please enter an account number.",
                parent=self
            )
            return

        if tx_type not in ("Deposit", "Withdraw"):
            messagebox.showwarning(
                "Invalid Type",
                "Please select Deposit or Withdraw.",
                parent=self
            )
            return

        try:
            amount = float(amount_text)
        except ValueError:

            messagebox.showerror(
                "Invalid Amount",
                "Please enter a valid numeric amount.",
                parent=self
            )
            return

        if amount <= 0:

            messagebox.showerror(
                "Invalid Amount",
                "Amount must be greater than zero.",
                parent=self
            )
            return

        try:

            datetime.strptime(
                tx_date,
                "%Y-%m-%d"
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Date",
                "Date must be in YYYY-MM-DD format.",
                parent=self
            )
            return

        try:

            account = db.fetch_one(
                """
                SELECT
                    sa.id,
                    sa.account_no,
                    sa.balance,
                    sa.status,
                    m.full_name,
                    m.member_no
                FROM savings_accounts sa
                JOIN members m
                    ON sa.member_id=m.id
                WHERE sa.account_no=?
                """,
                (account_no,)
            )

            if not account:

                messagebox.showerror(
                    "Not Found",
                    "Savings account does not exist.",
                    parent=self
                )
                return

            if account["status"] != "active":

                messagebox.showerror(
                    "Inactive Account",
                    "This savings account is inactive.",
                    parent=self
                )
                return

            current_balance = float(
                account["balance"] or 0
            )

            # ------------------------------------------------
            # WITHDRAWAL BALANCE CHECK
            # ------------------------------------------------

            if tx_type == "Withdraw":

                if amount > current_balance + 0.005:

                    messagebox.showerror(
                        "Insufficient Balance",
                        (
                            "Insufficient balance.\n\n"
                            f"Available Balance: "
                            f"Rs {current_balance:,.2f}\n"
                            f"Requested Amount: "
                            f"Rs {amount:,.2f}\n\n"
                            f"Shortage: "
                            f"Rs {amount - current_balance:,.2f}"
                        ),
                        parent=self
                    )

                    return

                new_balance = current_balance - amount

            else:

                new_balance = current_balance + amount

            new_balance = round(
                new_balance,
                2
            )

            voucher_no = db.next_voucher_no("V")

            if not narration:

                narration = (
                    "Savings deposit"
                    if tx_type == "Deposit"
                    else "Savings withdrawal"
                )

            user_id = self.get_user_id()

            # ------------------------------------------------
            # ATOMIC DATABASE TRANSACTION
            # ------------------------------------------------

            db.execute_atomic(
                [
                    (
                        """
                        UPDATE savings_accounts
                        SET balance=?
                        WHERE id=?
                        """,
                        (
                            new_balance,
                            account["id"]
                        )
                    ),
                    (
                        """
                        INSERT INTO savings_transactions
                        (
                            account_id,
                            transaction_type,
                            amount,
                            balance_after,
                            transaction_date,
                            narration,
                            voucher_no,
                            created_by
                        )
                        VALUES (?,?,?,?,?,?,?,?)
                        """,
                        (
                            account["id"],
                            tx_type,
                            amount,
                            new_balance,
                            tx_date,
                            narration,
                            voucher_no,
                            user_id
                        )
                    )
                ]
            )

            messagebox.showinfo(
                "Transaction Successful",
                (
                    f"{tx_type} successful.\n\n"
                    f"Account: {account_no}\n"
                    f"Member: {account['full_name']}\n"
                    f"Amount: Rs {amount:,.2f}\n"
                    f"Voucher No.: {voucher_no}\n"
                    f"New Balance: Rs {new_balance:,.2f}"
                ),
                parent=self
            )

            self.clear_transaction_form()
            self.load_accounts()
            self.load_history()
            self.load_account_numbers()

        except Exception as e:

            messagebox.showerror(
                "Transaction Error",
                f"Unable to process transaction.\n\n{e}",
                parent=self
            )

    # ========================================================
    # CLEAR TRANSACTION FORM
    # ========================================================

    def clear_transaction_form(self):

        self.tx_account.set("")
        self.tx_type.set("Deposit")
        self.tx_amount.set("")
        self.tx_date.set(
            datetime.now().strftime("%Y-%m-%d")
        )
        self.tx_narration.set("")

        self.tx_member_label.config(
            text="Member: -",
            fg=TEXT_MUTED
        )

        self.tx_balance_label.config(
            text="Current Balance: Rs 0.00",
            fg=TEXT_MUTED
        )

    # ========================================================
    # TRANSACTION HISTORY TAB
    # ========================================================

    def _build_history_tab(self):

        top = tk.Frame(
            self.history_tab,
            bg=BG_CARD
        )
        top.pack(
            fill="x",
            padx=15,
            pady=15
        )

        tk.Label(
            top,
            text="Transaction History",
            font=("Segoe UI", 13, "bold"),
            bg=BG_CARD,
            fg=TEXT_DARK
        ).pack(side="left")

        tk.Button(
            top,
            text="Refresh",
            command=self.load_history,
            bg=PRIMARY,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=15,
            pady=7
        ).pack(side="right")

        search_frame = tk.Frame(
            self.history_tab,
            bg=BG_CARD
        )
        search_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            search_frame,
            text="Search:",
            bg=BG_CARD,
            fg=TEXT_DARK
        ).pack(side="left")

        self.history_search = tk.StringVar()

        history_entry = ttk.Entry(
            search_frame,
            textvariable=self.history_search,
            width=40
        )

        history_entry.pack(
            side="left",
            padx=8
        )

        history_entry.bind(
            "<KeyRelease>",
            lambda event: self.load_history()
        )

        tk.Button(
            search_frame,
            text="Clear",
            command=lambda: (
                self.history_search.set(""),
                self.load_history()
            ),
            relief="flat",
            padx=10
        ).pack(side="left")

        table_frame = tk.Frame(
            self.history_tab,
            bg=BG_CARD
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        columns = (
            "id",
            "voucher",
            "date",
            "account",
            "member_no",
            "member",
            "type",
            "amount",
            "balance",
            "narration"
        )

        self.history_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "voucher": "Voucher",
            "date": "Date",
            "account": "Account No.",
            "member_no": "Member No.",
            "member": "Member",
            "type": "Type",
            "amount": "Amount",
            "balance": "Balance After",
            "narration": "Narration"
        }

        widths = {
            "id": 50,
            "voucher": 100,
            "date": 100,
            "account": 110,
            "member_no": 100,
            "member": 170,
            "type": 100,
            "amount": 110,
            "balance": 120,
            "narration": 200
        }

        for col in columns:

            self.history_tree.heading(
                col,
                text=headings[col]
            )

            self.history_tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.history_tree.yview
        )

        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.history_tree.xview
        )

        self.history_tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.history_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

    # ========================================================
    # LOAD TRANSACTION HISTORY
    #
    # IMPORTANT:
    # Uses db.fetch_all(), NOT db.query()
    # ========================================================

    def load_history(self):

        if not hasattr(self, "history_tree"):
            return

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        search = ""

        if hasattr(self, "history_search"):
            search = self.history_search.get().strip()

        try:

            if search:

                rows = db.fetch_all(
                    """
                    SELECT
                        st.id,
                        st.voucher_no,
                        st.transaction_date,
                        sa.account_no,
                        m.member_no,
                        m.full_name,
                        st.transaction_type,
                        st.amount,
                        st.balance_after,
                        st.narration
                    FROM savings_transactions st
                    JOIN savings_accounts sa
                        ON st.account_id=sa.id
                    JOIN members m
                        ON sa.member_id=m.id
                    WHERE
                        st.voucher_no LIKE ?
                        OR sa.account_no LIKE ?
                        OR m.member_no LIKE ?
                        OR m.full_name LIKE ?
                        OR st.transaction_type LIKE ?
                        OR st.narration LIKE ?
                    ORDER BY
                        st.id DESC
                    LIMIT 500
                    """,
                    (
                        f"%{search}%",
                        f"%{search}%",
                        f"%{search}%",
                        f"%{search}%",
                        f"%{search}%",
                        f"%{search}%"
                    )
                )

            else:

                rows = db.fetch_all(
                    """
                    SELECT
                        st.id,
                        st.voucher_no,
                        st.transaction_date,
                        sa.account_no,
                        m.member_no,
                        m.full_name,
                        st.transaction_type,
                        st.amount,
                        st.balance_after,
                        st.narration
                    FROM savings_transactions st
                    JOIN savings_accounts sa
                        ON st.account_id=sa.id
                    JOIN members m
                        ON sa.member_id=m.id
                    ORDER BY
                        st.id DESC
                    LIMIT 500
                    """
                )

            for row in rows:

                amount = float(
                    row.get("amount") or 0
                )

                balance = float(
                    row.get("balance_after") or 0
                )

                tx_type = row.get(
                    "transaction_type",
                    ""
                )

                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("id"),
                        row.get("voucher_no") or "-",
                        row.get("transaction_date"),
                        row.get("account_no"),
                        row.get("member_no"),
                        row.get("full_name"),
                        tx_type,
                        f"Rs {amount:,.2f}",
                        f"Rs {balance:,.2f}",
                        row.get("narration") or ""
                    )
                )

        except Exception as e:

            messagebox.showerror(
                "Transaction History Error",
                (
                    "Unable to load transaction history.\n\n"
                    f"{e}"
                ),
                parent=self
            )

    # ========================================================
    # INTEREST CALCULATOR
    # ========================================================

    def _build_interest_tab(self):

        container = tk.Frame(
            self.interest_tab,
            bg=BG_CARD
        )
        container.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=30
        )

        tk.Label(
            container,
            text="Savings Interest Calculator",
            font=("Segoe UI", 15, "bold"),
            bg=BG_CARD,
            fg=TEXT_DARK
        ).pack(anchor="w", pady=(0, 25))

        form = tk.Frame(
            container,
            bg=BG_CARD
        )
        form.pack(anchor="w")

        self.calc_principal = tk.StringVar()
        self.calc_rate = tk.StringVar(value="6")
        self.calc_months = tk.StringVar(value="12")

        fields = [
            ("Principal Amount (Rs)", self.calc_principal),
            ("Annual Interest Rate (%)", self.calc_rate),
            ("Period (Months)", self.calc_months)
        ]

        for i, (label, variable) in enumerate(fields):

            tk.Label(
                form,
                text=label,
                bg=BG_CARD,
                fg=TEXT_DARK,
                font=FONT_NORMAL
            ).grid(
                row=i,
                column=0,
                sticky="w",
                padx=5,
                pady=10
            )

            ttk.Entry(
                form,
                textvariable=variable,
                width=32
            ).grid(
                row=i,
                column=1,
                padx=15,
                pady=10
            )

        tk.Button(
            form,
            text="Calculate Interest",
            command=self.calculate_interest,
            bg=PRIMARY,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=20,
            pady=9
        ).grid(
            row=3,
            column=1,
            sticky="w",
            padx=15,
            pady=20
        )

        self.interest_result = tk.Label(
            container,
            text="",
            justify="left",
            anchor="w",
            bg=BG_CARD,
            fg=TEXT_DARK,
            font=("Segoe UI", 11)
        )

        self.interest_result.pack(
            anchor="w",
            pady=20
        )

    # ========================================================
    # CALCULATE INTEREST
    # ========================================================

    def calculate_interest(self):

        try:

            principal = float(
                self.calc_principal.get()
            )

            rate = float(
                self.calc_rate.get()
            )

            months = int(
                self.calc_months.get()
            )

            if principal < 0:
                raise ValueError(
                    "Principal cannot be negative."
                )

            if rate < 0:
                raise ValueError(
                    "Interest rate cannot be negative."
                )

            if months <= 0:
                raise ValueError(
                    "Months must be greater than zero."
                )

            # Simple interest

            interest = (
                principal
                * rate
                / 100
                * months
                / 12
            )

            total = principal + interest

            monthly_interest = (
                principal
                * rate
                / 100
                / 12
            )

            yearly_interest = (
                principal
                * rate
                / 100
            )

            self.interest_result.config(
                text=(
                    "INTEREST CALCULATION\n\n"
                    f"Principal: "
                    f"Rs {principal:,.2f}\n"
                    f"Annual Rate: "
                    f"{rate:.2f}%\n"
                    f"Period: "
                    f"{months} months\n\n"
                    f"Monthly Interest: "
                    f"Rs {monthly_interest:,.2f}\n"
                    f"Interest for Period: "
                    f"Rs {interest:,.2f}\n"
                    f"One-Year Interest: "
                    f"Rs {yearly_interest:,.2f}\n"
                    f"Total Amount: "
                    f"Rs {total:,.2f}"
                )
            )

        except ValueError as e:

            messagebox.showerror(
                "Invalid Input",
                str(e),
                parent=self
            )

    # ========================================================
    # OPEN NEW ACCOUNT
    # ========================================================

    def open_account(self):

        OpenAccountDialog(
            self,
            self.user,
            on_saved=self.refresh_all
        )

    # ========================================================
    # ACCOUNT DETAILS
    # ========================================================

    def get_selected_account_id(self):

        selection = self.account_tree.selection()

        if not selection:

            messagebox.showwarning(
                "Select Account",
                "Please select a savings account first.",
                parent=self
            )

            return None

        values = self.account_tree.item(
            selection[0],
            "values"
        )

        if not values:
            return None

        return int(values[0])

    def account_details(self):

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        try:

            account = db.fetch_one(
                """
                SELECT
                    sa.*,
                    m.member_no,
                    m.full_name,
                    m.phone,
                    m.address
                FROM savings_accounts sa
                JOIN members m
                    ON sa.member_id=m.id
                WHERE sa.id=?
                """,
                (account_id,)
            )

            if not account:

                messagebox.showerror(
                    "Error",
                    "Account information not found.",
                    parent=self
                )
                return

            transactions = db.fetch_all(
                """
                SELECT
                    transaction_type,
                    amount,
                    balance_after,
                    transaction_date,
                    voucher_no,
                    narration
                FROM savings_transactions
                WHERE account_id=?
                ORDER BY id DESC
                LIMIT 10
                """,
                (account_id,)
            )

            dialog = tk.Toplevel(self)
            dialog.title(
                f"Account Details - {account['account_no']}"
            )
            dialog.geometry("700x550")
            dialog.configure(bg=BG_CARD)
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()

            tk.Label(
                dialog,
                text="Savings Account Details",
                font=("Segoe UI", 16, "bold"),
                bg=BG_CARD,
                fg=TEXT_DARK
            ).pack(
                pady=15
            )

            info = tk.Frame(
                dialog,
                bg=BG_CARD
            )
            info.pack(
                fill="x",
                padx=30
            )

            details = [
                ("Account No.", account["account_no"]),
                ("Member No.", account["member_no"]),
                ("Member Name", account["full_name"]),
                ("Phone", account.get("phone") or "-"),
                ("Account Type", account["account_type"]),
                (
                    "Balance",
                    f"Rs {float(account['balance'] or 0):,.2f}"
                ),
                (
                    "Interest Rate",
                    f"{float(account['interest_rate'] or 0):.2f}%"
                ),
                ("Opened Date", account["opened_date"]),
                ("Status", account["status"])
            ]

            for i, (label, value) in enumerate(details):

                tk.Label(
                    info,
                    text=f"{label}:",
                    font=("Segoe UI", 10, "bold"),
                    bg=BG_CARD,
                    fg=TEXT_DARK
                ).grid(
                    row=i,
                    column=0,
                    sticky="w",
                    padx=5,
                    pady=5
                )

                tk.Label(
                    info,
                    text=value,
                    bg=BG_CARD,
                    fg=TEXT_DARK
                ).grid(
                    row=i,
                    column=1,
                    sticky="w",
                    padx=20,
                    pady=5
                )

            tk.Label(
                dialog,
                text="Recent Transactions",
                font=("Segoe UI", 12, "bold"),
                bg=BG_CARD,
                fg=TEXT_DARK
            ).pack(
                anchor="w",
                padx=30,
                pady=(20, 8)
            )

            tree_frame = tk.Frame(
                dialog,
                bg=BG_CARD
            )
            tree_frame.pack(
                fill="both",
                expand=True,
                padx=30,
                pady=(0, 15)
            )

            columns = (
                "date",
                "voucher",
                "type",
                "amount",
                "balance",
                "narration"
            )

            tree = ttk.Treeview(
                tree_frame,
                columns=columns,
                show="headings",
                height=7
            )

            titles = {
                "date": "Date",
                "voucher": "Voucher",
                "type": "Type",
                "amount": "Amount",
                "balance": "Balance",
                "narration": "Narration"
            }

            for col in columns:

                tree.heading(
                    col,
                    text=titles[col]
                )

                tree.column(
                    col,
                    width=100,
                    anchor="center"
                )

            for row in transactions:

                tree.insert(
                    "",
                    "end",
                    values=(
                        row["transaction_date"],
                        row["voucher_no"] or "-",
                        row["transaction_type"],
                        f"Rs {float(row['amount']):,.2f}",
                        f"Rs {float(row['balance_after']):,.2f}",
                        row["narration"] or ""
                    )
                )

            tree.pack(
                fill="both",
                expand=True
            )

            tk.Button(
                dialog,
                text="Close",
                command=dialog.destroy,
                bg=PRIMARY,
                fg=TEXT_LIGHT,
                relief="flat",
                padx=25,
                pady=7
            ).pack(
                pady=(0, 15)
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to load account details.\n\n{e}",
                parent=self
            )

    # ========================================================
    # CLOSE ACCOUNT
    # ========================================================

    def close_account(self):

        account_id = self.get_selected_account_id()

        if account_id is None:
            return

        try:

            account = db.fetch_one(
                """
                SELECT
                    sa.id,
                    sa.account_no,
                    sa.balance,
                    sa.status,
                    m.full_name
                FROM savings_accounts sa
                JOIN members m
                    ON sa.member_id=m.id
                WHERE sa.id=?
                """,
                (account_id,)
            )

            if not account:

                messagebox.showerror(
                    "Error",
                    "Account not found.",
                    parent=self
                )
                return

            if account["status"] != "active":

                messagebox.showwarning(
                    "Already Closed",
                    "This account is already inactive.",
                    parent=self
                )
                return

            balance = float(
                account["balance"] or 0
            )

            if balance > 0.005:

                messagebox.showerror(
                    "Cannot Close Account",
                    (
                        "The account cannot be closed while "
                        "there is a remaining balance.\n\n"
                        f"Current Balance: "
                        f"Rs {balance:,.2f}"
                    ),
                    parent=self
                )
                return

            confirm = messagebox.askyesno(
                "Close Account",
                (
                    f"Are you sure you want to close "
                    f"account {account['account_no']}?\n\n"
                    f"Member: {account['full_name']}"
                ),
                parent=self
            )

            if not confirm:
                return

            db.execute(
                """
                UPDATE savings_accounts
                SET status='closed'
                WHERE id=?
                """,
                (account_id,)
            )

            messagebox.showinfo(
                "Account Closed",
                "Savings account has been closed successfully.",
                parent=self
            )

            self.refresh_all()

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to close account.\n\n{e}",
                parent=self
            )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_all(self):

        self.load_accounts()
        self.load_history()
        self.load_account_numbers()


# ============================================================
# OPEN ACCOUNT DIALOG
# ============================================================

class OpenAccountDialog(tk.Toplevel):

    def __init__(
        self,
        parent,
        user=None,
        on_saved=None
    ):

        super().__init__(parent)

        self.parent = parent
        self.user = user or {}
        self.on_saved = on_saved

        self.title("Open Savings Account")
        self.geometry("550x500")
        self.resizable(False, False)

        self.configure(
            bg=BG_CARD
        )

        self.transient(
            parent.winfo_toplevel()
        )

        self.grab_set()

        self._build_ui()

    # --------------------------------------------------------
    # USER ID
    # --------------------------------------------------------

    def get_user_id(self):

        if isinstance(self.user, dict):
            return self.user.get("id")

        try:
            return self.user["id"]
        except Exception:
            return None

    # --------------------------------------------------------
    # BUILD UI
    # --------------------------------------------------------

    def _build_ui(self):

        tk.Label(
            self,
            text="Open New Savings Account",
            font=("Segoe UI", 16, "bold"),
            bg=BG_CARD,
            fg=TEXT_DARK
        ).pack(
            pady=(20, 15)
        )

        form = tk.Frame(
            self,
            bg=BG_CARD
        )
        form.pack(
            padx=30,
            fill="x"
        )

        self.account_no = tk.StringVar(
            value=db.next_account_no()
        )

        self.member_no = tk.StringVar()
        self.account_type = tk.StringVar(
            value="Regular"
        )

        self.interest_rate = tk.StringVar(
            value="6.00"
        )

        self.opened_date = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )

        self.member_name = tk.StringVar(
            value=""
        )

        # Account number

        self.add_field(
            form,
            0,
            "Account No.",
            self.account_no,
            readonly=True
        )

        # Member number

        tk.Label(
            form,
            text="Member No.",
            bg=BG_CARD,
            fg=TEXT_DARK
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=9
        )

        member_frame = tk.Frame(
            form,
            bg=BG_CARD
        )
        member_frame.grid(
            row=1,
            column=1,
            sticky="w",
            padx=10,
            pady=9
        )

        ttk.Entry(
            member_frame,
            textvariable=self.member_no,
            width=25
        ).pack(
            side="left"
        )

        tk.Button(
            member_frame,
            text="Check",
            command=self.check_member,
            bg=PRIMARY,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=8
        ).pack(
            side="left",
            padx=5
        )

        # Member name

        tk.Label(
            form,
            text="Member Name",
            bg=BG_CARD,
            fg=TEXT_DARK
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=9
        )

        tk.Label(
            form,
            textvariable=self.member_name,
            bg=BG_CARD,
            fg=TEXT_MUTED
        ).grid(
            row=2,
            column=1,
            sticky="w",
            padx=10,
            pady=9
        )

        # Account type

        tk.Label(
            form,
            text="Account Type",
            bg=BG_CARD,
            fg=TEXT_DARK
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=5,
            pady=9
        )

        ttk.Combobox(
            form,
            textvariable=self.account_type,
            values=(
                "Regular",
                "Fixed Deposit",
                "Recurring"
            ),
            state="readonly",
            width=28
        ).grid(
            row=3,
            column=1,
            sticky="w",
            padx=10,
            pady=9
        )

        # Interest rate

        self.add_field(
            form,
            4,
            "Interest Rate (%)",
            self.interest_rate
        )

        # Opened date

        self.add_field(
            form,
            5,
            "Opened Date",
            self.opened_date
        )

        # Buttons

        button_frame = tk.Frame(
            self,
            bg=BG_CARD
        )
        button_frame.pack(
            pady=25
        )

        tk.Button(
            button_frame,
            text="Create Account",
            command=self.save_account,
            bg=SUCCESS,
            fg=TEXT_LIGHT,
            relief="flat",
            padx=20,
            pady=9
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            relief="flat",
            padx=20,
            pady=9
        ).pack(
            side="left",
            padx=5
        )

    # --------------------------------------------------------
    # ADD FIELD
    # --------------------------------------------------------

    def add_field(
        self,
        parent,
        row,
        label,
        variable,
        readonly=False
    ):

        tk.Label(
            parent,
            text=label,
            bg=BG_CARD,
            fg=TEXT_DARK
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=5,
            pady=9
        )

        entry = ttk.Entry(
            parent,
            textvariable=variable,
            width=31
        )

        entry.grid(
            row=row,
            column=1,
            sticky="w",
            padx=10,
            pady=9
        )

        if readonly:
            entry.configure(
                state="readonly"
            )

    # --------------------------------------------------------
    # CHECK MEMBER
    # --------------------------------------------------------

    def check_member(self):

        member_no = self.member_no.get().strip()

        if not member_no:

            messagebox.showwarning(
                "Member Required",
                "Please enter a member number.",
                parent=self
            )
            return

        try:

            row = db.fetch_one(
                """
                SELECT
                    id,
                    member_no,
                    full_name,
                    status
                FROM members
                WHERE member_no=?
                """,
                (member_no,)
            )

            if not row:

                self.member_name.set("Member not found")

                messagebox.showerror(
                    "Member Not Found",
                    "No member was found with this member number.",
                    parent=self
                )

                return

            if row["status"] != "active":

                self.member_name.set(
                    f"{row['full_name']} (Inactive)"
                )

                messagebox.showwarning(
                    "Inactive Member",
                    "Only active members can open a savings account.",
                    parent=self
                )

                return

            self.member_name.set(
                row["full_name"]
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to check member.\n\n{e}",
                parent=self
            )




    # --------------------------------------------------------
    # SAVE ACCOUNT
    # --------------------------------------------------------

    def save_account(self):

        account_no = self.account_no.get().strip()
        member_no = self.member_no.get().strip()
        account_type = self.account_type.get().strip()
        interest_text = self.interest_rate.get().strip()
        opened_date = self.opened_date.get().strip()

        if not member_no:

            messagebox.showwarning(
                "Required",
                "Please enter a member number.",
                parent=self
            )
            return

        if not account_type:

            messagebox.showwarning(
                "Required",
                "Please select an account type.",
                parent=self
            )
            return

        try:

            interest_rate = float(
                interest_text
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Interest Rate",
                "Please enter a valid interest rate.",
                parent=self
            )
            return

        if interest_rate < 0:

            messagebox.showerror(
                "Invalid Interest Rate",
                "Interest rate cannot be negative.",
                parent=self
            )
            return

        try:

            datetime.strptime(
                opened_date,
                "%Y-%m-%d"
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Date",
                "Date must be in YYYY-MM-DD format.",
                parent=self
            )
            return

        try:

            member = db.fetch_one(
                """
                SELECT
                    id,
                    member_no,
                    full_name,
                    status
                FROM members
                WHERE member_no=?
                """,
                (member_no,)
            )

            if not member:

                messagebox.showerror(
                    "Member Not Found",
                    "Member does not exist.",
                    parent=self
                )
                return

            if member["status"] != "active":

                messagebox.showerror(
                    "Inactive Member",
                    "Only active members can open a savings account.",
                    parent=self
                )
                return

            # Check duplicate active account

            duplicate = db.fetch_one(
                """
                SELECT id
                FROM savings_accounts
                WHERE account_no=?
                """,
                (account_no,)
            )

            if duplicate:

                messagebox.showerror(
                    "Duplicate Account",
                    (
                        f"Account number {account_no} "
                        "already exists."
                    ),
                    parent=self
                )
                return

            user_id = self.get_user_id()

            db.execute(
                """
                INSERT INTO savings_accounts
                (
                    account_no,
                    member_id,
                    account_type,
                    balance,
                    interest_rate,
                    opened_date,
                    status,
                    created_by
                )
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    account_no,
                    member["id"],
                    account_type,
                    0.0,
                    interest_rate,
                    opened_date,
                    "active",
                    user_id
                )
            )

            messagebox.showinfo(
                "Success",
                (
                    "Savings account created successfully.\n\n"
                    f"Account No.: {account_no}\n"
                    f"Member No.: {member_no}\n"
                    f"Member Name: {member['full_name']}\n"
                    f"Account Type: {account_type}"
                ),
                parent=self
            )

            if self.on_saved:
                self.on_saved()

            self.destroy()

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Unable to create savings account.\n\n{e}",
                parent=self
            )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    db.initialize_database()

    root = tk.Tk()

    root.title(
        "Sahakari MIS - Savings"
    )

    root.geometry(
        "1200x700"
    )

    try:
        st.configure_styles()
    except Exception:
        pass

    page = SavingsPage(
        root,
        {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "full_name": "System Administrator"
        }
    )

    page.pack(
        fill="both",
        expand=True
    )

    root.mainloop()
