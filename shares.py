import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db
import styles as st


def create_frame(parent, user):
    frame = tk.Frame(parent, bg=st.BG_MAIN)
    SharesPage(frame, user)
    return frame


class SharesPage:
    def __init__(self, parent, user):
        self.parent      = parent
        self.user        = user
        self.selected_id = None
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self.parent, bg=st.BG_CARD, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Share Management",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(side="left", padx=20, pady=14)
        tk.Frame(self.parent, bg=st.BORDER, height=1).pack(fill="x")

        nb = ttk.Notebook(self.parent)
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        tab1 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(tab1, text="  Share Records  ")
        self._build_list(tab1)

        tab2 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(tab2, text="  Purchase / Additional  ")
        self._build_purchase(tab2)

        tab3 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(tab3, text="  Transfer Shares  ")
        self._build_transfer(tab3)

        tab4 = tk.Frame(nb, bg=st.BG_MAIN)
        nb.add(tab4, text="  Member Summary  ")
        self._build_summary(tab4)

    # ── Tab 1: List ────────────────────────────────────────────────────────────

    def _build_list(self, parent):
        tb = tk.Frame(parent, bg=st.BG_MAIN)
        tb.pack(fill="x", padx=8, pady=8)
        ttk.Button(tb, text="🖨  Print Certificate", style="Primary.TButton",
                   command=self._print_cert).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="✏️  Edit Share",         style="Info.TButton",
                   command=self._edit_share).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="🔄  Refresh",             style="Warning.TButton",
                   command=self._load).pack(side="right")

        sf = tk.Frame(parent, bg=st.BG_MAIN)
        sf.pack(fill="x", padx=8, pady=(0, 6))
        tk.Label(sf, text="Search:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._search())
        ttk.Entry(sf, textvariable=self.search_var, width=30,
                  font=st.FONT_NORMAL).pack(side="left", padx=8, ipady=5)

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=8)

        cols = ("No.", "Date", "Member No", "Member Name", "Share No(s)",
                "Qty", "Rate", "Amount", "Certificate", "Type")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        widths = [40, 100, 90, 180, 100, 60, 70, 110, 110, 90]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="center" if w <= 110 else "w")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_sel())

        self.sum_var = tk.StringVar()
        tk.Label(parent, textvariable=self.sum_var,
                 font=st.FONT_SMALL, bg=st.BG_MAIN,
                 fg=st.TEXT_MUTED).pack(anchor="w", padx=8, pady=4)

    def _on_sel(self):
        sel = self.tree.selection()
        self.selected_id = int(sel[0]) if sel else None

    def _load(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        if rows is None:
            rows = db.fetch_all(
                """SELECT s.id, s.purchase_date, m.member_no, m.full_name,
                          s.share_no, s.quantity, s.rate, s.amount,
                          s.certificate_no, s.type
                   FROM shares s JOIN members m ON s.member_id=m.id
                   ORDER BY s.id DESC"""
            )
        total_qty = sum(r["quantity"] for r in rows)
        total_amt = sum(r["amount"]   for r in rows)
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            range_lbl = db.share_range_label(r["share_no"], r["quantity"])
            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(i, r["purchase_date"], r["member_no"],
                                     r["full_name"], range_lbl,
                                     r["quantity"],
                                     f"Rs {r['rate']:.0f}",
                                     f"Rs {r['amount']:,.0f}",
                                     r["certificate_no"] or "-",
                                     r["type"].title()),
                             tags=(tag,))
        self.tree.tag_configure("even", background=st.ALT_ROW)
        self.tree.tag_configure("odd",  background=st.BG_CARD)
        self.sum_var.set(
            f"Records: {len(rows)}  |  Total Shares: {total_qty}  "
            f"|  Total Amount: Rs {total_amt:,.0f}")

    def _search(self):
        q = self.search_var.get().lower().strip()
        rows = db.fetch_all(
            """SELECT s.id, s.purchase_date, m.member_no, m.full_name,
                      s.share_no, s.quantity, s.rate, s.amount,
                      s.certificate_no, s.type
               FROM shares s JOIN members m ON s.member_id=m.id
               ORDER BY s.id DESC"""
        )
        if q:
            rows = [r for r in rows
                    if q in r["full_name"].lower()
                    or q in r["member_no"].lower()
                    or q in str(r["share_no"]).lower()]
        self._load(rows)

    def _print_cert(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a share record first.")
            return
        row = db.fetch_one(
            """SELECT s.*, m.full_name, m.member_no, m.address, m.citizenship_no
               FROM shares s JOIN members m ON s.member_id=m.id WHERE s.id=?""",
            (self.selected_id,)
        )
        ShareCertificateWindow(self.parent, row)

    def _edit_share(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a share record first.")
            return
        row = db.fetch_one("SELECT * FROM shares WHERE id=?", (self.selected_id,))
        EditShareDialog(self.parent, row, self.user, self._load)

    # ── Tab 2: Purchase / Additional ──────────────────────────────────────────

    def _build_purchase(self, parent):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.pack(padx=20, pady=20, fill="x")

        tk.Label(card, text="Purchase / Additional Shares",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Frame(card, bg=st.BORDER, height=1).pack(fill="x", padx=16)

        # Info banner
        info = tk.Frame(card, bg="#e8f4fd")
        info.pack(fill="x", padx=16, pady=6)
        tk.Label(info,
                 text="ℹ  Existing members can buy additional shares — no new Member ID created.",
                 font=st.FONT_SMALL, bg="#e8f4fd", fg="#1a6ea8").pack(
            anchor="w", padx=10, pady=6)

        form = tk.Frame(card, bg=st.BG_CARD)
        form.pack(fill="x", padx=16, pady=12)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.p_vars = {}
        rows_def = [
            (0, 0, "Member No *",      "member_no",    "entry"),
            (0, 2, "Member Name",      "member_name_p","readonly"),
            (1, 0, "Start Share No",   "share_no",     "readonly"),
            (1, 2, "End Share No",     "share_no_end", "readonly"),
            (2, 0, "Quantity *",       "quantity",     "entry"),
            (2, 2, "Rate (Rs) *",      "rate",         "entry"),
            (3, 0, "Amount (Rs)",      "amount_p",     "readonly"),
            (3, 2, "Date *",           "date_p",       "entry"),
            (4, 0, "Type",             "type_p",       "combo"),
            (4, 2, "Narration",        "narration_p",  "entry"),
        ]
        for r, c, lbl, key, wtype in rows_def:
            tk.Label(form, text=lbl, font=st.FONT_NORMAL,
                     bg=st.BG_CARD, fg=st.TEXT_DARK).grid(
                row=r, column=c, sticky="w", padx=(0, 8), pady=6)
            self.p_vars[key] = tk.StringVar()
            if wtype == "combo":
                w = ttk.Combobox(form, textvariable=self.p_vars[key],
                                 values=["purchase", "additional"],
                                 state="readonly",
                                 font=st.FONT_NORMAL, width=22)
                w.set("purchase")
            elif wtype == "readonly":
                w = ttk.Entry(form, textvariable=self.p_vars[key],
                              state="readonly",
                              font=st.FONT_NORMAL, width=24)
            else:
                w = ttk.Entry(form, textvariable=self.p_vars[key],
                              font=st.FONT_NORMAL, width=24)
            w.grid(row=r, column=c + 1, sticky="ew", pady=6)

        self.p_vars["rate"].set("100")
        self.p_vars["date_p"].set(datetime.now().strftime("%Y-%m-%d"))
        self._refresh_share_no()

        self.p_vars["member_no"].trace("w", self._lookup_member_p)
        self.p_vars["quantity"].trace("w", self._calc_amount_p)
        self.p_vars["rate"].trace("w",     self._calc_amount_p)

        bf = tk.Frame(card, bg=st.BG_CARD)
        bf.pack(anchor="w", padx=16, pady=(0, 14))
        ttk.Button(bf, text="✅  Purchase / Add Shares", style="Success.TButton",
                   command=self._purchase).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="🔄  Reset", style="Warning.TButton",
                   command=self._reset_purchase).pack(side="left")

    def _refresh_share_no(self):
        sn = db.next_share_no()
        self.p_vars["share_no"].set(str(sn))
        self._calc_end_share_no()

    def _lookup_member_p(self, *_):
        mno = self.p_vars["member_no"].get().strip().upper()
        r = db.fetch_one(
            "SELECT full_name FROM members WHERE member_no=? AND status='active'",
            (mno,))
        self.p_vars["member_name_p"].set(
            r["full_name"] if r else "Not found")
        # Suggest "additional" if member already has shares
        if r:
            existing = db.fetch_one(
                """SELECT COUNT(*) AS c FROM shares s
                   JOIN members m ON s.member_id=m.id
                   WHERE m.member_no=?""", (mno,))
            if existing and existing["c"] > 0:
                self.p_vars["type_p"].set("additional")
            else:
                self.p_vars["type_p"].set("purchase")

    def _calc_amount_p(self, *_):
        try:
            qty  = int(self.p_vars["quantity"].get())
            rate = float(self.p_vars["rate"].get())
            self.p_vars["amount_p"].set(f"{qty * rate:,.2f}")
            self._calc_end_share_no()
        except Exception:
            self.p_vars["amount_p"].set("")
            self.p_vars["share_no_end"].set("")

    def _calc_end_share_no(self):
        try:
            start = int(self.p_vars["share_no"].get())
            qty   = int(self.p_vars["quantity"].get())
            if qty > 1:
                self.p_vars["share_no_end"].set(str(start + qty - 1))
            else:
                self.p_vars["share_no_end"].set(str(start))
        except Exception:
            self.p_vars["share_no_end"].set("")

    def _reset_purchase(self):
        for key in self.p_vars:
            self.p_vars[key].set("")
        self.p_vars["rate"].set("100")
        self.p_vars["date_p"].set(datetime.now().strftime("%Y-%m-%d"))
        self.p_vars["type_p"].set("purchase")
        self._refresh_share_no()

    def _purchase(self):
        v = {k: var.get().strip() for k, var in self.p_vars.items()}
        member = db.fetch_one(
            "SELECT id FROM members WHERE member_no=? AND status='active'",
            (v["member_no"].upper(),))
        if not member:
            messagebox.showerror("Error",
                                 "Member not found or inactive.",
                                 parent=self.parent)
            return
        try:
            qty  = int(v["quantity"])
            rate = float(v["rate"])
        except ValueError:
            messagebox.showerror("Error",
                                 "Invalid quantity or rate.",
                                 parent=self.parent)
            return
        if qty <= 0:
            messagebox.showerror("Error",
                                 "Quantity must be positive.",
                                 parent=self.parent)
            return

        # Re-fetch next share_no at save time to avoid race
        share_no = db.next_share_no()
        cert_no  = db.next_cert_no()
        amount   = qty * rate

        db.execute(
            """INSERT INTO shares
               (member_id,share_no,quantity,rate,amount,purchase_date,
                certificate_no,type,narration,created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (member["id"], share_no, qty, rate, amount,
             v["date_p"], cert_no,
             v["type_p"] or "purchase",
             v["narration_p"], self.user["id"])
        )
        range_lbl = db.share_range_label(share_no, qty)
        messagebox.showinfo("Success",
                            f"Shares recorded!\n"
                            f"Share No(s): {range_lbl}\n"
                            f"Certificate: {cert_no}\n"
                            f"Amount: Rs {amount:,.0f}",
                            parent=self.parent)
        self._reset_purchase()
        self._load()

    # ── Tab 3: Transfer ────────────────────────────────────────────────────────

    def _build_transfer(self, parent):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.pack(padx=20, pady=20, fill="x")
        tk.Label(card, text="Transfer Shares Between Members",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Frame(card, bg=st.BORDER, height=1).pack(fill="x", padx=16)

        form = tk.Frame(card, bg=st.BG_CARD)
        form.pack(fill="x", padx=16, pady=12)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.t_vars = {}
        fields = [
            (0, "From Member No *",       "from_no",           "entry"),
            (0, "From Name",              "from_name",          "readonly"),
            (1, "To Member No *",         "to_no",              "entry"),
            (1, "To Name",               "to_name",            "readonly"),
            (2, "Share No to Transfer *", "transfer_share_no",  "entry"),
            (2, "Date *",                "transfer_date",       "entry"),
            (3, "Narration",             "transfer_narr",       "entry"),
        ]
        for i, (r, lbl, key, wtype) in enumerate(fields):
            c = (i % 2) * 2
            tk.Label(form, text=lbl, font=st.FONT_NORMAL,
                     bg=st.BG_CARD, fg=st.TEXT_DARK).grid(
                row=r, column=c, sticky="w", padx=(0, 8), pady=6)
            self.t_vars[key] = tk.StringVar()
            state = "readonly" if wtype == "readonly" else "normal"
            ttk.Entry(form, textvariable=self.t_vars[key],
                      state=state, font=st.FONT_NORMAL,
                      width=24).grid(row=r, column=c + 1,
                                     sticky="ew", pady=6)

        self.t_vars["transfer_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.t_vars["from_no"].trace(
            "w", lambda *a: self._lookup_t("from_no", "from_name"))
        self.t_vars["to_no"].trace(
            "w", lambda *a: self._lookup_t("to_no", "to_name"))

        bf = tk.Frame(card, bg=st.BG_CARD)
        bf.pack(anchor="w", padx=16, pady=(0, 14))
        ttk.Button(bf, text="🔄  Transfer Shares",
                   style="Primary.TButton",
                   command=self._transfer).pack(side="left")

    def _lookup_t(self, key_no, key_name):
        mno = self.t_vars[key_no].get().strip().upper()
        r   = db.fetch_one(
            "SELECT full_name FROM members WHERE member_no=? AND status='active'",
            (mno,))
        self.t_vars[key_name].set(r["full_name"] if r else "Not found")

    def _transfer(self):
        v      = {k: var.get().strip() for k, var in self.t_vars.items()}
        from_m = db.fetch_one(
            "SELECT id FROM members WHERE member_no=? AND status='active'",
            (v["from_no"].upper(),))
        to_m   = db.fetch_one(
            "SELECT id FROM members WHERE member_no=? AND status='active'",
            (v["to_no"].upper(),))
        if not from_m or not to_m:
            messagebox.showerror("Error",
                                 "Invalid from/to member.",
                                 parent=self.parent)
            return
        share = db.fetch_one(
            "SELECT * FROM shares WHERE share_no=? AND member_id=?",
            (v["transfer_share_no"], from_m["id"]))
        if not share:
            messagebox.showerror("Error",
                                 "Share not found for this member.",
                                 parent=self.parent)
            return

        new_cert = db.next_cert_no()
        db.execute(
            """INSERT INTO shares
               (member_id,share_no,quantity,rate,amount,purchase_date,
                certificate_no,type,transferred_to,narration,created_by)
               VALUES (?,?,?,?,?,?,?,'transfer',?,?,?)""",
            (to_m["id"], v["transfer_share_no"], share["quantity"],
             share["rate"], share["amount"], v["transfer_date"],
             new_cert, from_m["id"], v["transfer_narr"], self.user["id"])
        )
        db.execute("DELETE FROM shares WHERE id=?", (share["id"],))
        messagebox.showinfo(
            "Success",
            f"Share {v['transfer_share_no']} transferred successfully!",
            parent=self.parent)
        self._load()

    # ── Tab 4: Summary ─────────────────────────────────────────────────────────

    def _build_summary(self, parent):
        tb = tk.Frame(parent, bg=st.BG_MAIN)
        tb.pack(fill="x", padx=8, pady=8)
        ttk.Button(tb, text="🔄  Refresh", style="Warning.TButton",
                   command=self._load_summary).pack(side="right")

        tf = tk.Frame(parent, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=8)

        cols = ("No.", "Member No", "Name", "Total Shares",
                "Total Amount", "Certificates")
        self.sum_tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical",
                            command=self.sum_tree.yview)
        self.sum_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.sum_tree.pack(fill="both", expand=True)
        widths = [40, 90, 180, 100, 120, 200]
        for col, w in zip(cols, widths):
            self.sum_tree.heading(col, text=col)
            self.sum_tree.column(col, width=w,
                                 anchor="center" if w <= 120 else "w")
        self._load_summary()

    def _load_summary(self):
        self.sum_tree.delete(*self.sum_tree.get_children())
        rows = db.fetch_all(
            """SELECT m.member_no, m.full_name,
                      SUM(s.quantity) AS total_qty,
                      SUM(s.amount)   AS total_amt,
                      GROUP_CONCAT(s.certificate_no, ', ') AS certs
               FROM shares s JOIN members m ON s.member_id=m.id
               GROUP BY s.member_id ORDER BY total_qty DESC"""
        )
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            self.sum_tree.insert(
                "", "end",
                values=(i, r["member_no"], r["full_name"],
                        r["total_qty"],
                        f"Rs {r['total_amt']:,.0f}",
                        r["certs"] or "-"),
                tags=(tag,))
        self.sum_tree.tag_configure("even", background=st.ALT_ROW)
        self.sum_tree.tag_configure("odd",  background=st.BG_CARD)


# ── Edit Share Dialog ──────────────────────────────────────────────────────────

class EditShareDialog(tk.Toplevel):
    def __init__(self, parent, row, user, callback):
        super().__init__(parent)
        self.row      = row
        self.user     = user
        self.callback = callback
        self.title(f"Edit Share Record – ID {row['id']}")
        self.resizable(False, False)
        self.configure(bg=st.BG_MAIN)
        self.grab_set()
        self._center(440, 400)
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tb = tk.Frame(self, bg=st.PRIMARY, height=46)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tk.Label(tb, text="Edit Share Record",
                 font=st.FONT_HEADING, bg=st.PRIMARY,
                 fg=st.TEXT_LIGHT).pack(side="left", padx=14, pady=8)

        card = tk.Frame(self, bg=st.BG_CARD)
        card.pack(fill="both", expand=True, padx=14, pady=10)

        self.v = {}
        fields = [
            ("Purchase Date *",  "purchase_date", False),
            ("Quantity *",       "quantity",       False),
            ("Rate (Rs) *",      "rate",           False),
            ("Amount (Rs)",      "amount",         True),
            ("Certificate No",   "certificate_no", True),
            ("Type",             "type",           False),
            ("Narration",        "narration",      False),
        ]
        for lbl, key, readonly in fields:
            f = tk.Frame(card, bg=st.BG_CARD)
            f.pack(fill="x", pady=4, padx=10)
            tk.Label(f, text=lbl, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
            self.v[key] = tk.StringVar()
            if key == "type":
                w = ttk.Combobox(f, textvariable=self.v[key],
                                 values=["purchase", "additional", "transfer"],
                                 state="readonly", font=st.FONT_NORMAL)
            else:
                state = "readonly" if readonly else "normal"
                w = ttk.Entry(f, textvariable=self.v[key],
                              state=state, font=st.FONT_NORMAL)
            w.pack(fill="x", ipady=4)

        # Populate
        for key in self.v:
            val = self.row.get(key, "") or ""
            self.v[key].set(str(val))

        self.v["quantity"].trace("w", self._recalc)
        self.v["rate"].trace("w",     self._recalc)

        bf = tk.Frame(self, bg=st.BG_MAIN)
        bf.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(bf, text="💾  Save", style="Success.TButton",
                   command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Cancel", style="Danger.TButton",
                   command=self.destroy).pack(side="left")

    def _recalc(self, *_):
        try:
            qty  = int(self.v["quantity"].get())
            rate = float(self.v["rate"].get())
            self.v["amount"].set(f"{qty * rate:.2f}")
        except Exception:
            pass

    def _save(self):
        try:
            qty  = int(self.v["quantity"].get())
            rate = float(self.v["rate"].get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or rate.", parent=self)
            return
        amount = qty * rate
        db.execute(
            """UPDATE shares SET purchase_date=?,quantity=?,rate=?,
               amount=?,type=?,narration=? WHERE id=?""",
            (self.v["purchase_date"].get(), qty, rate, amount,
             self.v["type"].get(), self.v["narration"].get(),
             self.row["id"])
        )
        messagebox.showinfo("Saved", "Share record updated.", parent=self)
        self.callback()
        self.destroy()


# ── Share Certificate Window ───────────────────────────────────────────────────

class ShareCertificateWindow(tk.Toplevel):
    """
    Landscape share certificate styled after the Nepali cooperative
    certificate reference — zigzag green border, red inner border,
    Devanagari field labels, cooperative seal watermark, signature lines.
    """

    # Colours matching the reference image
    C_GREEN_DARK  = "#1a5c1a"   # zigzag fill
    C_GREEN_MED   = "#2e7d32"   # thin lines
    C_RED         = "#c0392b"   # inner border
    C_RED2        = "#e74c3c"   # accent text
    C_GOLD        = "#b7950b"   # title accent
    C_BG          = "#ffffff"
    C_LABEL       = "#333333"
    C_MUTED       = "#666666"
    C_SEAL        = "#c8e6c9"   # pale green for watermark circle

    W, H = 820, 580             # landscape canvas size
    OUTER = 6                   # zigzag band outer edge
    TOOTH = 10                  # zigzag tooth size
    INNER1 = 24                 # first red border inset
    INNER2 = 28                 # second red border inset (double line)
    MARGIN = 36                 # content margin from edge

    def __init__(self, parent, row):
        super().__init__(parent)
        self.row = row
        self.title(f"शेयर प्रमाण-पत्र  –  {row.get('certificate_no', '')}")
        self.resizable(False, False)
        self.configure(bg="#e8e8e8")
        self.grab_set()
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(
            f"{self.W + 40}x{self.H + 80}"
            f"+{(sw - self.W - 40)//2}+{(sh - self.H - 80)//2}")

    def _build(self):
        top = tk.Frame(self, bg="#e8e8e8")
        top.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(top, text=f"शेयर प्रमाण-पत्र  |  Certificate No: {self.row.get('certificate_no','')}",
                 font=("Helvetica", 10, "bold"), bg="#e8e8e8",
                 fg="#444").pack(side="left")

        btn_row = tk.Frame(self, bg="#e8e8e8")
        btn_row.pack(fill="x", padx=14, pady=(0, 6))
        ttk.Button(btn_row, text="🖨  Print (Save as Text)",
                   style="Primary.TButton",
                   command=self._print_text).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Close",
                   style="Warning.TButton",
                   command=self.destroy).pack(side="left")

        # Canvas
        self.canvas = tk.Canvas(
            self, width=self.W, height=self.H,
            bg=self.C_BG, highlightthickness=0)
        self.canvas.pack(padx=14, pady=(0, 14))

        self._draw()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        c = self.canvas
        W, H = self.W, self.H

        # 1. White background fill
        c.create_rectangle(0, 0, W, H, fill=self.C_BG, outline="")

        # 2. Zigzag green border band
        self._draw_zigzag_border(c, 0, 0, W, H,
                                 self.TOOTH, self.C_GREEN_DARK)

        # 3. Thin green inner line just inside the zigzag
        g = self.INNER1 - 6
        c.create_rectangle(g, g, W - g, H - g,
                           outline=self.C_GREEN_MED, width=1)

        # 4. Red double border
        i1 = self.INNER1
        c.create_rectangle(i1, i1, W - i1, H - i1,
                           outline=self.C_RED, width=2)
        i2 = self.INNER2
        c.create_rectangle(i2, i2, W - i2, H - i2,
                           outline=self.C_RED, width=1)

        # 5. Cooperative watermark / seal (centred, pale green circle)
        cx, cy = W // 2, H // 2 + 20
        r_seal = 90
        c.create_oval(cx - r_seal, cy - r_seal,
                      cx + r_seal, cy + r_seal,
                      fill=self.C_SEAL, outline=self.C_GREEN_MED, width=2)
        # Inner ring
        c.create_oval(cx - r_seal + 8, cy - r_seal + 8,
                      cx + r_seal - 8, cy + r_seal - 8,
                      fill="", outline=self.C_GREEN_MED, width=1)
        # Seal text
        c.create_text(cx, cy - 28, text="सहकारी संस्था",
                      font=("Helvetica", 9, "bold"),
                      fill=self.C_GREEN_DARK, anchor="center")
        c.create_text(cx, cy, text="✦ मुद्रा ✦",
                      font=("Helvetica", 14),
                      fill=self.C_GREEN_DARK, anchor="center")
        c.create_text(cx, cy + 28, text="(Seal)",
                      font=("Helvetica", 8),
                      fill=self.C_GREEN_MED, anchor="center")

        # 6. Header section
        M = self.MARGIN
        hdr_y = M + 6

        # Organisation name (top centre)
        org_name = "सहकारी संस्था लि."
        c.create_text(W // 2, hdr_y, text=org_name,
                      font=("Helvetica", 11, "bold"),
                      fill=self.C_GREEN_DARK, anchor="center")

        # Address line
        c.create_text(W // 2, hdr_y + 18,
                      text="रजिष्ट्रेशन नं: ________  |  दर्ता मिति: ________",
                      font=("Helvetica", 8),
                      fill=self.C_MUTED, anchor="center")

        # Divider
        c.create_line(M + 20, hdr_y + 32, W - M - 20, hdr_y + 32,
                      fill=self.C_RED, width=1)

        # Main certificate title
        c.create_text(W // 2, hdr_y + 52,
                      text="शेयर प्रमाण-पत्र",
                      font=("Helvetica", 20, "bold"),
                      fill=self.C_RED2, anchor="center")
        c.create_text(W // 2, hdr_y + 74,
                      text="( Share Certificate )",
                      font=("Helvetica", 10, "italic"),
                      fill=self.C_MUTED, anchor="center")

        # Divider
        c.create_line(M + 20, hdr_y + 86, W - M - 20, hdr_y + 86,
                      fill=self.C_RED, width=1)

        # 7. Fields — two columns
        row     = self.row
        sn      = row.get("share_no", "")
        qty     = int(row.get("quantity", 1))
        sn_end  = int(sn) + qty - 1 if sn else ""
        rng_lbl = (f"{sn}" if qty == 1
                   else f"{sn} देखि {sn_end} सम्म")

        fields_left = [
            ("प्रमाण-पत्र नं.",   row.get("certificate_no") or "-"),
            ("सदस्य नं.",         row.get("member_no") or "-"),
            ("सदस्यको नाम",       row.get("full_name") or "-"),
            ("ठेगाना",            row.get("address") or "-"),
            ("नागरिकता नं.",      row.get("citizenship_no") or "-"),
        ]
        fields_right = [
            ("शेयर नं.",          rng_lbl),
            ("शेयर संख्या",       f"{qty} कित्ता"),
            ("दर (प्रति शेयर)",   f"रू. {float(row.get('rate', 100)):,.0f}"),
            ("जम्मा रकम",         f"रू. {float(row.get('amount', 0)):,.2f}"),
            ("मिति (Date)",       row.get("purchase_date") or "-"),
        ]

        field_y0  = hdr_y + 102
        line_gap  = 34
        col_l_x   = M + 10
        col_r_x   = W // 2 + 10
        val_offset = 148          # label width before value

        def draw_field(lbl, val, x, y):
            c.create_text(x, y, text=lbl + " :",
                          font=("Helvetica", 9, "bold"),
                          fill=self.C_LABEL, anchor="nw")
            # Dotted underline for value area
            dot_x1 = x + val_offset
            dot_x2 = x + val_offset + 200
            c.create_line(dot_x1, y + 16, dot_x2, y + 16,
                          fill="#aaaaaa", dash=(3, 3))
            c.create_text(dot_x1 + 4, y + 1, text=val,
                          font=("Helvetica", 9),
                          fill=self.C_GREEN_DARK, anchor="nw")

        for i, (lbl, val) in enumerate(fields_left):
            draw_field(lbl, val, col_l_x, field_y0 + i * line_gap)

        for i, (lbl, val) in enumerate(fields_right):
            draw_field(lbl, val, col_r_x, field_y0 + i * line_gap)

        # 8. Certification text
        cert_y = field_y0 + max(len(fields_left), len(fields_right)) * line_gap + 8
        cert_text = (
            "माथि उल्लिखित विवरण अनुसारका शेयर यस संस्थाको"
            "  नियमानुसार जारी गरिएको छ।"
        )
        c.create_text(W // 2, cert_y,
                      text=cert_text,
                      font=("Helvetica", 8, "italic"),
                      fill=self.C_MUTED, anchor="center")

        # 9. Signature block
        sig_y    = H - self.MARGIN - 12
        sig_lbls = [
            ("अध्यक्ष", "Chairman"),
            ("सचिव",    "Secretary"),
            ("कोषाध्यक्ष", "Treasurer"),
        ]
        seg_w = (W - 2 * M) // len(sig_lbls)
        for i, (nep, eng) in enumerate(sig_lbls):
            sx = M + i * seg_w + seg_w // 2
            # Signature line
            c.create_line(sx - 60, sig_y - 16, sx + 60, sig_y - 16,
                          fill=self.C_GREEN_DARK, width=1)
            c.create_text(sx, sig_y - 4,
                          text=nep,
                          font=("Helvetica", 9, "bold"),
                          fill=self.C_LABEL, anchor="center")
            c.create_text(sx, sig_y + 10,
                          text=f"({eng})",
                          font=("Helvetica", 8),
                          fill=self.C_MUTED, anchor="center")

        # Footer note (bottom right)
        c.create_text(W - M - 6, H - self.MARGIN + 6,
                      text="यो प्रमाण-पत्र हस्तान्तरणयोग्य छ।",
                      font=("Helvetica", 7, "italic"),
                      fill=self.C_MUTED, anchor="se")

    def _draw_zigzag_border(self, c, x0, y0, x1, y1, size, color):
        """
        Fill the outer band (0..INNER1-10) around the rectangle with
        solid-filled alternating triangles forming a zigzag/sawtooth.
        """
        band = self.INNER1 - 8   # thickness of zigzag band

        # ── Top border ───────────────────────────────────────────────
        x = x0
        up = True
        while x < x1:
            nx = min(x + size, x1)
            if up:
                # Triangle pointing down (into interior)
                c.create_polygon(
                    x, y0, nx, y0, (x + nx) // 2, y0 + band,
                    fill=color, outline=color)
            else:
                # Fill gap between triangles with solid rectangle top strip
                c.create_rectangle(x, y0, nx, y0 + band // 2,
                                   fill=color, outline=color)
            x  += size
            up  = not up

        # ── Bottom border ────────────────────────────────────────────
        x = x0
        up = True
        while x < x1:
            nx = min(x + size, x1)
            if up:
                c.create_polygon(
                    x, y1, nx, y1, (x + nx) // 2, y1 - band,
                    fill=color, outline=color)
            else:
                c.create_rectangle(x, y1 - band // 2, nx, y1,
                                   fill=color, outline=color)
            x  += size
            up  = not up

        # ── Left border ───────────────────────────────────────────────
        y = y0
        rt = True
        while y < y1:
            ny = min(y + size, y1)
            if rt:
                c.create_polygon(
                    x0, y, x0, ny, x0 + band, (y + ny) // 2,
                    fill=color, outline=color)
            else:
                c.create_rectangle(x0, y, x0 + band // 2, ny,
                                   fill=color, outline=color)
            y  += size
            rt  = not rt

        # ── Right border ──────────────────────────────────────────────
        y = y0
        lt = True
        while y < y1:
            ny = min(y + size, y1)
            if lt:
                c.create_polygon(
                    x1, y, x1, ny, x1 - band, (y + ny) // 2,
                    fill=color, outline=color)
            else:
                c.create_rectangle(x1 - band // 2, y, x1, ny,
                                   fill=color, outline=color)
            y  += size
            lt  = not lt

    # ── Print / export ────────────────────────────────────────────────────────

    def _print_text(self):
        import os
        row      = self.row
        sn       = row.get("share_no", "")
        qty      = int(row.get("quantity", 1))
        sn_end   = int(sn) + qty - 1 if sn else ""
        rng_lbl  = f"{sn}" if qty == 1 else f"{sn}-{sn_end}"

        lines = [
            "=" * 60,
            "         साझा सहकारी संस्था लि.",
            "            शेयर प्रमाण-पत्र",
            "         ( Share Certificate )",
            "=" * 60,
            f"  प्रमाण-पत्र नं.   : {row.get('certificate_no','')}",
            f"  सदस्य नं.         : {row.get('member_no','')}",
            f"  सदस्यको नाम       : {row.get('full_name','')}",
            f"  ठेगाना             : {row.get('address','')}",
            f"  नागरिकता नं.      : {row.get('citizenship_no','')}",
            "-" * 60,
            f"  शेयर नं.          : {rng_lbl}",
            f"  शेयर संख्या       : {qty} कित्ता",
            f"  दर (प्रति शेयर)   : रू. {float(row.get('rate',100)):,.0f}",
            f"  जम्मा रकम         : रू. {float(row.get('amount',0)):,.2f}",
            f"  मिति              : {row.get('purchase_date','')}",
            "=" * 60,
            "",
            "  अध्यक्ष              सचिव              कोषाध्यक्ष",
            "  ___________       ___________       ___________",
            "",
            "=" * 60,
        ]
        out_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "reports_output")
        os.makedirs(out_dir, exist_ok=True)
        cert_no = row.get("certificate_no", "CERT").replace("/", "_")
        path    = os.path.join(out_dir, f"certificate_{cert_no}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        from tkinter import messagebox as mb
        mb.showinfo("Saved",
                    f"Certificate saved as text file:\n{path}",
                    parent=self)
