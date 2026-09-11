import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db
import styles as st


def create_frame(parent, user):
    frame = tk.Frame(parent, bg=st.BG_MAIN)
    LoansPage(frame, user)
    return frame


class LoansPage:
    def __init__(self, parent, user):
        self.parent   = parent
        self.user     = user
        self.sel_loan = None
        self._build()

    def _build(self):
        hdr = tk.Frame(self.parent, bg=st.BG_CARD, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Loan Management",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(side="left", padx=20, pady=14)
        tk.Frame(self.parent, bg=st.BORDER, height=1).pack(fill="x")

        nb = ttk.Notebook(self.parent)
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        t1 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t1, text="  Loan Applications  ")
        self._build_list(t1)

        t2 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t2, text="  New Application  ")
        self._build_apply(t2)

        t3 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t3, text="  Repayment  ")
        self._build_repayment(t3)

        t4 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t4, text="  Repayment History  ")
        self._build_rep_history(t4)

        t5 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(t5, text="  EMI Calculator  ")
        self._build_emi_calc(t5)

    # ── Tab 1: Loan List ───────────────────────────────────────────────────────

    def _build_list(self, parent):
        tb = tk.Frame(parent, bg=st.BG_MAIN)
        tb.pack(fill="x", padx=8, pady=8)
        ttk.Button(tb, text="✅  Approve",    style="Success.TButton",
                   command=self._approve).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="💵  Issue Loan", style="Primary.TButton",
                   command=self._issue).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="👁  View",       style="Info.TButton",
                   command=self._view_loan).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="🔄  Refresh",    style="Warning.TButton",
                   command=self._load_loans).pack(side="right")

        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=8, pady=(0, 6))
        tk.Label(sf, text="Filter:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.status_filter = tk.StringVar(value="All")
        cb = ttk.Combobox(sf, textvariable=self.status_filter,
                          values=["All", "applied", "approved",
                                  "issued", "closed"],
                          state="readonly", width=12)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self._load_loans())

        tk.Label(sf, text="Search:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.loan_search = tk.StringVar()
        self.loan_search.trace("w", lambda *a: self._load_loans())
        ttk.Entry(sf, textvariable=self.loan_search, width=24,
                  font=st.FONT_NORMAL).pack(side="left", padx=8, ipady=5)

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=8)
        cols = ("No.", "Loan No", "Member", "Type", "Applied",
                "Approved", "Rate%", "Months", "EMI", "Status", "Outstanding")
        self.loan_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical",
                            command=self.loan_tree.yview)
        self.loan_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.loan_tree.pack(fill="both", expand=True)
        widths = [40, 90, 160, 90, 110, 110, 60, 70, 100, 90, 110]
        for col, w in zip(cols, widths):
            self.loan_tree.heading(col, text=col)
            self.loan_tree.column(col, width=w,
                                  anchor="center" if w <= 110 else "w")
        self.loan_tree.bind("<<TreeviewSelect>>", self._on_loan_sel)

        self.loan_sum = tk.StringVar()
        tk.Label(
            parent,
            textvariable=self.loan_sum,
            font=st.FONT_SMALL,
            bg=st.BG_MAIN,
            fg=st.TEXT_MUTED
        ).pack(anchor="w", padx=8, pady=4)

        self._load_loans()
    def _on_loan_sel(self, _=None):
        sel           = self.loan_tree.selection()
        self.sel_loan = sel[0] if sel else None

    def _load_loans(self):
        self.loan_tree.delete(*self.loan_tree.get_children())
        fil = (self.status_filter.get()
               if hasattr(self, "status_filter") else "All")
        q   = (self.loan_search.get().lower().strip()
               if hasattr(self, "loan_search") else "")
        rows = db.fetch_all(
            """SELECT l.id, l.loan_no, m.full_name, l.loan_type,
                      l.applied_amount, l.approved_amount, l.interest_rate,
                      l.duration_months, l.emi, l.status,
                      COALESCE(l.outstanding,0) AS outstanding
               FROM loans l JOIN members m ON l.member_id=m.id
               ORDER BY l.id DESC"""
        )
        if fil != "All":
            rows = [r for r in rows if r["status"] == fil]
        if q:
            rows = [r for r in rows
                    if q in r["full_name"].lower()
                    or q in r["loan_no"].lower()]
        active_out = sum(r["outstanding"] for r in rows
                         if r["status"] == "issued")
        for i, r in enumerate(rows, 1):
            sc = {"applied": "odd", "approved": "approved",
                  "issued": "issued", "closed": "closed"}.get(
                r["status"], "odd")
            appr = (f"Rs {r['approved_amount']:,.0f}"
                    if r["approved_amount"] else "-")
            emi  = (f"Rs {r['emi']:,.0f}"
                    if r["emi"] else "-")
            self.loan_tree.insert(
                "", "end", iid=r["loan_no"],
                values=(i, r["loan_no"], r["full_name"],
                        r["loan_type"],
                        f"Rs {r['applied_amount']:,.0f}",
                        appr,
                        f"{r['interest_rate']:.1f}%",
                        r["duration_months"],
                        emi,
                        r["status"].upper(),
                        f"Rs {r['outstanding']:,.0f}"),
                tags=(sc,))
        self.loan_tree.tag_configure("odd",      background=st.BG_CARD)
        self.loan_tree.tag_configure("approved", background="#eafaf1")
        self.loan_tree.tag_configure("issued",   background="#fef9e7")
        self.loan_tree.tag_configure("closed",   background="#f2f3f4")
        self.loan_sum.set(
            f"Total: {len(rows)} loans  |  "
            f"Active Outstanding: Rs {active_out:,.0f}")

    def _approve(self):
        if not self.sel_loan:
            messagebox.showwarning("Select", "Please select a loan first.")
            return
        loan = db.fetch_one(
            "SELECT * FROM loans WHERE loan_no=?", (self.sel_loan,))
        if not loan or loan["status"] != "applied":
            messagebox.showwarning("Warning",
                                   "Only 'Applied' loans can be approved.")
            return
        ApproveDialog(self.parent, loan, self.user, self._load_loans)

    def _issue(self):
        if not self.sel_loan:
            messagebox.showwarning("Select", "Please select a loan first.")
            return
        loan = db.fetch_one(
            "SELECT * FROM loans WHERE loan_no=?", (self.sel_loan,))
        if not loan or loan["status"] != "approved":
            messagebox.showwarning("Warning",
                                   "Only 'Approved' loans can be issued.")
            return
        amt = loan["approved_amount"] or loan["applied_amount"]
        if not messagebox.askyesno(
                "Confirm Issue",
                f"Issue loan {self.sel_loan}?\n"
                f"Amount: Rs {amt:,.0f}"):
            return
        today = datetime.now().strftime("%Y-%m-%d")
        db.execute(
            "UPDATE loans SET status='issued', issue_date=?, "
            "outstanding=? WHERE loan_no=?",
            (today, amt, self.sel_loan)
        )
        messagebox.showinfo("Success",
                            f"Loan {self.sel_loan} issued successfully!")
        self._load_loans()

    def _view_loan(self):
        if not self.sel_loan:
            messagebox.showwarning("Select", "Please select a loan first.")
            return
        loan = db.fetch_one(
            """SELECT l.*, m.full_name, m.member_no, m.phone, m.address
               FROM loans l JOIN members m ON l.member_id=m.id
               WHERE l.loan_no=?""", (self.sel_loan,))
        LoanDetailWindow(self.parent, loan)

    # ── Tab 2: Apply ───────────────────────────────────────────────────────────

    def _build_apply(self, parent):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.pack(padx=20, pady=16, fill="x")
        tk.Label(card, text="New Loan Application",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Frame(card, bg=st.BORDER, height=1).pack(fill="x", padx=16)

        form = tk.Frame(card, bg=st.BG_CARD)
        form.pack(fill="x", padx=16, pady=12)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.app_vars = {}
        flds = [
            (0, 0, "Member No *",        "app_mno",       "entry"),
            (0, 2, "Member Name",         "app_mname",     "readonly"),
            (1, 0, "Loan Type *",         "app_type",      "combo"),
            (1, 2, "Applied Amount *",    "app_amount",    "entry"),
            (2, 0, "Interest Rate % *",   "app_rate",      "entry"),
            (2, 2, "Duration (Months) *", "app_months",    "entry"),
            (3, 0, "EMI (Auto)",          "app_emi",       "readonly"),
            (3, 2, "Purpose",             "app_purpose",   "entry"),
            (4, 0, "Collateral",          "app_collateral","entry"),
            (4, 2, "Application Date *",  "app_date",      "entry"),
        ]
        for r, c, lbl, key, wtype in flds:
            tk.Label(form, text=lbl, font=st.FONT_NORMAL,
                     bg=st.BG_CARD, fg=st.TEXT_DARK).grid(
                row=r, column=c, sticky="w", padx=(0, 8), pady=6)
            self.app_vars[key] = tk.StringVar()
            if wtype == "combo":
                w = ttk.Combobox(
                    form, textvariable=self.app_vars[key],
                    values=["Personal", "Business", "Agriculture",
                            "Education", "Home", "Vehicle"],
                    state="readonly", font=st.FONT_NORMAL, width=22)
                w.set("Personal")
            elif wtype == "readonly":
                w = ttk.Entry(form, textvariable=self.app_vars[key],
                              state="readonly", font=st.FONT_NORMAL, width=24)
            else:
                w = ttk.Entry(form, textvariable=self.app_vars[key],
                              font=st.FONT_NORMAL, width=24)
            w.grid(row=r, column=c + 1, sticky="ew", pady=6)

        self.app_vars["app_rate"].set("12")
        self.app_vars["app_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.app_vars["app_mno"].trace("w",    self._lookup_app_member)
        self.app_vars["app_amount"].trace("w", self._calc_app_emi)
        self.app_vars["app_rate"].trace("w",   self._calc_app_emi)
        self.app_vars["app_months"].trace("w", self._calc_app_emi)

        bf = tk.Frame(card, bg=st.BG_CARD)
        bf.pack(anchor="w", padx=16, pady=(0, 14))
        ttk.Button(bf, text="📝  Submit Application",
                   style="Primary.TButton",
                   command=self._submit_application).pack(
            side="left", padx=(0, 8))
        ttk.Button(bf, text="🔄  Reset", style="Warning.TButton",
                   command=self._reset_apply).pack(side="left")

    def _lookup_app_member(self, *_):
        mno = self.app_vars["app_mno"].get().strip().upper()
        r   = db.fetch_one(
            "SELECT full_name FROM members WHERE member_no=? AND status='active'",
            (mno,))
        self.app_vars["app_mname"].set(
            r["full_name"] if r else "Not found")

    def _calc_app_emi(self, *_):
        try:
            amt    = float(self.app_vars["app_amount"].get().replace(",", ""))
            rate   = float(self.app_vars["app_rate"].get())
            months = int(self.app_vars["app_months"].get())
            emi    = db.calculate_emi(amt, rate, months)
            self.app_vars["app_emi"].set(f"{emi:,.2f}")
        except Exception:
            self.app_vars["app_emi"].set("")

    def _reset_apply(self):
        for k, v in self.app_vars.items():
            v.set("")
        self.app_vars["app_rate"].set("12")
        self.app_vars["app_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.app_vars["app_type"].set("Personal")

    def _submit_application(self):
        v = {k: var.get().strip() for k, var in self.app_vars.items()}
        member = db.fetch_one(
            "SELECT id FROM members WHERE member_no=? AND status='active'",
            (v["app_mno"].upper(),))
        if not member:
            messagebox.showerror("Error", "Member not found.",
                                 parent=self.parent)
            return
        try:
            amount = float(v["app_amount"].replace(",", ""))
            rate   = float(v["app_rate"])
            months = int(v["app_months"])
        except ValueError:
            messagebox.showerror("Error",
                                 "Invalid amount / rate / months.",
                                 parent=self.parent)
            return
        if amount <= 0 or rate < 0 or months <= 0:
            messagebox.showerror("Error",
                                 "Amount and months must be positive.",
                                 parent=self.parent)
            return
        if not v["app_date"]:
            messagebox.showerror("Error", "Application date is required.",
                                 parent=self.parent)
            return

        emi     = db.calculate_emi(amount, rate, months)
        loan_no = db.next_loan_no()
        db.execute(
            """INSERT INTO loans
               (loan_no,member_id,loan_type,applied_amount,interest_rate,
                duration_months,emi,purpose,collateral,application_date,
                created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (loan_no, member["id"], v["app_type"], amount, rate,
             months, emi, v["app_purpose"], v["app_collateral"],
             v["app_date"], self.user["id"])
        )
        messagebox.showinfo(
            "Success",
            f"Loan application submitted!\n"
            f"Loan No: {loan_no}\n"
            f"EMI: Rs {emi:,.2f}",
            parent=self.parent)
        self._reset_apply()
        self._load_loans()

    # ── Tab 3: Repayment ───────────────────────────────────────────────────────

    def _build_repayment(self, parent):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.pack(padx=20, pady=16, fill="x")
        tk.Label(card, text="Record Loan Repayment",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Frame(card, bg=st.BORDER, height=1).pack(fill="x", padx=16)

        form = tk.Frame(card, bg=st.BG_CARD)
        form.pack(fill="x", padx=16, pady=12)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.rep_vars = {}
        flds = [
            (0, 0, "Loan No *",        "rep_lno",   "entry"),
            (0, 2, "Member Name",      "rep_mname", "readonly"),
            (1, 0, "Outstanding",      "rep_out",   "readonly"),
            (1, 2, "EMI Amount",       "rep_emi",   "readonly"),
            (2, 0, "Principal Paid *", "rep_prin",  "entry"),
            (2, 2, "Interest Paid *",  "rep_int",   "entry"),
            (3, 0, "Total Payment",    "rep_total", "readonly"),
            (3, 2, "Payment Date *",   "rep_date",  "entry"),
            (4, 0, "Narration",        "rep_narr",  "entry"),
        ]
        for r, c, lbl, key, wtype in flds:
            tk.Label(form, text=lbl, font=st.FONT_NORMAL,
                     bg=st.BG_CARD, fg=st.TEXT_DARK).grid(
                row=r, column=c, sticky="w", padx=(0, 8), pady=6)
            self.rep_vars[key] = tk.StringVar()
            state = "readonly" if wtype == "readonly" else "normal"
            ttk.Entry(form, textvariable=self.rep_vars[key],
                      state=state, font=st.FONT_NORMAL,
                      width=24).grid(row=r, column=c + 1,
                                     sticky="ew", pady=6)

        self.rep_vars["rep_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.rep_vars["rep_lno"].trace("w",  self._lookup_loan)
        self.rep_vars["rep_prin"].trace("w", self._calc_total)
        self.rep_vars["rep_int"].trace("w",  self._calc_total)

        bf = tk.Frame(card, bg=st.BG_CARD)
        bf.pack(anchor="w", padx=16, pady=(0, 14))
        ttk.Button(bf, text="✅  Record Repayment",
                   style="Success.TButton",
                   command=self._record_repayment).pack(
            side="left", padx=(0, 8))
        ttk.Button(bf, text="🔄  Reset", style="Warning.TButton",
                   command=self._reset_rep).pack(side="left")

    def _lookup_loan(self, *_):
        lno = self.rep_vars["rep_lno"].get().strip().upper()
        r   = db.fetch_one(
            """SELECT l.outstanding, l.emi, m.full_name
               FROM loans l JOIN members m ON l.member_id=m.id
               WHERE l.loan_no=? AND l.status='issued'""", (lno,))
        if r:
            self.rep_vars["rep_mname"].set(r["full_name"])
            self.rep_vars["rep_out"].set(
                f"Rs {r['outstanding']:,.2f}")
            self.rep_vars["rep_emi"].set(
                f"Rs {r['emi']:,.2f}" if r["emi"] else "-")
            # Auto-fill principal from outstanding (up to EMI)
            emi = r["emi"] or 0
            out = r["outstanding"] or 0
            if emi > 0:
                # Split EMI into principal + interest approx
                monthly_rate = 0.0
                loan_full = db.fetch_one(
                    "SELECT interest_rate FROM loans WHERE loan_no=?",
                    (lno,))
                if loan_full:
                    monthly_rate = loan_full["interest_rate"] / 12 / 100
                interest_portion = round(out * monthly_rate, 2)
                principal_portion = round(min(emi - interest_portion, out), 2)
                self.rep_vars["rep_int"].set(str(max(interest_portion, 0)))
                self.rep_vars["rep_prin"].set(str(max(principal_portion, 0)))
        else:
            for k in ("rep_mname", "rep_out", "rep_emi",
                      "rep_prin", "rep_int", "rep_total"):
                self.rep_vars[k].set("" if k != "rep_mname" else "Not found")

    def _calc_total(self, *_):
        try:
            p = float(
                self.rep_vars["rep_prin"].get().replace(",", "") or 0)
            i = float(
                self.rep_vars["rep_int"].get().replace(",", "") or 0)
            self.rep_vars["rep_total"].set(f"{p + i:,.2f}")
        except Exception:
            self.rep_vars["rep_total"].set("")

    def _reset_rep(self):
        for k, v in self.rep_vars.items():
            v.set("")
        self.rep_vars["rep_date"].set(datetime.now().strftime("%Y-%m-%d"))

    def _record_repayment(self):
        v   = {k: var.get().strip() for k, var in self.rep_vars.items()}
        lno = v["rep_lno"].upper()

        if not lno:
            messagebox.showerror("Error", "Loan No is required.",
                                 parent=self.parent)
            return

        # Re-fetch loan atomically to get current outstanding
        loan = db.fetch_one(
            "SELECT * FROM loans WHERE loan_no=? AND status='issued'", (lno,))
        if not loan:
            messagebox.showerror(
                "Error",
                "Loan not found or not in 'Issued' status.",
                parent=self.parent)
            return

        try:
            prin  = float(v["rep_prin"].replace(",", ""))
            inter = float(v["rep_int"].replace(",", ""))
        except ValueError:
            messagebox.showerror("Error", "Invalid amount.", parent=self.parent)
            return

        if prin < 0 or inter < 0:
            messagebox.showerror("Error",
                                 "Principal and interest cannot be negative.",
                                 parent=self.parent)
            return
        if prin == 0 and inter == 0:
            messagebox.showerror("Error",
                                 "At least one of principal or interest must be > 0.",
                                 parent=self.parent)
            return

        current_out = loan["outstanding"] or 0
        if prin > current_out + 0.005:
            messagebox.showerror(
                "Error",
                f"Principal paid (Rs {prin:,.2f}) exceeds outstanding "
                f"(Rs {current_out:,.2f}).",
                parent=self.parent)
            return

        total    = round(prin + inter, 2)
        new_out  = round(max(current_out - prin, 0), 2)
        new_paid = round((loan["total_paid"] or 0) + total, 2)

        db.execute_atomic([
            (
                "UPDATE loans SET outstanding=?, total_paid=? WHERE loan_no=?",
                (new_out, new_paid, lno)
            ),
            (
                """INSERT INTO loan_repayments
                   (loan_id,payment_date,principal_paid,interest_paid,
                    total_paid,outstanding_balance,narration,created_by)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (loan["id"], v["rep_date"], prin, inter, total,
                 new_out, v["rep_narr"], self.user["id"])
            ),
        ])

        if new_out <= 0.005:
            db.execute(
                "UPDATE loans SET status='closed' WHERE loan_no=?", (lno,))
            messagebox.showinfo(
                "Loan Closed",
                f"Repayment recorded. Loan {lno} is now FULLY PAID.\n"
                f"Total Paid: Rs {total:,.2f}",
                parent=self.parent)
        else:
            messagebox.showinfo(
                "Success",
                f"Repayment recorded.\n"
                f"Paid: Rs {total:,.2f}\n"
                f"Remaining Outstanding: Rs {new_out:,.2f}",
                parent=self.parent)

        self._reset_rep()
        self._load_loans()
        self._load_rep_history(all_r=True)

    # ── Tab 4: Repayment History ───────────────────────────────────────────────

    def _build_rep_history(self, parent):
        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=8, pady=8)
        tk.Label(sf, text="Loan No:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.rhist_var = tk.StringVar()
        ttk.Entry(sf, textvariable=self.rhist_var, width=16,
                  font=st.FONT_NORMAL).pack(side="left", padx=8, ipady=5)
        ttk.Button(sf, text="🔍  Load", style="Primary.TButton",
                   command=lambda: self._load_rep_history()).pack(side="left")
        ttk.Button(sf, text="All", style="Info.TButton",
                   command=lambda: self._load_rep_history(
                       all_r=True)).pack(side="left", padx=8)

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=8)
        cols = ("No.", "Loan No", "Member", "Date", "Principal",
                "Interest", "Total Paid", "Outstanding", "Narration")
        self.rhist_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical",
                            command=self.rhist_tree.yview)
        self.rhist_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.rhist_tree.pack(fill="both", expand=True)
        widths = [40, 90, 160, 100, 100, 100, 100, 110, 160]
        for col, w in zip(cols, widths):
            self.rhist_tree.heading(col, text=col)
            self.rhist_tree.column(col, width=w,
                                   anchor="center" if w <= 110 else "w")
        self._load_rep_history(all_r=True)

    def _load_rep_history(self, all_r=False):
        self.rhist_tree.delete(*self.rhist_tree.get_children())
        lno = (self.rhist_var.get().strip().upper()
               if hasattr(self, "rhist_var") and not all_r else "")
        if lno:
            rows = db.fetch_all(
                """SELECT lr.*, l.loan_no, m.full_name
                   FROM loan_repayments lr
                   JOIN loans l ON lr.loan_id=l.id
                   JOIN members m ON l.member_id=m.id
                   WHERE l.loan_no=? ORDER BY lr.id DESC""", (lno,))
        else:
            rows = db.fetch_all(
                """SELECT lr.*, l.loan_no, m.full_name
                   FROM loan_repayments lr
                   JOIN loans l ON lr.loan_id=l.id
                   JOIN members m ON l.member_id=m.id
                   ORDER BY lr.id DESC LIMIT 300""")
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            self.rhist_tree.insert(
                "", "end",
                values=(i, r["loan_no"], r["full_name"],
                        r["payment_date"],
                        f"Rs {r['principal_paid']:,.2f}",
                        f"Rs {r['interest_paid']:,.2f}",
                        f"Rs {r['total_paid']:,.2f}",
                        f"Rs {r['outstanding_balance']:,.2f}",
                        r["narration"] or "-"),
                tags=(tag,))
        self.rhist_tree.tag_configure("even", background=st.ALT_ROW)
        self.rhist_tree.tag_configure("odd",  background=st.BG_CARD)

    # ── Tab 5: EMI Calculator ──────────────────────────────────────────────────

    def _build_emi_calc(self, parent):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.pack(padx=30, pady=30)
        tk.Label(card, text="📊  EMI / Loan Calculator",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Frame(card, bg=st.BORDER, height=1).pack(fill="x", padx=16)

        form = tk.Frame(card, bg=st.BG_CARD)
        form.pack(padx=16, pady=12)
        self.emi_vars = {}
        flds = [
            ("Loan Amount (Rs)",    "principal"),
            ("Annual Interest (%)", "rate"),
            ("Duration (Months)",   "months"),
        ]
        for lbl, key in flds:
            row = tk.Frame(form, bg=st.BG_CARD)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=lbl, width=24, anchor="w",
                     font=st.FONT_NORMAL, bg=st.BG_CARD).pack(side="left")
            self.emi_vars[key] = tk.StringVar()
            ttk.Entry(row, textvariable=self.emi_vars[key],
                      width=20, font=st.FONT_NORMAL).pack(
                side="left", ipady=5)

        ttk.Button(card, text="📊  Calculate EMI",
                   style="Primary.TButton",
                   command=self._calc_emi).pack(pady=12)

        self.emi_result = tk.Frame(card, bg=st.ALT_ROW)
        self.emi_result.pack(fill="x", padx=16, pady=(0, 16))

    def _calc_emi(self):
        try:
            principal = float(
                self.emi_vars["principal"].get().replace(",", ""))
            rate   = float(self.emi_vars["rate"].get())
            months = int(self.emi_vars["months"].get())
        except ValueError:
            messagebox.showerror("Error",
                                 "Please enter valid numbers.",
                                 parent=self.parent)
            return
        if principal <= 0 or months <= 0 or rate < 0:
            messagebox.showerror("Error",
                                 "Values must be positive.",
                                 parent=self.parent)
            return

        for w in self.emi_result.winfo_children():
            w.destroy()

        emi           = db.calculate_emi(principal, rate, months)
        total_payment = round(emi * months, 2)
        total_interest = round(total_payment - principal, 2)

        results = [
            ("Monthly EMI",      f"Rs {emi:,.2f}"),
            ("Total Payment",    f"Rs {total_payment:,.2f}"),
            ("Total Interest",   f"Rs {total_interest:,.2f}"),
            ("Principal",        f"Rs {principal:,.2f}"),
        ]
        for lbl, val in results:
            row = tk.Frame(self.emi_result, bg=st.ALT_ROW)
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=lbl, font=st.FONT_NORMAL,
                     bg=st.ALT_ROW, fg=st.TEXT_MUTED,
                     width=20, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=st.FONT_SUB,
                     bg=st.ALT_ROW, fg=st.PRIMARY).pack(side="left")

        # Amortisation preview (first 6 rows)
        tk.Label(self.emi_result,
                 text="Amortisation Preview (first 6 months):",
                 font=st.FONT_SMALL, bg=st.ALT_ROW,
                 fg=st.TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 2))
        hdr = tk.Frame(self.emi_result, bg=st.PRIMARY)
        hdr.pack(fill="x", padx=12)
        for txt in ("Month", "Principal", "Interest", "Balance"):
            tk.Label(hdr, text=txt, font=st.FONT_SMALL,
                     bg=st.PRIMARY, fg=st.TEXT_LIGHT,
                     width=12, anchor="center").pack(side="left")

        bal = principal
        monthly_rate = rate / 12 / 100
        for m in range(1, min(months + 1, 7)):
            interest_m  = round(bal * monthly_rate, 2)
            principal_m = round(emi - interest_m, 2)
            bal         = round(max(bal - principal_m, 0), 2)
            bg = st.ALT_ROW if m % 2 == 0 else st.BG_CARD
            ar = tk.Frame(self.emi_result, bg=bg)
            ar.pack(fill="x", padx=12)
            for val in (str(m),
                        f"Rs {principal_m:,.2f}",
                        f"Rs {interest_m:,.2f}",
                        f"Rs {bal:,.2f}"):
                tk.Label(ar, text=val, font=st.FONT_SMALL,
                         bg=bg, fg=st.TEXT_DARK,
                         width=12, anchor="center").pack(side="left")


