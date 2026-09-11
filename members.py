import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import database as db
import styles as st

# Nepali meaning for info popup
_NEPALI = "सदस्य व्यवस्थापन\n(Sadhasya Vyavasthapan)\n\nMember registration, editing,\ndocument upload and profile view."

try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False


def _info_popup(parent, title, text):
    w = tk.Toplevel(parent)
    w.title(title)
    w.resizable(False, False)
    w.configure(bg=st.BG_CARD)
    w.grab_set()
    w.update_idletasks()
    sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
    w.geometry(f"320x180+{(sw-320)//2}+{(sh-180)//2}")
    tk.Label(w, text="ℹ  " + title, font=st.FONT_SUB,
             bg=st.PRIMARY, fg=st.TEXT_LIGHT).pack(fill="x", ipady=8)
    tk.Label(w, text=text, font=("Helvetica", 11),
             bg=st.BG_CARD, fg=st.TEXT_DARK,
             justify="center", wraplength=280).pack(expand=True, pady=10)
    ttk.Button(w, text="OK", style="Primary.TButton",
               command=w.destroy).pack(pady=(0, 12))


def create_frame(parent, user):
    frame = tk.Frame(parent, bg=st.BG_MAIN)
    MembersPage(frame, user)
    return frame


class MembersPage:
    def __init__(self, parent, user):
        self.parent = parent
        self.user   = user
        self.selected_id = None
        self._build()
        self._load_members()

    def _build(self):
        hdr = tk.Frame(self.parent, bg=st.BG_CARD, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Member Management",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(side="left", padx=20, pady=14)
        ttk.Button(hdr, text="ℹ", style="Small.TButton",
                   command=lambda: _info_popup(self.parent, "Member Management", _NEPALI)
                   ).pack(side="left", pady=18)
        tk.Frame(self.parent, bg=st.BORDER, height=1).pack(fill="x")

        body = tk.Frame(self.parent, bg=st.BG_MAIN)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(body, bg=st.BG_MAIN)
        left.pack(side="left", fill="both", expand=True)

        tb = tk.Frame(left, bg=st.BG_MAIN)
        tb.pack(fill="x", pady=(0, 8))
        ttk.Button(tb, text="➕  Add Member",  style="Success.TButton",
                   command=self._add).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="✏️  Edit",         style="Primary.TButton",
                   command=self._edit).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="🗑  Delete",        style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="👁  View Profile",  style="Info.TButton",
                   command=self._view).pack(side="left", padx=(0, 6))
        ttk.Button(tb, text="🔄  Refresh",       style="Warning.TButton",
                   command=self._load_members).pack(side="right")

        sf = tk.Frame(left, bg=st.BG_MAIN)
        sf.pack(fill="x", pady=(0, 8))
        tk.Label(sf, text="Search:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN, fg=st.TEXT_DARK).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._search())
        ttk.Entry(sf, textvariable=self.search_var, width=32,
                  font=st.FONT_NORMAL).pack(side="left", padx=8, ipady=5)
        tk.Label(sf, text="Filter:", font=st.FONT_NORMAL,
                 bg=st.BG_MAIN).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        cb = ttk.Combobox(sf, textvariable=self.filter_var,
                          values=["All", "Male", "Female", "Other",
                                  "active", "inactive"],
                          width=12, state="readonly")
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self._search())

        tf = tk.Frame(left, bg=st.BG_CARD,
                      highlightbackground=st.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True)

        cols = ("No.", "Member No", "Name", "Gender", "Phone",
                "Address", "Join Date", "Status")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        widths = [40, 90, 180, 70, 110, 160, 100, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w,
                             anchor="center" if w <= 100 else "w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._view())

        self.summary_var = tk.StringVar()
        tk.Label(left, textvariable=self.summary_var,
                 font=st.FONT_SMALL, bg=st.BG_MAIN,
                 fg=st.TEXT_MUTED).pack(anchor="w", pady=(4, 0))

    def _load_members(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        if rows is None:
            rows = db.fetch_all(
                "SELECT id,member_no,full_name,gender,phone,address,"
                "join_date,status FROM members ORDER BY id DESC"
            )
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(i, r["member_no"], r["full_name"],
                                     r["gender"], r["phone"] or "-",
                                     r["address"] or "-",
                                     r["join_date"], r["status"].upper()),
                             tags=(tag,))
        self.tree.tag_configure("even", background=st.ALT_ROW)
        self.tree.tag_configure("odd",  background=st.BG_CARD)
        self.summary_var.set(f"Total: {len(rows)} members")

    def _search(self):
        q   = self.search_var.get().lower().strip()
        fil = self.filter_var.get()
        rows = db.fetch_all(
            "SELECT id,member_no,full_name,gender,phone,address,"
            "join_date,status FROM members ORDER BY id DESC"
        )
        if q:
            rows = [r for r in rows
                    if q in r["full_name"].lower()
                    or q in (r["member_no"] or "").lower()
                    or q in (r["phone"] or "").lower()
                    or q in (r["address"] or "").lower()]
        if fil != "All":
            rows = [r for r in rows
                    if r["gender"] == fil or r["status"] == fil]
        self._load_members(rows)

    def _sort(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children()]
        items.sort()
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        self.selected_id = int(sel[0]) if sel else None

    def _add(self):
        MemberForm(self.parent, None, self.user, self._load_members)

    def _edit(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a member first.")
            return
        row = db.fetch_one("SELECT * FROM members WHERE id=?",
                           (self.selected_id,))
        MemberForm(self.parent, row, self.user, self._load_members)

    def _delete(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a member first.")
            return
        row = db.fetch_one("SELECT full_name FROM members WHERE id=?",
                           (self.selected_id,))
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Mark '{row['full_name']}' as inactive?\n"
                "This does NOT delete data."):
            return
        db.execute("UPDATE members SET status='inactive' WHERE id=?",
                   (self.selected_id,))
        messagebox.showinfo("Done", "Member marked as inactive.")
        self._load_members()

    def _view(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a member first.")
            return
        row = db.fetch_one("SELECT * FROM members WHERE id=?",
                           (self.selected_id,))
        MemberProfile(self.parent, row)


# ── Member Form ────────────────────────────────────────────────────────────────

class MemberForm(tk.Toplevel):
    def __init__(self, parent, row, user, callback):
        super().__init__(parent)
        self.row      = row
        self.user     = user
        self.callback = callback
        self.is_edit  = row is not None
        self.photo_path = tk.StringVar()
        self.doc_path   = tk.StringVar()

        self.title("Edit Member" if self.is_edit else "Add New Member")
        self.resizable(True, True)
        self.configure(bg=st.BG_MAIN)
        self.grab_set()
        self._center(600, 680)
        self._build()
        if self.is_edit:
            self._populate()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tb = tk.Frame(self, bg=st.PRIMARY, height=50)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        lbl = "Edit Member" if self.is_edit else "Add New Member"
        tk.Label(tb, text=lbl, font=st.FONT_HEADING,
                 bg=st.PRIMARY, fg=st.TEXT_LIGHT).pack(
            side="left", padx=16, pady=10)

        # Scrollable content
        container = tk.Frame(self, bg=st.BG_MAIN)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg=st.BG_MAIN, highlightthickness=0)
        vsb    = ttk.Scrollbar(container, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=st.BG_MAIN)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        card = tk.Frame(inner, bg=st.BG_CARD)
        card.pack(fill="both", expand=True, padx=16, pady=12)

        self.vars = {}
        fields = [
            ("Member No",       "member_no",       not self.is_edit),
            ("Full Name *",     "full_name",        True),
            ("Gender *",        "gender",           True),
            ("Date of Birth",   "dob",              True),
            ("Address",         "address",          True),
            ("Phone *",         "phone",            True),
            ("Citizenship No",  "citizenship_no",   True),
            ("Occupation",      "occupation",       True),
            ("Join Date *",     "join_date",        True),
            ("Nominee Name",    "nominee_name",     True),
            ("Nominee Relation","nominee_relation", True),
        ]
        combobox_fields = {"gender": ["Male", "Female", "Other"]}

        for i, (label, key, enabled) in enumerate(fields):
            r, c = divmod(i, 2)
            lf = tk.Frame(card, bg=st.BG_CARD)
            lf.grid(row=r, column=c, padx=12, pady=6, sticky="ew")
            card.columnconfigure(c, weight=1)
            tk.Label(lf, text=label, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
            self.vars[key] = tk.StringVar()
            if key in combobox_fields:
                w = ttk.Combobox(lf, textvariable=self.vars[key],
                                 values=combobox_fields[key],
                                 state="readonly", font=st.FONT_NORMAL)
            else:
                state = "normal" if enabled else "readonly"
                w = ttk.Entry(lf, textvariable=self.vars[key],
                              state=state, font=st.FONT_NORMAL)
            w.pack(fill="x", ipady=5)

        if not self.is_edit:
            self.vars["member_no"].set(db.next_member_no())
            self.vars["join_date"].set(datetime.now().strftime("%Y-%m-%d"))

        # Status (edit only)
        if self.is_edit:
            sf = tk.Frame(card, bg=st.BG_CARD)
            sf.grid(row=6, column=0, columnspan=2,
                    padx=12, pady=6, sticky="ew")
            tk.Label(sf, text="Status", font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
            self.vars["status"] = tk.StringVar()
            ttk.Combobox(sf, textvariable=self.vars["status"],
                         values=["active", "inactive"],
                         state="readonly",
                         font=st.FONT_NORMAL).pack(fill="x", ipady=5)

        # ── Photo upload ──────────────────────────────────────────────
        pf = tk.Frame(card, bg=st.BG_CARD)
        pf.grid(row=7, column=0, columnspan=2,
                padx=12, pady=6, sticky="ew")
        tk.Label(pf, text="Photo (JPG/PNG)", font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
        pr = tk.Frame(pf, bg=st.BG_CARD)
        pr.pack(fill="x")
        self.photo_lbl = ttk.Entry(pr, textvariable=self.photo_path,
                                   state="readonly", font=st.FONT_SMALL)
        self.photo_lbl.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(pr, text="Browse…", style="Small.TButton",
                   command=self._browse_photo).pack(side="left", padx=6)

        # ── Document upload ───────────────────────────────────────────
        df = tk.Frame(card, bg=st.BG_CARD)
        df.grid(row=8, column=0, columnspan=2,
                padx=12, pady=6, sticky="ew")
        tk.Label(df, text="Document (Citizenship/Other PDF/Image)",
                 font=st.FONT_SMALL, bg=st.BG_CARD,
                 fg=st.TEXT_MUTED).pack(anchor="w")
        dr = tk.Frame(df, bg=st.BG_CARD)
        dr.pack(fill="x")
        self.doc_lbl = ttk.Entry(dr, textvariable=self.doc_path,
                                 state="readonly", font=st.FONT_SMALL)
        self.doc_lbl.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(dr, text="Browse…", style="Small.TButton",
                   command=self._browse_doc).pack(side="left", padx=6)

        # Buttons
        bf = tk.Frame(self, bg=st.BG_MAIN)
        bf.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(bf, text="💾  Save", style="Success.TButton",
                   command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Cancel", style="Danger.TButton",
                   command=self.destroy).pack(side="left")

    def _browse_photo(self):
        path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")])
        if path:
            self.photo_path.set(path)

    def _browse_doc(self):
        path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=[("Documents", "*.pdf *.jpg *.jpeg *.png *.bmp *.tiff"),
                       ("All files", "*.*")])
        if path:
            self.doc_path.set(path)

    def _populate(self):
        for k, v in self.vars.items():
            val = self.row.get(k, "") or ""
            v.set(str(val))
        if self.row.get("photo_path"):
            self.photo_path.set(self.row["photo_path"])
        if self.row.get("doc_path"):
            self.doc_path.set(self.row["doc_path"])

    def _save(self):
        v = {k: var.get().strip() for k, var in self.vars.items()}

        if not v.get("full_name"):
            messagebox.showerror("Validation", "Full name is required.", parent=self)
            return
        if not v.get("gender"):
            messagebox.showerror("Validation", "Gender is required.", parent=self)
            return
        if not v.get("join_date"):
            messagebox.showerror("Validation", "Join date is required.", parent=self)
            return

        # Copy uploaded files into uploads folder
        photo_dest = None
        doc_dest   = None
        raw_photo = self.photo_path.get().strip()
        raw_doc   = self.doc_path.get().strip()

        if raw_photo and os.path.isfile(raw_photo):
            # Only copy if it's not already in our uploads dir
            if db.UPLOAD_DIR not in raw_photo:
                try:
                    photo_dest = db.copy_to_uploads(
                        raw_photo, f"photo_{v.get('member_no','M')}")
                except Exception:
                    photo_dest = raw_photo
            else:
                photo_dest = raw_photo
        elif self.is_edit:
            photo_dest = self.row.get("photo_path") or None

        if raw_doc and os.path.isfile(raw_doc):
            if db.UPLOAD_DIR not in raw_doc:
                try:
                    doc_dest = db.copy_to_uploads(
                        raw_doc, f"doc_{v.get('member_no','M')}")
                except Exception:
                    doc_dest = raw_doc
            else:
                doc_dest = raw_doc
        elif self.is_edit:
            doc_dest = self.row.get("doc_path") or None

        if self.is_edit:
            db.execute(
                """UPDATE members SET full_name=?,gender=?,dob=?,address=?,phone=?,
                   citizenship_no=?,occupation=?,join_date=?,nominee_name=?,
                   nominee_relation=?,status=?,photo_path=?,doc_path=?
                   WHERE id=?""",
                (v["full_name"], v["gender"], v["dob"], v["address"],
                 v["phone"], v["citizenship_no"], v["occupation"],
                 v["join_date"], v["nominee_name"], v["nominee_relation"],
                 v.get("status", "active"), photo_dest, doc_dest,
                 self.row["id"])
            )
            messagebox.showinfo("Saved", "Member updated successfully.", parent=self)
        else:
            db.execute(
                """INSERT INTO members
                   (member_no,full_name,gender,dob,address,phone,citizenship_no,
                    occupation,join_date,nominee_name,nominee_relation,
                    photo_path,doc_path,created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (v["member_no"], v["full_name"], v["gender"], v["dob"],
                 v["address"], v["phone"], v["citizenship_no"],
                 v["occupation"], v["join_date"], v["nominee_name"],
                 v["nominee_relation"], photo_dest, doc_dest,
                 self.user["id"])
            )
            messagebox.showinfo("Saved",
                                f"Member {v['member_no']} added successfully.",
                                parent=self)
        self.callback()
        self.destroy()


# ── Member Profile ─────────────────────────────────────────────────────────────

class MemberProfile(tk.Toplevel):
    def __init__(self, parent, row):
        super().__init__(parent)
        self.row = row
        self.title(f"Member Profile – {row['full_name']}")
        self.configure(bg=st.BG_MAIN)
        self.resizable(True, True)
        self.grab_set()
        self._center(560, 640)
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        hdr = tk.Frame(self, bg=st.PRIMARY, height=100)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Photo display
        photo_path = self.row.get("photo_path") or ""
        photo_shown = False
        if _PIL and photo_path and os.path.isfile(photo_path):
            try:
                img = Image.open(photo_path).resize((72, 72))
                self._photo_img = ImageTk.PhotoImage(img)
                tk.Label(hdr, image=self._photo_img,
                         bg=st.PRIMARY).pack(side="left", padx=14, pady=14)
                photo_shown = True
            except Exception:
                pass
        if not photo_shown:
            tk.Label(hdr, text="👤", font=("Helvetica", 36),
                     bg=st.PRIMARY, fg=st.ACCENT).pack(
                side="left", padx=18, pady=12)

        ri = tk.Frame(hdr, bg=st.PRIMARY)
        ri.pack(side="left", pady=16)
        tk.Label(ri, text=self.row["full_name"], font=st.FONT_HEADING,
                 bg=st.PRIMARY, fg=st.TEXT_LIGHT).pack(anchor="w")
        tk.Label(ri, text=f"Member No: {self.row['member_no']}",
                 font=st.FONT_NORMAL, bg=st.PRIMARY,
                 fg="#b8d4f0").pack(anchor="w")
        sc = st.SUCCESS if self.row["status"] == "active" else st.DANGER
        tk.Label(ri, text=self.row["status"].upper(),
                 font=st.FONT_SMALL, bg=sc,
                 fg=st.TEXT_LIGHT, padx=8, pady=2).pack(anchor="w", pady=4)

        card = tk.Frame(self, bg=st.BG_CARD)
        card.pack(fill="both", expand=True, padx=16, pady=12)

        fields = [
            ("Gender",            self.row.get("gender") or "-"),
            ("Date of Birth",     self.row.get("dob") or "-"),
            ("Address",           self.row.get("address") or "-"),
            ("Phone",             self.row.get("phone") or "-"),
            ("Citizenship No",    self.row.get("citizenship_no") or "-"),
            ("Occupation",        self.row.get("occupation") or "-"),
            ("Join Date",         self.row.get("join_date") or "-"),
            ("Nominee",           self.row.get("nominee_name") or "-"),
            ("Nominee Relation",  self.row.get("nominee_relation") or "-"),
        ]
        for i, (label, value) in enumerate(fields):
            r, c = divmod(i, 2)
            f = tk.Frame(card, bg=st.BG_CARD)
            f.grid(row=r, column=c, padx=14, pady=7, sticky="w")
            card.columnconfigure(c, weight=1)
            tk.Label(f, text=label, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
            tk.Label(f, text=value, font=st.FONT_SUB,
                     bg=st.BG_CARD, fg=st.TEXT_DARK).pack(anchor="w")

        # Document link
        doc_path = self.row.get("doc_path") or ""
        if doc_path and os.path.isfile(doc_path):
            df = tk.Frame(card, bg=st.BG_CARD)
            df.grid(row=5, column=0, columnspan=2,
                    padx=14, pady=4, sticky="w")
            tk.Label(df, text="Document:", font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(side="left")
            tk.Label(df, text=os.path.basename(doc_path),
                     font=st.FONT_SMALL, bg=st.BG_CARD,
                     fg=st.PRIMARY, cursor="hand2").pack(
                side="left", padx=6)

        # Savings & Loans summary
        savings = db.fetch_one(
            "SELECT COALESCE(SUM(balance),0) AS total FROM savings_accounts "
            "WHERE member_id=? AND status='active'", (self.row["id"],))
        loans = db.fetch_one(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(outstanding),0) AS outs "
            "FROM loans WHERE member_id=? AND status='issued'",
            (self.row["id"],))
        sav_total = (savings or {}).get("total", 0)
        loan_cnt  = (loans or {}).get("cnt", 0)
        loan_outs = (loans or {}).get("outs", 0)

        sep = tk.Frame(card, bg=st.BORDER, height=1)
        sep.grid(row=6, column=0, columnspan=2,
                 sticky="ew", padx=14, pady=6)

        sumrow = tk.Frame(card, bg=st.BG_CARD)
        sumrow.grid(row=7, column=0, columnspan=2,
                    padx=14, pady=4, sticky="ew")
        for lbl, val, color in [
            ("Savings Balance",  f"Rs {sav_total:,.2f}", st.SUCCESS),
            ("Active Loans",     str(loan_cnt),          st.DANGER),
            ("Loan Outstanding", f"Rs {loan_outs:,.2f}", "#e67e22"),
        ]:
            cf = tk.Frame(sumrow, bg=st.ALT_ROW,
                          highlightbackground=st.BORDER, highlightthickness=1)
            cf.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(cf, text=lbl, font=st.FONT_SMALL,
                     bg=st.ALT_ROW, fg=st.TEXT_MUTED).pack(pady=(8, 2))
            tk.Label(cf, text=val, font=st.FONT_SUB,
                     bg=st.ALT_ROW, fg=color).pack(pady=(0, 8))

        ttk.Button(self, text="Close", style="Primary.TButton",
                   command=self.destroy).pack(pady=(0, 12))
