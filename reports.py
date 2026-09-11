import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import database as db
import styles as st


def create_frame(parent, user):
    frame = tk.Frame(parent, bg=st.BG_MAIN)
    ReportsPage(frame, user)
    return frame


REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports_output")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ReportsPage:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self._build()

    def _build(self):
        hdr = tk.Frame(self.parent, bg=st.BG_CARD, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Reports System",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(side="left", padx=20, pady=14)
        tk.Frame(self.parent, bg=st.BORDER, height=1).pack(fill="x")

        nb = ttk.Notebook(self.parent)
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        t1 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t1, text="  Member Report  ")
        self._build_member_report(t1)

        t2 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t2, text="  Share Report  ")
        self._build_share_report(t2)

        t3 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t3, text="  Savings Report  ")
        self._build_savings_report(t3)

        t4 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t4, text="  Loan Report  ")
        self._build_loan_report(t4)

        t5 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t5, text="  Daily / Period Report  ")
        self._build_period_report(t5)

        t6 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t6, text="  Export  ")
        self._build_export(t6)

    # ── Member Report ─────────────────────────────────────────────────────────

    def _build_member_report(self, parent):
        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=10, pady=8)
        tk.Label(sf, text="Filter:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.mem_filter = tk.StringVar(value="All")
        ttk.Combobox(sf, textvariable=self.mem_filter,
                     values=["All", "Male", "Female", "Other",
                             "active", "inactive"],
                     state="readonly", width=12).pack(side="left", padx=8)
        ttk.Button(sf, text="🔄  Load", style="Primary.TButton",
                   command=self._load_mem_report).pack(side="left")
        ttk.Button(sf, text="📄  Export CSV", style="Info.TButton",
                   command=lambda: self._export_csv("members")).pack(side="right")

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=10)
        cols = ("No.", "Member No", "Name", "Gender", "Address",
                "Phone", "Citizenship", "Join Date", "Status", "Savings", "Loans")
        self.mem_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.mem_tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.mem_tree.xview)
        self.mem_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.mem_tree.pack(fill="both", expand=True)
        widths = [40, 90, 180, 70, 140, 110, 110, 100, 80, 110, 90]
        for col, w in zip(cols, widths):
            self.mem_tree.heading(col, text=col)
            self.mem_tree.column(col, width=w,
                                 anchor="center" if w <= 100 else "w")
        self.mem_sum = tk.StringVar()
        tk.Label(parent, textvariable=self.mem_sum,
                 font=st.FONT_SMALL, bg=st.BG_MAIN,
                 fg=st.TEXT_MUTED).pack(anchor="w", padx=10, pady=4)
        self._load_mem_report()

    def _load_mem_report(self):
        self.mem_tree.delete(*self.mem_tree.get_children())
        fil = self.mem_filter.get()
        q = "SELECT * FROM members"
        params = ()
        if fil in ("Male", "Female", "Other"):
            q += " WHERE gender=?"
            params = (fil,)
        elif fil in ("active", "inactive"):
            q += " WHERE status=?"
            params = (fil,)
        q += " ORDER BY id"
        rows = db.fetch_all(q, params)
        for i, r in enumerate(rows, 1):
            sav = (db.fetch_one(
                "SELECT COALESCE(SUM(balance),0) AS v FROM savings_accounts WHERE member_id=? AND status='active'",
                (r["id"],)) or {}).get("v", 0)
            loans = (db.fetch_one(
                "SELECT COUNT(*) AS c FROM loans WHERE member_id=? AND status='issued'",
                (r["id"],)) or {}).get("c", 0)
            tag = "even" if i % 2 == 0 else "odd"
            self.mem_tree.insert("", "end",
                                 values=(i, r["member_no"], r["full_name"],
                                         r["gender"], r["address"] or "-",
                                         r["phone"] or "-",
                                         r["citizenship_no"] or "-",
                                         r["join_date"], r["status"].upper(),
                                         f"Rs {sav:,.0f}", str(loans)),
                                 tags=(tag,))
        self.mem_tree.tag_configure("even", background=st.ALT_ROW)
        self.mem_tree.tag_configure("odd",  background=st.BG_CARD)
        self.mem_sum.set(f"Total members in report: {len(rows)}")

    # ── Share Report ──────────────────────────────────────────────────────────

    def _build_share_report(self, parent):
        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=10, pady=8)
        ttk.Button(sf, text="🔄  Load", style="Primary.TButton",
                   command=self._load_share_report).pack(side="left")
        ttk.Button(sf, text="📄  Export CSV", style="Info.TButton",
                   command=lambda: self._export_csv("shares")).pack(side="right")

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=10)
        cols = ("No.", "Member No", "Name", "Share No", "Qty",
                "Rate", "Amount", "Certificate", "Date", "Type")
        self.share_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.share_tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.share_tree.xview)
        self.share_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.share_tree.pack(fill="both", expand=True)
        widths = [40, 90, 180, 80, 60, 70, 110, 110, 100, 90]
        for col, w in zip(cols, widths):
            self.share_tree.heading(col, text=col)
            self.share_tree.column(col, width=w,
                                   anchor="center" if w <= 110 else "w")
        self.share_sum = tk.StringVar()
        tk.Label(parent, textvariable=self.share_sum,
                 font=st.FONT_SMALL, bg=st.BG_MAIN,
                 fg=st.TEXT_MUTED).pack(anchor="w", padx=10, pady=4)
        self._load_share_report()

    def _load_share_report(self):
        self.share_tree.delete(*self.share_tree.get_children())
        rows = db.fetch_all(
            """SELECT s.*, m.member_no, m.full_name
               FROM shares s JOIN members m ON s.member_id=m.id ORDER BY s.id""")
        total_qty = sum(r["quantity"] for r in rows)
        total_amt = sum(r["amount"] for r in rows)
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            self.share_tree.insert("", "end",
                                   values=(i, r["member_no"], r["full_name"],
                                           r["share_no"], r["quantity"],
                                           f"Rs {r['rate']:.0f}",
                                           f"Rs {r['amount']:,.0f}",
                                           r["certificate_no"] or "-",
                                           r["purchase_date"], r["type"].title()),
                                   tags=(tag,))
        self.share_tree.tag_configure("even", background=st.ALT_ROW)
        self.share_tree.tag_configure("odd",  background=st.BG_CARD)
        self.share_sum.set(
            f"Total Records: {len(rows)}  |  Total Shares: {total_qty}  |  Total Value: Rs {total_amt:,.0f}")

    # ── Savings Report ────────────────────────────────────────────────────────

    def _build_savings_report(self, parent):
        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=10, pady=8)
        tk.Label(sf, text="Status:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.sav_filter = tk.StringVar(value="active")
        ttk.Combobox(sf, textvariable=self.sav_filter,
                     values=["active", "closed", "All"],
                     state="readonly", width=10).pack(side="left", padx=8)
        ttk.Button(sf, text="🔄  Load", style="Primary.TButton",
                   command=self._load_sav_report).pack(side="left")
        ttk.Button(sf, text="📄  Export CSV", style="Info.TButton",
                   command=lambda: self._export_csv("savings")).pack(side="right")

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=10)
        cols = ("No.", "Account No", "Member No", "Name", "Type",
                "Balance", "Rate%", "Opened Date", "Status")
        self.sav_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.sav_tree.yview)
        self.sav_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.sav_tree.pack(fill="both", expand=True)
        widths = [40, 100, 90, 180, 100, 120, 60, 100, 80]
        for col, w in zip(cols, widths):
            self.sav_tree.heading(col, text=col)
            self.sav_tree.column(col, width=w,
                                 anchor="center" if w <= 100 else "w")
        self.sav_sum = tk.StringVar()
        tk.Label(parent, textvariable=self.sav_sum,
                 font=st.FONT_SMALL, bg=st.BG_MAIN,
                 fg=st.TEXT_MUTED).pack(anchor="w", padx=10, pady=4)
        self._load_sav_report()

    def _load_sav_report(self):
        self.sav_tree.delete(*self.sav_tree.get_children())
        fil = self.sav_filter.get()
        if fil == "All":
            rows = db.fetch_all(
                """SELECT sa.*, m.member_no, m.full_name
                   FROM savings_accounts sa JOIN members m ON sa.member_id=m.id ORDER BY sa.id""")
        else:
            rows = db.fetch_all(
                """SELECT sa.*, m.member_no, m.full_name
                   FROM savings_accounts sa JOIN members m ON sa.member_id=m.id
                   WHERE sa.status=? ORDER BY sa.id""", (fil,))
        total_bal = sum(r["balance"] for r in rows if r["status"] == "active")
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            self.sav_tree.insert("", "end",
                                 values=(i, r["account_no"], r["member_no"],
                                         r["full_name"], r["account_type"],
                                         f"Rs {r['balance']:,.2f}",
                                         f"{r['interest_rate']:.1f}%",
                                         r["opened_date"], r["status"].upper()),
                                 tags=(tag,))
        self.sav_tree.tag_configure("even", background=st.ALT_ROW)
        self.sav_tree.tag_configure("odd",  background=st.BG_CARD)
        self.sav_sum.set(
            f"Total Accounts: {len(rows)}  |  Total Active Balance: Rs {total_bal:,.2f}")

    # ── Loan Report ───────────────────────────────────────────────────────────

    def _build_loan_report(self, parent):
        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=10, pady=8)
        tk.Label(sf, text="Status:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.loan_filter = tk.StringVar(value="All")
        ttk.Combobox(sf, textvariable=self.loan_filter,
                     values=["All", "applied", "approved", "issued", "closed"],
                     state="readonly", width=12).pack(side="left", padx=8)
        ttk.Button(sf, text="🔄  Load", style="Primary.TButton",
                   command=self._load_loan_report).pack(side="left")
        ttk.Button(sf, text="📄  Export CSV", style="Info.TButton",
                   command=lambda: self._export_csv("loans")).pack(side="right")

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=10)
        cols = ("No.", "Loan No", "Member", "Type", "Applied",
                "Approved", "Rate%", "Months", "EMI",
                "Total Paid", "Outstanding", "Status")
        self.loan_rep_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.loan_rep_tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.loan_rep_tree.xview)
        self.loan_rep_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.loan_rep_tree.pack(fill="both", expand=True)
        widths = [40, 90, 160, 90, 100, 100, 60, 70, 100, 100, 110, 90]
        for col, w in zip(cols, widths):
            self.loan_rep_tree.heading(col, text=col)
            self.loan_rep_tree.column(col, width=w,
                                      anchor="center" if w <= 110 else "w")
        self.loan_sum = tk.StringVar()
        tk.Label(parent, textvariable=self.loan_sum,
                 font=st.FONT_SMALL, bg=st.BG_MAIN,
                 fg=st.TEXT_MUTED).pack(anchor="w", padx=10, pady=4)
        self._load_loan_report()

    def _load_loan_report(self):
        self.loan_rep_tree.delete(*self.loan_rep_tree.get_children())
        fil = self.loan_filter.get()
        if fil == "All":
            rows = db.fetch_all(
                """SELECT l.*, m.full_name FROM loans l
                   JOIN members m ON l.member_id=m.id ORDER BY l.id""")
        else:
            rows = db.fetch_all(
                """SELECT l.*, m.full_name FROM loans l
                   JOIN members m ON l.member_id=m.id
                   WHERE l.status=? ORDER BY l.id""", (fil,))
        total_out = sum(r["outstanding"] for r in rows if r["status"] == "issued")
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            self.loan_rep_tree.insert("", "end",
                                      values=(i, r["loan_no"], r["full_name"],
                                              r["loan_type"],
                                              f"Rs {r['applied_amount']:,.0f}",
                                              f"Rs {r['approved_amount']:,.0f}" if r["approved_amount"] else "-",
                                              f"{r['interest_rate']:.1f}%",
                                              r["duration_months"],
                                              f"Rs {r['emi']:,.0f}" if r["emi"] else "-",
                                              f"Rs {r['total_paid']:,.0f}",
                                              f"Rs {r['outstanding']:,.0f}",
                                              r["status"].upper()),
                                      tags=(tag,))
        self.loan_rep_tree.tag_configure("even", background=st.ALT_ROW)
        self.loan_rep_tree.tag_configure("odd",  background=st.BG_CARD)
        self.loan_sum.set(
            f"Total: {len(rows)} loans  |  Active Outstanding: Rs {total_out:,.0f}")

    # ── Period Report ─────────────────────────────────────────────────────────

    def _build_period_report(self, parent):
        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=10, pady=8)
        tk.Label(sf, text="From:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.pr_from = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        ttk.Entry(sf, textvariable=self.pr_from, width=12,
                  font=st.FONT_NORMAL).pack(side="left", padx=6, ipady=4)
        tk.Label(sf, text="To:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.pr_to = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(sf, textvariable=self.pr_to, width=12,
                  font=st.FONT_NORMAL).pack(side="left", padx=6, ipady=4)
        ttk.Button(sf, text="📊  Generate", style="Primary.TButton",
                   command=self._load_period).pack(side="left", padx=8)
        ttk.Button(sf, text="💾  Export TXT", style="Info.TButton",
                   command=self._export_period_txt).pack(side="left")

        self.pr_text = tk.Text(parent, font=st.FONT_MONO, bg=st.BG_CARD,
                               fg=st.TEXT_DARK, relief="solid",
                               borderwidth=1, wrap="none")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.pr_text.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.pr_text.xview)
        self.pr_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.pr_text.pack(fill="both", expand=True, padx=10)
        self._load_period()

    def _get_period_text(self):
        fr = self.pr_from.get()
        to = self.pr_to.get()
        inc_rows  = db.fetch_all(
            "SELECT category, SUM(amount) AS amt FROM daily_income WHERE income_date BETWEEN ? AND ? GROUP BY category",
            (fr, to))
        exp_rows  = db.fetch_all(
            "SELECT category, SUM(amount) AS amt FROM daily_expense WHERE expense_date BETWEEN ? AND ? GROUP BY category",
            (fr, to))
        new_mem   = (db.fetch_one("SELECT COUNT(*) AS c FROM members WHERE join_date BETWEEN ? AND ?", (fr, to)) or {}).get("c", 0)
        dep_amt   = (db.fetch_one(
            "SELECT COALESCE(SUM(amount),0) AS v FROM savings_transactions WHERE transaction_type='deposit' AND transaction_date BETWEEN ? AND ?",
            (fr, to)) or {}).get("v", 0)
        wit_amt   = (db.fetch_one(
            "SELECT COALESCE(SUM(amount),0) AS v FROM savings_transactions WHERE transaction_type='withdraw' AND transaction_date BETWEEN ? AND ?",
            (fr, to)) or {}).get("v", 0)
        loan_rep  = (db.fetch_one(
            "SELECT COALESCE(SUM(total_paid),0) AS v FROM loan_repayments WHERE payment_date BETWEEN ? AND ?",
            (fr, to)) or {}).get("v", 0)
        new_loans = (db.fetch_one("SELECT COUNT(*) AS c FROM loans WHERE application_date BETWEEN ? AND ?", (fr, to)) or {}).get("c", 0)
        shares_v  = (db.fetch_one("SELECT COALESCE(SUM(amount),0) AS v FROM shares WHERE purchase_date BETWEEN ? AND ?", (fr, to)) or {}).get("v", 0)

        total_inc = sum(r["amt"] for r in inc_rows)
        total_exp = sum(r["amt"] for r in exp_rows)

        lines = [
            "=" * 60,
            f"  PERIOD REPORT:  {fr}  to  {to}",
            "  Sahakari Cooperative Management System",
            "=" * 60,
            "",
            "  MEMBER ACTIVITY",
            "-" * 60,
            f"  New Members Joined           : {new_mem}",
            f"  New Loan Applications        : {new_loans}",
            f"  Shares Purchased Value       : Rs {shares_v:,.2f}",
            "",
            "  SAVINGS ACTIVITY",
            "-" * 60,
            f"  Total Deposits               : Rs {dep_amt:,.2f}",
            f"  Total Withdrawals            : Rs {wit_amt:,.2f}",
            f"  Net Savings Movement         : Rs {dep_amt - wit_amt:,.2f}",
            "",
            "  LOAN ACTIVITY",
            "-" * 60,
            f"  Total Repayments Received    : Rs {loan_rep:,.2f}",
            "",
            "  INCOME BREAKDOWN",
            "-" * 60,
        ]
        for r in inc_rows:
            lines.append(f"  {r['category']:<40} Rs {r['amt']:>12,.2f}")
        lines += [
            f"  {'TOTAL INCOME':<40} Rs {total_inc:>12,.2f}",
            "",
            "  EXPENSE BREAKDOWN",
            "-" * 60,
        ]
        for r in exp_rows:
            lines.append(f"  {r['category']:<40} Rs {r['amt']:>12,.2f}")
        lines += [
            f"  {'TOTAL EXPENSE':<40} Rs {total_exp:>12,.2f}",
            "",
            "=" * 60,
            f"  {'NET SURPLUS / (DEFICIT)':<40} Rs {(total_inc - total_exp):>12,.2f}",
            "=" * 60,
            "",
            f"  Generated: {datetime.now().strftime('%d %B %Y  %I:%M %p')}",
        ]
        return "\n".join(lines)

    def _load_period(self):
        text = self._get_period_text()
        self.pr_text.config(state="normal")
        self.pr_text.delete("1.0", "end")
        self.pr_text.insert("1.0", text)
        self.pr_text.config(state="disabled")

    def _export_period_txt(self):
        text = self._get_period_text()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(REPORTS_DIR, f"period_report_{ts}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Exported", f"Report saved:\n{path}", parent=self.parent)

    # ── Export Tab ────────────────────────────────────────────────────────────

    def _build_export(self, parent):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.pack(padx=30, pady=30)
        tk.Label(card, text="📤  Export Data to CSV",
                 font=st.FONT_HEADING, bg=st.BG_CARD, fg=st.PRIMARY).pack(
            anchor="w", padx=16, pady=(14, 8))
        tk.Frame(card, bg=st.BORDER, height=1).pack(fill="x", padx=16)

        info = tk.Frame(card, bg=st.ALT_ROW)
        info.pack(fill="x", padx=16, pady=10)
        tk.Label(info, text=f"📁  Export directory:  {REPORTS_DIR}",
                 font=st.FONT_SMALL, bg=st.ALT_ROW, fg=st.TEXT_MUTED).pack(
            anchor="w", padx=12, pady=8)

        exports = [
            ("👥  Members",         "members",      "Export all member records"),
            ("📊  Shares",           "shares",       "Export all share records"),
            ("💰  Savings Accounts", "savings",      "Export all savings accounts"),
            ("💸  Savings Transactions", "savings_txn", "Export savings transactions"),
            ("🏦  Loans",            "loans",        "Export all loan records"),
            ("📋  Loan Repayments",  "repayments",   "Export all repayment records"),
            ("💵  Daily Income",     "daily_income", "Export income entries"),
            ("📉  Daily Expense",    "daily_expense","Export expense entries"),
            ("📒  Journal Entries",  "journal",      "Export journal entries"),
        ]
        for label, key, desc in exports:
            row = tk.Frame(card, bg=st.BG_CARD)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=label, font=st.FONT_NORMAL,
                     bg=st.BG_CARD, fg=st.TEXT_DARK, width=24, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(side="left", padx=10)
            ttk.Button(row, text="Export CSV",
                       style="Small.TButton",
                       command=lambda k=key: self._export_csv(k)).pack(side="right")

        ttk.Button(card, text="📦  Export ALL", style="Primary.TButton",
                   command=self._export_all).pack(pady=(12, 16))

    def _export_csv(self, key):
        queries = {
            "members": (
                "SELECT member_no,full_name,gender,address,phone,citizenship_no,join_date,status FROM members",
                ["Member No", "Name", "Gender", "Address", "Phone", "Citizenship", "Join Date", "Status"]
            ),
            "shares": (
                "SELECT s.share_no, m.member_no, m.full_name, s.quantity, s.rate, s.amount, s.purchase_date, s.certificate_no, s.type FROM shares s JOIN members m ON s.member_id=m.id",
                ["Share No", "Member No", "Name", "Quantity", "Rate", "Amount", "Date", "Certificate", "Type"]
            ),
            "savings": (
                "SELECT sa.account_no, m.member_no, m.full_name, sa.account_type, sa.balance, sa.interest_rate, sa.opened_date, sa.status FROM savings_accounts sa JOIN members m ON sa.member_id=m.id",
                ["Account No", "Member No", "Name", "Type", "Balance", "Rate%", "Opened", "Status"]
            ),
            "savings_txn": (
                "SELECT st.transaction_date, sa.account_no, m.full_name, st.transaction_type, st.amount, st.balance_after, st.narration FROM savings_transactions st JOIN savings_accounts sa ON st.account_id=sa.id JOIN members m ON sa.member_id=m.id",
                ["Date", "Account No", "Name", "Type", "Amount", "Balance After", "Narration"]
            ),
            "loans": (
                "SELECT l.loan_no, m.full_name, l.loan_type, l.applied_amount, l.approved_amount, l.interest_rate, l.duration_months, l.emi, l.status, l.outstanding, l.application_date FROM loans l JOIN members m ON l.member_id=m.id",
                ["Loan No", "Name", "Type", "Applied", "Approved", "Rate%", "Months", "EMI", "Status", "Outstanding", "Applied Date"]
            ),
            "repayments": (
                "SELECT lr.payment_date, l.loan_no, m.full_name, lr.principal_paid, lr.interest_paid, lr.total_paid, lr.outstanding_balance FROM loan_repayments lr JOIN loans l ON lr.loan_id=l.id JOIN members m ON l.member_id=m.id",
                ["Date", "Loan No", "Name", "Principal", "Interest", "Total Paid", "Outstanding"]
            ),
            "daily_income": (
                "SELECT income_date, category, amount, narration, voucher_no FROM daily_income",
                ["Date", "Category", "Amount", "Narration", "Voucher"]
            ),
            "daily_expense": (
                "SELECT expense_date, category, amount, narration, voucher_no FROM daily_expense",
                ["Date", "Category", "Amount", "Narration", "Voucher"]
            ),
            "journal": (
                "SELECT entry_no, entry_date, narration, total_debit, total_credit FROM journal_entries",
                ["Entry No", "Date", "Narration", "Total Debit", "Total Credit"]
            ),
        }
        if key not in queries:
            return
        sql, headers = queries[key]
        rows = db.fetch_all(sql)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(REPORTS_DIR, f"{key}_{ts}.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                vals = [str(v).replace(",", "") if v is not None else "" for v in r.values()]
                f.write(",".join(f'"{v}"' for v in vals) + "\n")
        messagebox.showinfo("Exported",
                            f"{len(rows)} records exported to:\n{path}",
                            parent=self.parent)

    def _export_all(self):
        for key in ("members", "shares", "savings", "savings_txn",
                    "loans", "repayments", "daily_income", "daily_expense", "journal"):
            self._export_csv(key)
        messagebox.showinfo("Done",
                            f"All data exported to:\n{REPORTS_DIR}",
                            parent=self.parent)