# ── Approve Dialog ─────────────────────────────────────────────────────────────

class ApproveDialog(tk.Toplevel):
    def __init__(self, parent, loan, user, callback):
        super().__init__(parent)
        self.loan     = loan
        self.user     = user
        self.callback = callback
        self.title(f"Approve Loan – {loan['loan_no']}")
        self.resizable(False, False)
        self.configure(bg=st.BG_MAIN)
        self.grab_set()
        self._center(380, 280)
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tb = tk.Frame(self, bg=st.SUCCESS, height=46)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tk.Label(tb, text=f"Approve Loan – {self.loan['loan_no']}",
                 font=st.FONT_HEADING, bg=st.SUCCESS,
                 fg=st.TEXT_LIGHT).pack(side="left", padx=14, pady=8)

        card = tk.Frame(self, bg=st.BG_CARD)
        card.pack(fill="both", expand=True, padx=14, pady=10)

        tk.Label(card,
                 text=f"Applied Amount: Rs {self.loan['applied_amount']:,.0f}",
                 font=st.FONT_NORMAL, bg=st.BG_CARD,
                 fg=st.TEXT_DARK).pack(anchor="w", padx=10, pady=8)

        self.v = {}
        flds = [
            ("Approved Amount *", "approved_amount", False),
            ("Approval Date *",   "approved_date",   False),
            ("Remarks",           "remarks",          False),
        ]
        for lbl, key, readonly in flds:
            f = tk.Frame(card, bg=st.BG_CARD)
            f.pack(fill="x", pady=4, padx=10)
            tk.Label(f, text=lbl, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
            self.v[key] = tk.StringVar()
            ttk.Entry(f, textvariable=self.v[key],
                      font=st.FONT_NORMAL).pack(fill="x", ipady=4)

        self.v["approved_amount"].set(
            str(self.loan["applied_amount"]))
        self.v["approved_date"].set(
            datetime.now().strftime("%Y-%m-%d"))

        bf = tk.Frame(self, bg=st.BG_MAIN)
        bf.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(bf, text="✅  Approve",
                   style="Success.TButton",
                   command=self._approve).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Cancel", style="Danger.TButton",
                   command=self.destroy).pack(side="left")

    def _approve(self):
        try:
            amt = float(self.v["approved_amount"].get().replace(",", ""))
        except ValueError:
            messagebox.showerror("Error", "Invalid approved amount.", parent=self)
            return
        if amt <= 0:
            messagebox.showerror("Error", "Approved amount must be > 0.", parent=self)
            return
        if not self.v["approved_date"].get().strip():
            messagebox.showerror("Error", "Approval date is required.", parent=self)
            return

        db.execute(
            """UPDATE loans SET status='approved', approved_amount=?,
               approved_date=?, approved_by=? WHERE loan_no=?""",
            (amt, self.v["approved_date"].get(),
             self.user["id"], self.loan["loan_no"])
        )
        messagebox.showinfo("Approved",
                            f"Loan {self.loan['loan_no']} approved for "
                            f"Rs {amt:,.0f}.",
                            parent=self)
        self.callback()
        self.destroy()


