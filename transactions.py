import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os

import database as db
import styles as st


def create_frame(parent, user):
    frame = tk.Frame(parent, bg=st.BG_MAIN)
    TransactionsPage(frame, user)
    return frame


class TransactionsPage:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user

        try:
            self._build()
        except Exception as e:
            self._show_build_error(e)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _show_build_error(self, error):
        for widget in self.parent.winfo_children():
            widget.destroy()

        card = tk.Frame(
            self.parent,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=30, pady=30)

        tk.Label(
            card,
            text="Unable to load Daily Transactions",
            font=st.FONT_HEADING,
            bg=st.BG_CARD,
            fg=st.DANGER
        ).pack(pady=(30, 10))

        tk.Label(
            card,
            text=f"{type(error).__name__}: {error}",
            font=st.FONT_NORMAL,
            bg=st.BG_CARD,
            fg=st.TEXT_DARK,
            wraplength=700,
            justify="left"
        ).pack(padx=30, pady=10)

    # ------------------------------------------------------------------
    # Main UI
    # ------------------------------------------------------------------

    def _build(self):
        hdr = tk.Frame(
            self.parent,
            bg=st.BG_CARD,
            height=58
        )
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="Daily Transactions",
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

        nb = ttk.Notebook(self.parent)
        nb.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=10
        )

        # --------------------------------------------------------------
        # Tab 1
        # --------------------------------------------------------------

        t1 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t1, text="  Daily Summary  ")
        self._build_summary(t1)

        # --------------------------------------------------------------
        # Tab 2
        # --------------------------------------------------------------

        t2 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t2, text="  Income Entry  ")
        self._build_income(t2)

        # --------------------------------------------------------------
        # Tab 3
        # --------------------------------------------------------------

        t3 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t3, text="  Expense Entry  ")
        self._build_expense(t3)

        # --------------------------------------------------------------
        # Tab 4
        # --------------------------------------------------------------

        t4 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t4, text="  All Transactions  ")
        self._build_all(t4)

        # --------------------------------------------------------------
        # Tab 5
        # --------------------------------------------------------------

        t5 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t5, text="  Day Closing Report  ")
        self._build_day_close(t5)

    # ==================================================================
    # TAB 1 - DAILY SUMMARY
    # ==================================================================

    def _build_summary(self, parent):

        sf = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )
        sf.pack(
            fill="x",
            padx=12,
            pady=8
        )

        tk.Label(
            sf,
            text="Date:",
            font=st.FONT_NORMAL,
            bg=st.BG_MAIN
        ).pack(side="left")

        self.sum_date = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )

        ttk.Entry(
            sf,
            textvariable=self.sum_date,
            width=14,
            font=st.FONT_NORMAL
        ).pack(
            side="left",
            padx=8,
            ipady=4
        )

        ttk.Button(
            sf,
            text="🔍  Load",
            style="Primary.TButton",
            command=self._load_summary
        ).pack(side="left")

        self.sum_cards = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )
        self.sum_cards.pack(
            fill="x",
            padx=12,
            pady=8
        )

        self.sum_income_tree_frame = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )
        self.sum_income_tree_frame.pack(
            fill="both",
            expand=True,
            padx=12
        )

        self._load_summary()

    def _load_summary(self):

        try:
            date = self.sum_date.get().strip()

            for widget in self.sum_cards.winfo_children():
                widget.destroy()

            for widget in self.sum_income_tree_frame.winfo_children():
                widget.destroy()

            inc = db.fetch_one(
                """
                SELECT COALESCE(SUM(amount), 0) AS v
                FROM daily_income
                WHERE income_date=?
                """,
                (date,)
            )

            exp = db.fetch_one(
                """
                SELECT COALESCE(SUM(amount), 0) AS v
                FROM daily_expense
                WHERE expense_date=?
                """,
                (date,)
            )

            dep = db.fetch_one(
                """
                SELECT COALESCE(SUM(st.amount), 0) AS v
                FROM savings_transactions st
                WHERE st.transaction_type='deposit'
                AND DATE(st.created_at)=?
                """,
                (date,)
            )

            wit = db.fetch_one(
                """
                SELECT COALESCE(SUM(st.amount), 0) AS v
                FROM savings_transactions st
                WHERE st.transaction_type='withdraw'
                AND DATE(st.created_at)=?
                """,
                (date,)
            )

            loan_rep = db.fetch_one(
                """
                SELECT COALESCE(SUM(total_paid), 0) AS v
                FROM loan_repayments
                WHERE payment_date=?
                """,
                (date,)
            )

            inc_amt = inc["v"] if inc else 0
            exp_amt = exp["v"] if exp else 0
            dep_amt = dep["v"] if dep else 0
            wit_amt = wit["v"] if wit else 0
            loan_rep_amt = loan_rep["v"] if loan_rep else 0

            net_cash = (
                inc_amt
                + dep_amt
                + loan_rep_amt
                - exp_amt
                - wit_amt
            )

            stats = [
                (
                    "Daily Income",
                    f"Rs {inc_amt:,.2f}",
                    st.SUCCESS
                ),
                (
                    "Daily Expense",
                    f"Rs {exp_amt:,.2f}",
                    st.DANGER
                ),
                (
                    "Savings Deposits",
                    f"Rs {dep_amt:,.2f}",
                    "#2980b9"
                ),
                (
                    "Savings Withdrawals",
                    f"Rs {wit_amt:,.2f}",
                    "#8e44ad"
                ),
                (
                    "Loan Repayments",
                    f"Rs {loan_rep_amt:,.2f}",
                    st.ACCENT
                ),
                (
                    "Net Cash Flow",
                    f"Rs {net_cash:,.2f}",
                    st.PRIMARY if net_cash >= 0 else st.DANGER
                )
            ]

            for c in range(3):
                self.sum_cards.columnconfigure(
                    c,
                    weight=1
                )

            for i, (title, value, color) in enumerate(stats):

                row, col = divmod(i, 3)

                card = tk.Frame(
                    self.sum_cards,
                    bg=st.BG_CARD,
                    highlightbackground=st.BORDER,
                    highlightthickness=1
                )

                card.grid(
                    row=row,
                    column=col,
                    padx=6,
                    pady=6,
                    sticky="nsew"
                )

                tk.Label(
                    card,
                    text=title,
                    font=st.FONT_SMALL,
                    bg=st.BG_CARD,
                    fg=st.TEXT_MUTED
                ).pack(pady=(12, 2))

                tk.Label(
                    card,
                    text=value,
                    font=("Helvetica", 16, "bold"),
                    bg=st.BG_CARD,
                    fg=color
                ).pack(pady=(0, 12))

            outer = tk.Frame(
                self.sum_income_tree_frame,
                bg=st.BG_MAIN
            )

            outer.pack(
                fill="both",
                expand=True
            )

            outer.columnconfigure(0, weight=1)
            outer.columnconfigure(1, weight=1)

            tables = [
                (
                    0,
                    "Today's Income",
                    """
                    SELECT category, amount, narration
                    FROM daily_income
                    WHERE income_date=?
                    ORDER BY id DESC
                    """,
                    "#eafaf1"
                ),
                (
                    1,
                    "Today's Expense",
                    """
                    SELECT category, amount, narration
                    FROM daily_expense
                    WHERE expense_date=?
                    ORDER BY id DESC
                    """,
                    "#fdf2f0"
                )
            ]

            for col, title, query, bg_color in tables:

                card = tk.Frame(
                    outer,
                    bg=st.BG_CARD,
                    highlightbackground=st.BORDER,
                    highlightthickness=1
                )

                card.grid(
                    row=0,
                    column=col,
                    padx=6,
                    sticky="nsew"
                )

                tk.Label(
                    card,
                    text=title,
                    font=st.FONT_SUB,
                    bg=st.BG_CARD,
                    fg=st.PRIMARY
                ).pack(
                    anchor="w",
                    padx=10,
                    pady=(8, 4)
                )

                tk.Frame(
                    card,
                    bg=st.BORDER,
                    height=1
                ).pack(
                    fill="x",
                    padx=10
                )

                rows = db.fetch_all(
                    query,
                    (date,)
                )

                for row in rows:

                    row_frame = tk.Frame(
                        card,
                        bg=bg_color
                    )

                    row_frame.pack(
                        fill="x",
                        padx=4,
                        pady=1
                    )

                    tk.Label(
                        row_frame,
                        text=row["category"],
                        font=st.FONT_SMALL,
                        bg=bg_color,
                        fg=st.TEXT_DARK,
                        width=20,
                        anchor="w"
                    ).pack(
                        side="left",
                        padx=6,
                        pady=4
                    )

                    tk.Label(
                        row_frame,
                        text=f"Rs {row['amount']:,.2f}",
                        font=st.FONT_SMALL,
                        bg=bg_color,
                        fg=st.SUCCESS if col == 0 else st.DANGER
                    ).pack(
                        side="right",
                        padx=6
                    )

                if not rows:

                    tk.Label(
                        card,
                        text="No records for this date.",
                        font=st.FONT_SMALL,
                        bg=st.BG_CARD,
                        fg=st.TEXT_MUTED
                    ).pack(pady=12)

        except Exception as e:

            messagebox.showerror(
                "Daily Summary Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    # ==================================================================
    # TAB 2 - INCOME ENTRY
    # ==================================================================

    def _build_income(self, parent):

        outer = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        outer.pack(
            fill="both",
            expand=True
        )

        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

        form_card = tk.Frame(
            outer,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        form_card.grid(
            row=0,
            column=0,
            padx=(12, 6),
            pady=12,
            sticky="nsew"
        )

        tk.Label(
            form_card,
            text="Add Income Entry",
            font=st.FONT_HEADING,
            bg=st.BG_CARD,
            fg=st.SUCCESS
        ).pack(
            anchor="w",
            padx=14,
            pady=(12, 6)
        )

        tk.Frame(
            form_card,
            bg=st.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=14
        )

        self.inc_vars = {}

        fields = [
            ("Date *", "inc_date", "entry"),
            ("Category *", "inc_cat", "combo"),
            ("Amount *", "inc_amount", "entry"),
            ("Narration", "inc_narr", "entry"),
            ("Voucher No", "inc_vno", "entry")
        ]

        categories = [
            "Interest Income",
            "Membership Fee",
            "Service Charge",
            "Share Application Fee",
            "Penalty",
            "Other Income"
        ]

        form = tk.Frame(
            form_card,
            bg=st.BG_CARD
        )

        form.pack(
            fill="x",
            padx=14,
            pady=10
        )

        for label_text, key, widget_type in fields:

            tk.Label(
                form,
                text=label_text,
                font=st.FONT_SMALL,
                bg=st.BG_CARD,
                fg=st.TEXT_MUTED
            ).pack(anchor="w")

            self.inc_vars[key] = tk.StringVar()

            if widget_type == "combo":

                widget = ttk.Combobox(
                    form,
                    textvariable=self.inc_vars[key],
                    values=categories,
                    font=st.FONT_NORMAL
                )

            else:

                widget = ttk.Entry(
                    form,
                    textvariable=self.inc_vars[key],
                    font=st.FONT_NORMAL
                )

            widget.pack(
                fill="x",
                ipady=5,
                pady=(2, 8)
            )

        self.inc_vars["inc_date"].set(
            datetime.now().strftime("%Y-%m-%d")
        )

        ttk.Button(
            form_card,
            text="✅  Add Income",
            style="Success.TButton",
            command=self._add_income
        ).pack(
            padx=14,
            pady=(0, 14),
            fill="x"
        )

        list_card = tk.Frame(
            outer,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        list_card.grid(
            row=0,
            column=1,
            padx=(6, 12),
            pady=12,
            sticky="nsew"
        )

        tk.Label(
            list_card,
            text="Recent Income",
            font=st.FONT_HEADING,
            bg=st.BG_CARD,
            fg=st.SUCCESS
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 6)
        )

        tk.Frame(
            list_card,
            bg=st.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=12
        )

        columns = (
            "Date",
            "Category",
            "Amount",
            "Narration"
        )

        self.inc_tree = ttk.Treeview(
            list_card,
            columns=columns,
            show="headings",
            height=14
        )

        vsb = ttk.Scrollbar(
            list_card,
            orient="vertical",
            command=self.inc_tree.yview
        )

        self.inc_tree.configure(
            yscrollcommand=vsb.set
        )

        vsb.pack(
            side="right",
            fill="y",
            pady=6
        )

        self.inc_tree.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=6
        )

        for column, width in zip(
            columns,
            [90, 160, 100, 200]
        ):
            self.inc_tree.heading(
                column,
                text=column
            )

            self.inc_tree.column(
                column,
                width=width,
                anchor="center" if width <= 100 else "w"
            )

        self._load_inc_list()

    def _add_income(self):

        try:

            values = {
                key: var.get().strip()
                for key, var in self.inc_vars.items()
            }

            if (
                not values["inc_cat"]
                or not values["inc_amount"]
                or not values["inc_date"]
            ):
                messagebox.showerror(
                    "Error",
                    "Date, category and amount are required.",
                    parent=self.parent
                )
                return

            try:
                amount = float(
                    values["inc_amount"].replace(",", "")
                )
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Invalid amount.",
                    parent=self.parent
                )
                return

            if amount <= 0:
                messagebox.showerror(
                    "Error",
                    "Amount must be greater than zero.",
                    parent=self.parent
                )
                return

            db.execute(
                """
                INSERT INTO daily_income
                (
                    income_date,
                    category,
                    amount,
                    narration,
                    voucher_no,
                    created_by
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    values["inc_date"],
                    values["inc_cat"],
                    amount,
                    values["inc_narr"],
                    values["inc_vno"],
                    self.user["id"]
                )
            )

            messagebox.showinfo(
                "Saved",
                f"Income Rs {amount:,.2f} recorded.",
                parent=self.parent
            )

            self.inc_vars["inc_amount"].set("")
            self.inc_vars["inc_narr"].set("")
            self.inc_vars["inc_vno"].set("")

            self._load_inc_list()

            self._load_summary()

        except Exception as e:

            messagebox.showerror(
                "Income Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    def _load_inc_list(self):

        try:

            self.inc_tree.delete(
                *self.inc_tree.get_children()
            )

            rows = db.fetch_all(
                """
                SELECT
                    income_date,
                    category,
                    amount,
                    narration
                FROM daily_income
                ORDER BY id DESC
                LIMIT 100
                """
            )

            for i, row in enumerate(rows, 1):

                tag = (
                    "even"
                    if i % 2 == 0
                    else "odd"
                )

                self.inc_tree.insert(
                    "",
                    "end",
                    values=(
                        row["income_date"],
                        row["category"],
                        f"Rs {row['amount']:,.2f}",
                        row["narration"] or "-"
                    ),
                    tags=(tag,)
                )

            self.inc_tree.tag_configure(
                "even",
                background="#eafaf1"
            )

            self.inc_tree.tag_configure(
                "odd",
                background=st.BG_CARD
            )

        except Exception as e:

            messagebox.showerror(
                "Income List Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    # ==================================================================
    # TAB 3 - EXPENSE ENTRY
    # ==================================================================

    def _build_expense(self, parent):

        outer = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        outer.pack(
            fill="both",
            expand=True
        )

        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

        form_card = tk.Frame(
            outer,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        form_card.grid(
            row=0,
            column=0,
            padx=(12, 6),
            pady=12,
            sticky="nsew"
        )

        tk.Label(
            form_card,
            text="Add Expense Entry",
            font=st.FONT_HEADING,
            bg=st.BG_CARD,
            fg=st.DANGER
        ).pack(
            anchor="w",
            padx=14,
            pady=(12, 6)
        )

        tk.Frame(
            form_card,
            bg=st.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=14
        )

        self.exp_vars = {}

        categories = [
            "Staff Salary",
            "Office Rent",
            "Stationery",
            "Utilities",
            "Maintenance",
            "Transport",
            "Entertainment",
            "Miscellaneous"
        ]

        fields = [
            ("Date *", "exp_date", "entry"),
            ("Category *", "exp_cat", "combo"),
            ("Amount *", "exp_amount", "entry"),
            ("Narration", "exp_narr", "entry"),
            ("Voucher No", "exp_vno", "entry")
        ]

        form = tk.Frame(
            form_card,
            bg=st.BG_CARD
        )

        form.pack(
            fill="x",
            padx=14,
            pady=10
        )

        for label_text, key, widget_type in fields:

            tk.Label(
                form,
                text=label_text,
                font=st.FONT_SMALL,
                bg=st.BG_CARD,
                fg=st.TEXT_MUTED
            ).pack(anchor="w")

            self.exp_vars[key] = tk.StringVar()

            if widget_type == "combo":

                widget = ttk.Combobox(
                    form,
                    textvariable=self.exp_vars[key],
                    values=categories,
                    font=st.FONT_NORMAL
                )

            else:

                widget = ttk.Entry(
                    form,
                    textvariable=self.exp_vars[key],
                    font=st.FONT_NORMAL
                )

            widget.pack(
                fill="x",
                ipady=5,
                pady=(2, 8)
            )

        self.exp_vars["exp_date"].set(
            datetime.now().strftime("%Y-%m-%d")
        )

        ttk.Button(
            form_card,
            text="✅  Add Expense",
            style="Danger.TButton",
            command=self._add_expense
        ).pack(
            padx=14,
            pady=(0, 14),
            fill="x"
        )

        list_card = tk.Frame(
            outer,
            bg=st.BG_CARD,
            highlightbackground=st.BORDER,
            highlightthickness=1
        )

        list_card.grid(
            row=0,
            column=1,
            padx=(6, 12),
            pady=12,
            sticky="nsew"
        )

        tk.Label(
            list_card,
            text="Recent Expenses",
            font=st.FONT_HEADING,
            bg=st.BG_CARD,
            fg=st.DANGER
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 6)
        )

        tk.Frame(
            list_card,
            bg=st.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=12
        )

        columns = (
            "Date",
            "Category",
            "Amount",
            "Narration"
        )

        self.exp_tree = ttk.Treeview(
            list_card,
            columns=columns,
            show="headings",
            height=14
        )

        vsb = ttk.Scrollbar(
            list_card,
            orient="vertical",
            command=self.exp_tree.yview
        )

        self.exp_tree.configure(
            yscrollcommand=vsb.set
        )

        vsb.pack(
            side="right",
            fill="y",
            pady=6
        )

        self.exp_tree.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=6
        )

        for column, width in zip(
            columns,
            [90, 160, 100, 200]
        ):
            self.exp_tree.heading(
                column,
                text=column
            )

            self.exp_tree.column(
                column,
                width=width,
                anchor="center" if width <= 100 else "w"
            )

        self._load_exp_list()

    def _add_expense(self):

        try:

            values = {
                key: var.get().strip()
                for key, var in self.exp_vars.items()
            }

            if (
                not values["exp_cat"]
                or not values["exp_amount"]
                or not values["exp_date"]
            ):
                messagebox.showerror(
                    "Error",
                    "Date, category and amount are required.",
                    parent=self.parent
                )
                return

            try:
                amount = float(
                    values["exp_amount"].replace(",", "")
                )
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Invalid amount.",
                    parent=self.parent
                )
                return

            if amount <= 0:
                messagebox.showerror(
                    "Error",
                    "Amount must be greater than zero.",
                    parent=self.parent
                )
                return

            db.execute(
                """
                INSERT INTO daily_expense
                (
                    expense_date,
                    category,
                    amount,
                    narration,
                    voucher_no,
                    created_by
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    values["exp_date"],
                    values["exp_cat"],
                    amount,
                    values["exp_narr"],
                    values["exp_vno"],
                    self.user["id"]
                )
            )

            messagebox.showinfo(
                "Saved",
                f"Expense Rs {amount:,.2f} recorded.",
                parent=self.parent
            )

            self.exp_vars["exp_amount"].set("")
            self.exp_vars["exp_narr"].set("")
            self.exp_vars["exp_vno"].set("")

            self._load_exp_list()

            self._load_summary()

        except Exception as e:

            messagebox.showerror(
                "Expense Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    def _load_exp_list(self):

        try:

            self.exp_tree.delete(
                *self.exp_tree.get_children()
            )

            rows = db.fetch_all(
                """
                SELECT
                    expense_date,
                    category,
                    amount,
                    narration
                FROM daily_expense
                ORDER BY id DESC
                LIMIT 100
                """
            )

            for i, row in enumerate(rows, 1):

                tag = (
                    "even"
                    if i % 2 == 0
                    else "odd"
                )

                self.exp_tree.insert(
                    "",
                    "end",
                    values=(
                        row["expense_date"],
                        row["category"],
                        f"Rs {row['amount']:,.2f}",
                        row["narration"] or "-"
                    ),
                    tags=(tag,)
                )

            self.exp_tree.tag_configure(
                "even",
                background="#fdf2f0"
            )

            self.exp_tree.tag_configure(
                "odd",
                background=st.BG_CARD
            )

        except Exception as e:

            messagebox.showerror(
                "Expense List Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    # ==================================================================
    # TAB 4 - ALL TRANSACTIONS
    # ==================================================================

    def _build_all(self, parent):

        sf = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        sf.pack(
            fill="x",
            padx=10,
            pady=8
        )

        tk.Label(
            sf,
            text="From:",
            font=st.FONT_NORMAL,
            bg=st.BG_MAIN
        ).pack(side="left")

        self.all_from = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-01")
        )

        ttk.Entry(
            sf,
            textvariable=self.all_from,
            width=12,
            font=st.FONT_NORMAL
        ).pack(
            side="left",
            padx=6,
            ipady=4
        )

        tk.Label(
            sf,
            text="To:",
            font=st.FONT_NORMAL,
            bg=st.BG_MAIN
        ).pack(side="left")

        self.all_to = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )

        ttk.Entry(
            sf,
            textvariable=self.all_to,
            width=12,
            font=st.FONT_NORMAL
        ).pack(
            side="left",
            padx=6,
            ipady=4
        )

        ttk.Button(
            sf,
            text="🔍  Load",
            style="Primary.TButton",
            command=self._load_all
        ).pack(
            side="left",
            padx=8
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
            padx=10
        )

        columns = (
            "No.",
            "Date",
            "Type",
            "Category",
            "Amount",
            "Narration"
        )

        self.all_tree = ttk.Treeview(
            tf,
            columns=columns,
            show="headings"
        )

        vsb = ttk.Scrollbar(
            tf,
            orient="vertical",
            command=self.all_tree.yview
        )

        self.all_tree.configure(
            yscrollcommand=vsb.set
        )

        vsb.pack(
            side="right",
            fill="y"
        )

        self.all_tree.pack(
            fill="both",
            expand=True
        )

        widths = [
            40,
            100,
            90,
            160,
            110,
            250
        ]

        for column, width in zip(
            columns,
            widths
        ):

            self.all_tree.heading(
                column,
                text=column
            )

            self.all_tree.column(
                column,
                width=width,
                anchor="center" if width <= 110 else "w"
            )

        self.all_sum = tk.StringVar()

        tk.Label(
            parent,
            textvariable=self.all_sum,
            font=st.FONT_SUB,
            bg=st.BG_MAIN,
            fg=st.PRIMARY
        ).pack(
            anchor="e",
            padx=10,
            pady=4
        )

        self._load_all()

    def _load_all(self):

        try:

            self.all_tree.delete(
                *self.all_tree.get_children()
            )

            fr = self.all_from.get().strip()
            to = self.all_to.get().strip()

            if not fr or not to:

                messagebox.showerror(
                    "Error",
                    "Both From and To dates are required.",
                    parent=self.parent
                )
                return

            incomes = db.fetch_all(
                """
                SELECT
                    income_date AS dt,
                    'Income' AS tp,
                    category,
                    amount,
                    narration
                FROM daily_income
                WHERE income_date BETWEEN ? AND ?
                """,
                (fr, to)
            )

            expenses = db.fetch_all(
                """
                SELECT
                    expense_date AS dt,
                    'Expense' AS tp,
                    category,
                    amount,
                    narration
                FROM daily_expense
                WHERE expense_date BETWEEN ? AND ?
                """,
                (fr, to)
            )

            rows = sorted(
                incomes + expenses,
                key=lambda row: row["dt"],
                reverse=True
            )

            total_in = sum(
                float(row["amount"])
                for row in rows
                if row["tp"] == "Income"
            )

            total_out = sum(
                float(row["amount"])
                for row in rows
                if row["tp"] == "Expense"
            )

            for i, row in enumerate(rows, 1):

                tag = (
                    "income"
                    if row["tp"] == "Income"
                    else "expense"
                )

                self.all_tree.insert(
                    "",
                    "end",
                    values=(
                        i,
                        row["dt"],
                        row["tp"],
                        row["category"],
                        f"Rs {row['amount']:,.2f}",
                        row["narration"] or "-"
                    ),
                    tags=(tag,)
                )

            self.all_tree.tag_configure(
                "income",
                background="#eafaf1"
            )

            self.all_tree.tag_configure(
                "expense",
                background="#fdf2f0"
            )

            self.all_sum.set(
                f"Total Income: Rs {total_in:,.2f}    "
                f"Total Expense: Rs {total_out:,.2f}    "
                f"Net: Rs {(total_in - total_out):,.2f}"
            )

        except Exception as e:

            messagebox.showerror(
                "Transaction Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    # ==================================================================
    # TAB 5 - DAY CLOSING REPORT
    # ==================================================================

    def _build_day_close(self, parent):

        sf = tk.Frame(
            parent,
            bg=st.BG_MAIN
        )

        sf.pack(
            fill="x",
            padx=12,
            pady=8
        )

        tk.Label(
            sf,
            text="Date:",
            font=st.FONT_NORMAL,
            bg=st.BG_MAIN
        ).pack(side="left")

        self.dc_date = tk.StringVar(
            value=datetime.now().strftime("%Y-%m-%d")
        )

        ttk.Entry(
            sf,
            textvariable=self.dc_date,
            width=14,
            font=st.FONT_NORMAL
        ).pack(
            side="left",
            padx=8,
            ipady=4
        )

        ttk.Button(
            sf,
            text="📋  Generate Report",
            style="Primary.TButton",
            command=self._gen_day_close
        ).pack(side="left")

        ttk.Button(
            sf,
            text="💾  Export TXT",
            style="Info.TButton",
            command=self._export_day_close
        ).pack(
            side="left",
            padx=8
        )

        self.dc_text = tk.Text(
            parent,
            font=st.FONT_MONO,
            bg=st.BG_CARD,
            fg=st.TEXT_DARK,
            relief="solid",
            borderwidth=1,
            wrap="none"
        )

        vsb = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=self.dc_text.yview
        )

        hsb = ttk.Scrollbar(
            parent,
            orient="horizontal",
            command=self.dc_text.xview
        )

        self.dc_text.configure(
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

        self.dc_text.pack(
            fill="both",
            expand=True,
            padx=12
        )

        self._gen_day_close()

    def _get_day_close_text(self):

        date = self.dc_date.get().strip()

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        inc_rows = db.fetch_all(
            """
            SELECT
                category,
                SUM(amount) AS amt
            FROM daily_income
            WHERE income_date=?
            GROUP BY category
            """,
            (date,)
        )

        exp_rows = db.fetch_all(
            """
            SELECT
                category,
                SUM(amount) AS amt
            FROM daily_expense
            WHERE expense_date=?
            GROUP BY category
            """,
            (date,)
        )

        # --------------------------------------------------------------
        # FIX:
        # Do not use .get() because database rows may be sqlite3.Row.
        # --------------------------------------------------------------

        dep_row = db.fetch_one(
            """
            SELECT COALESCE(SUM(amount), 0) AS v
            FROM savings_transactions
            WHERE transaction_type='deposit'
            AND DATE(created_at)=?
            """,
            (date,)
        )

        dep_amt = (
            dep_row["v"]
            if dep_row is not None
            else 0
        )

        wit_row = db.fetch_one(
            """
            SELECT COALESCE(SUM(amount), 0) AS v
            FROM savings_transactions
            WHERE transaction_type='withdraw'
            AND DATE(created_at)=?
            """,
            (date,)
        )

        wit_amt = (
            wit_row["v"]
            if wit_row is not None
            else 0
        )

        loan_row = db.fetch_one(
            """
            SELECT COALESCE(SUM(total_paid), 0) AS v
            FROM loan_repayments
            WHERE payment_date=?
            """,
            (date,)
        )

        loan_rep = (
            loan_row["v"]
            if loan_row is not None
            else 0
        )

        total_inc = sum(
            float(row["amt"])
            for row in inc_rows
        )

        total_exp = sum(
            float(row["amt"])
            for row in exp_rows
        )

        total_inflows = (
            total_inc
            + float(dep_amt or 0)
            + float(loan_rep or 0)
        )

        total_outflows = (
            total_exp
            + float(wit_amt or 0)
        )

        net_cash = (
            total_inflows
            - total_outflows
        )

        lines = [
            "=" * 56,
            f"  DAY CLOSING REPORT — {date}",
            "  Sahakari Cooperative Management System",
            "=" * 56,
            "",
            "  INCOME SUMMARY",
            "-" * 56
        ]

        for row in inc_rows:

            lines.append(
                f"  {row['category']:<35} "
                f"Rs {float(row['amt']):>12,.2f}"
            )

        lines += [
            f"  {'Savings Deposits':<35} "
            f"Rs {float(dep_amt or 0):>12,.2f}",

            f"  {'Loan Repayments Received':<35} "
            f"Rs {float(loan_rep or 0):>12,.2f}",

            "-" * 56,

            f"  {'TOTAL INFLOWS':<35} "
            f"Rs {total_inflows:>12,.2f}",

            "",

            "  EXPENSE SUMMARY",
            "-" * 56
        ]

        for row in exp_rows:

            lines.append(
                f"  {row['category']:<35} "
                f"Rs {float(row['amt']):>12,.2f}"
            )

        lines += [
            f"  {'Savings Withdrawals':<35} "
            f"Rs {float(wit_amt or 0):>12,.2f}",

            "-" * 56,

            f"  {'TOTAL OUTFLOWS':<35} "
            f"Rs {total_outflows:>12,.2f}",

            "",

            "=" * 56,

            f"  {'NET CASH FLOW':<35} "
            f"Rs {net_cash:>12,.2f}",

            "=" * 56,

            "",

            f"  Report generated: "
            f"{datetime.now().strftime('%d %B %Y  %I:%M %p')}",

            f"  Officer: "
            f"{self.user.get('username', 'Admin')}"
        ]

        return "\n".join(lines)

    def _gen_day_close(self):

        try:

            text = self._get_day_close_text()

            self.dc_text.config(
                state="normal"
            )

            self.dc_text.delete(
                "1.0",
                "end"
            )

            self.dc_text.insert(
                "1.0",
                text
            )

            self.dc_text.config(
                state="disabled"
            )

        except Exception as e:

            self.dc_text.config(
                state="normal"
            )

            self.dc_text.delete(
                "1.0",
                "end"
            )

            self.dc_text.insert(
                "1.0",
                "Unable to generate Day Closing Report.\n\n"
                f"Error: {type(e).__name__}: {e}"
            )

            self.dc_text.config(
                state="disabled"
            )

            messagebox.showerror(
                "Day Closing Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )

    def _export_day_close(self):

        try:

            text = self._get_day_close_text()

            date = (
                self.dc_date.get()
                .strip()
                .replace("-", "")
            )

            if not date:
                date = datetime.now().strftime("%Y%m%d")

            path = os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ),
                f"day_close_{date}.txt"
            )

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:
                file.write(text)

            messagebox.showinfo(
                "Exported",
                f"Report saved to:\n{path}",
                parent=self.parent
            )

        except Exception as e:

            messagebox.showerror(
                "Export Error",
                f"{type(e).__name__}: {e}",
                parent=self.parent
            )