# ── Loan Detail Window ─────────────────────────────────────────────────────────

class LoanDetailWindow(tk.Toplevel):
    def __init__(self, parent, loan):
        super().__init__(parent)
        self.loan = loan
        self.title(f"Loan Detail – {loan['loan_no']}")
        self.configure(bg=st.BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._center(500, 560)
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        hdr = tk.Frame(self, bg=st.PRIMARY, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"🏦  {self.loan['loan_no']}",
                 font=st.FONT_HEADING, bg=st.PRIMARY,
                 fg=st.TEXT_LIGHT).pack(side="left", padx=16, pady=12)
        sc = st.SUCCESS if self.loan["status"] == "closed" else st.ACCENT
        tk.Label(hdr, text=self.loan["status"].upper(),
                 font=st.FONT_SMALL, bg=sc,
                 fg=st.TEXT_LIGHT, padx=8, pady=4).pack(
            side="right", padx=16, pady=16)

        card = tk.Frame(self, bg=st.BG_CARD)
        card.pack(fill="both", expand=True, padx=14, pady=12)

        fields = [
            ("Member",          self.loan.get("full_name") or "-"),
            ("Member No",       self.loan.get("member_no") or "-"),
            ("Phone",           self.loan.get("phone") or "-"),
            ("Loan Type",       self.loan.get("loan_type") or "-"),
            ("Applied Amount",  f"Rs {self.loan.get('applied_amount',0):,.2f}"),
            ("Approved Amount", f"Rs {self.loan.get('approved_amount') or 0:,.2f}"),
            ("Interest Rate",   f"{self.loan.get('interest_rate',0):.1f}% p.a."),
            ("Duration",        f"{self.loan.get('duration_months',0)} months"),
            ("EMI",             f"Rs {self.loan.get('emi') or 0:,.2f}"),
            ("Purpose",         self.loan.get("purpose") or "-"),
            ("Collateral",      self.loan.get("collateral") or "-"),
            ("Applied On",      self.loan.get("application_date") or "-"),
            ("Approved On",     self.loan.get("approved_date") or "-"),
            ("Issued On",       self.loan.get("issue_date") or "-"),
            ("Total Paid",      f"Rs {self.loan.get('total_paid') or 0:,.2f}"),
            ("Outstanding",     f"Rs {self.loan.get('outstanding') or 0:,.2f}"),
        ]
        for i, (lbl, val) in enumerate(fields):
            r, c = divmod(i, 2)
            f = tk.Frame(card, bg=st.BG_CARD)
            f.grid(row=r, column=c, padx=12, pady=5, sticky="w")
            card.columnconfigure(c, weight=1)
            tk.Label(f, text=lbl, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
            tk.Label(f, text=val, font=st.FONT_SUB,
                     bg=st.BG_CARD, fg=st.TEXT_DARK).pack(anchor="w")

        ttk.Button(self, text="Close", style="Primary.TButton",
                   command=self.destroy).pack(pady=(0, 12))
