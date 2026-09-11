import tkinter as tk
from tkinter import ttk, messagebox
import database as db
import styles as st

_modules = {}


def load_module(name):
    if name not in _modules:
        import importlib
        _modules[name] = importlib.import_module(name)
    return _modules[name]


# ─── Forgot Password Dialog ────────────────────────────────────────────────────

MASTER_RECOVERY_CODE = "SAHAKARI@RESET"


class ForgotPasswordDialog(tk.Toplevel):
    """
    Two-path password reset:
      Tab 1 – Reset any user via admin credentials (normal use)
      Tab 2 – Emergency admin reset using master recovery code
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Forgot Password – Sahakari MIS")
        self.resizable(False, False)
        self.configure(bg=st.BG_MAIN)
        self.grab_set()
        self._center(440, 460)
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        # ── Title bar ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=st.PRIMARY, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🔑  Forgot Password",
                 font=st.FONT_HEADING, bg=st.PRIMARY,
                 fg=st.TEXT_LIGHT).pack(side="left", padx=18, pady=12)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=12)

        t1 = tk.Frame(nb, bg=st.BG_CARD)
        nb.add(t1, text="  Reset via Admin  ")
        self._build_admin_reset(t1)

        t2 = tk.Frame(nb, bg=st.BG_CARD)
        nb.add(t2, text="  Emergency Recovery  ")
        self._build_emergency(t2)

        ttk.Button(self, text="Cancel", style="Danger.TButton",
                   command=self.destroy).pack(pady=(0, 12))

    # ── Tab 1: Reset via admin ─────────────────────────────────────────────────

    def _build_admin_reset(self, parent):
        tk.Label(parent,
                 text="An admin must authorise the password reset.\n"
                      "Enter admin credentials, then set the new password.",
                 font=st.FONT_SMALL, bg=st.BG_CARD, fg=st.TEXT_MUTED,
                 justify="center", wraplength=380).pack(pady=(14, 10))

        frm = tk.Frame(parent, bg=st.BG_CARD)
        frm.pack(fill="x", padx=24)

        self.adm_u  = self._field(frm, "Admin Username")
        self.adm_pw = self._field(frm, "Admin Password", show="●")

        tk.Frame(frm, bg=st.BORDER, height=1).pack(fill="x", pady=10)

        # User to reset
        tk.Label(frm, text="User to Reset", font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
        self.target_var = tk.StringVar()
        users = db.fetch_all("SELECT username FROM users WHERE is_active=1 ORDER BY username")
        names = [u["username"] for u in users]
        cb = ttk.Combobox(frm, textvariable=self.target_var,
                          values=names, state="readonly", font=st.FONT_NORMAL)
        cb.pack(fill="x", ipady=5, pady=(2, 10))
        if names:
            cb.current(0)

        self.new_pw1 = self._field(frm, "New Password", show="●")
        self.new_pw2 = self._field(frm, "Confirm New Password", show="●")

        self.adm_err = tk.StringVar()
        tk.Label(frm, textvariable=self.adm_err, font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.DANGER).pack(pady=(4, 0))

        ttk.Button(frm, text="✅  Reset Password", style="Success.TButton",
                   command=self._do_admin_reset).pack(pady=(8, 14), fill="x")

    def _do_admin_reset(self):
        adm_username = self.adm_u.get().strip()
        adm_password = self.adm_pw.get().strip()
        target       = self.target_var.get().strip()
        new_pw       = self.new_pw1.get().strip()
        confirm_pw   = self.new_pw2.get().strip()

        if not adm_username or not adm_password:
            self.adm_err.set("Admin credentials are required.")
            return
        if not target:
            self.adm_err.set("Please select a user to reset.")
            return
        if not new_pw:
            self.adm_err.set("New password cannot be empty.")
            return
        if new_pw != confirm_pw:
            self.adm_err.set("New passwords do not match.")
            return
        if len(new_pw) < 4:
            self.adm_err.set("Password must be at least 4 characters.")
            return

        admin = db.fetch_one(
            "SELECT id, role FROM users WHERE username=? AND password=? AND is_active=1",
            (adm_username, db.hash_password(adm_password))
        )
        if not admin:
            self.adm_err.set("Invalid admin credentials.")
            return
        if admin["role"] != "admin":
            self.adm_err.set("Only an admin can reset passwords.")
            return

        db.execute(
            "UPDATE users SET password=? WHERE username=?",
            (db.hash_password(new_pw), target)
        )
        self.adm_err.set("")
        messagebox.showinfo("Success",
                            f"Password for '{target}' has been reset successfully.\n"
                            "Please log in with the new password.",
                            parent=self)
        self.destroy()

    # ── Tab 2: Emergency recovery ──────────────────────────────────────────────

    def _build_emergency(self, parent):
        tk.Label(parent,
                 text="Use this only if the admin password is lost.\n"
                      "Enter the master recovery code to reset the\n"
                      "admin account password.",
                 font=st.FONT_SMALL, bg=st.BG_CARD, fg=st.TEXT_MUTED,
                 justify="center", wraplength=380).pack(pady=(14, 6))

        hint = tk.Frame(parent, bg="#fff3cd",
                        highlightbackground="#ffc107", highlightthickness=1)
        hint.pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(hint,
                 text="⚠  Recovery code is:  SAHAKARI@RESET\n"
                      "(Keep this confidential — write it in a safe place)",
                 font=st.FONT_SMALL, bg="#fff3cd", fg="#856404",
                 justify="center").pack(pady=8)

        frm = tk.Frame(parent, bg=st.BG_CARD)
        frm.pack(fill="x", padx=24)

        self.rec_code = self._field(frm, "Master Recovery Code", show="●")
        self.rec_pw1  = self._field(frm, "New Admin Password", show="●")
        self.rec_pw2  = self._field(frm, "Confirm New Admin Password", show="●")

        self.rec_err = tk.StringVar()
        tk.Label(frm, textvariable=self.rec_err, font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.DANGER).pack(pady=(4, 0))

        ttk.Button(frm, text="🔓  Emergency Reset Admin", style="Danger.TButton",
                   command=self._do_emergency).pack(pady=(8, 14), fill="x")

    def _do_emergency(self):
        code    = self.rec_code.get().strip()
        new_pw  = self.rec_pw1.get().strip()
        confirm = self.rec_pw2.get().strip()

        if code != MASTER_RECOVERY_CODE:
            self.rec_err.set("Invalid recovery code.")
            return
        if not new_pw:
            self.rec_err.set("New password cannot be empty.")
            return
        if new_pw != confirm:
            self.rec_err.set("Passwords do not match.")
            return
        if len(new_pw) < 4:
            self.rec_err.set("Password must be at least 4 characters.")
            return

        db.execute(
            "UPDATE users SET password=? WHERE username='admin'",
            (db.hash_password(new_pw),)
        )
        self.rec_err.set("")
        messagebox.showinfo("Success",
                            "Admin password has been reset.\n"
                            "Please log in with the new password.",
                            parent=self)
        self.destroy()

    # ── Helper ────────────────────────────────────────────────────────────────

    def _field(self, parent, label, show=None):
        tk.Label(parent, text=label, font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
        var = tk.StringVar()
        kw  = {"show": show} if show else {}
        ttk.Entry(parent, textvariable=var,
                  font=st.FONT_NORMAL, **kw).pack(fill="x", ipady=5,
                                                   pady=(2, 10))
        return var


# ─── Login Window ─────────────────────────────────────────────────────────────

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sahakari MIS – Login")
        self.resizable(False, False)
        self.configure(bg=st.PRIMARY)
        self._center(420, 560)
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        outer = tk.Frame(self, bg=st.PRIMARY)
        outer.pack(fill="both", expand=True, padx=30, pady=30)

        # Logo + title
        tk.Label(outer, text="🏦", font=("Helvetica", 48),
                 bg=st.PRIMARY, fg=st.ACCENT).pack(pady=(10, 0))
        tk.Label(outer, text="Sahakari MIS",
                 font=("Helvetica", 22, "bold"),
                 bg=st.PRIMARY, fg=st.TEXT_LIGHT).pack()
        tk.Label(outer, text="Cooperative Management System",
                 font=st.FONT_SMALL, bg=st.PRIMARY,
                 fg="#a8c8e8").pack(pady=(2, 20))

        # Card
        card  = tk.Frame(outer, bg=st.BG_CARD, relief="flat")
        card.pack(fill="x")
        inner = tk.Frame(card, bg=st.BG_CARD)
        inner.pack(fill="both", padx=28, pady=28)

        # Username
        tk.Label(inner, text="Username", bg=st.BG_CARD,
                 font=st.FONT_SUB, fg=st.TEXT_DARK).pack(anchor="w")
        self.username_var = tk.StringVar(value="admin")
        e1 = ttk.Entry(inner, textvariable=self.username_var,
                       font=st.FONT_NORMAL)
        e1.pack(fill="x", pady=(2, 12), ipady=6)

        # Password row (label + show/hide toggle)
        pw_hdr = tk.Frame(inner, bg=st.BG_CARD)
        pw_hdr.pack(fill="x")
        tk.Label(pw_hdr, text="Password", bg=st.BG_CARD,
                 font=st.FONT_SUB, fg=st.TEXT_DARK).pack(side="left")

        # Password field
        self.password_var  = tk.StringVar(value="admin123")
        self._show_pw      = False
        self.e2 = ttk.Entry(inner, textvariable=self.password_var,
                            show="●", font=st.FONT_NORMAL)
        self.e2.pack(fill="x", pady=(2, 6), ipady=6)

        # Show/hide + Forgot password row
        link_row = tk.Frame(inner, bg=st.BG_CARD)
        link_row.pack(fill="x", pady=(0, 14))

        self._show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(link_row, text="Show password",
                       variable=self._show_var,
                       font=st.FONT_SMALL, bg=st.BG_CARD,
                       fg=st.TEXT_MUTED, activebackground=st.BG_CARD,
                       command=self._toggle_pw).pack(side="left")

        forgot_lbl = tk.Label(link_row, text="Forgot Password?",
                              font=(st.FONT_SMALL[0], st.FONT_SMALL[1],
                                    "underline"),
                              bg=st.BG_CARD, fg=st.PRIMARY,
                              cursor="hand2")
        forgot_lbl.pack(side="right")
        forgot_lbl.bind("<Button-1>", lambda e: self._forgot())

        # Error label
        self.error_var = tk.StringVar()
        tk.Label(inner, textvariable=self.error_var,
                 bg=st.BG_CARD, fg=st.DANGER,
                 font=st.FONT_SMALL).pack(pady=(0, 6))

        # Login button
        tk.Button(inner, text="LOGIN",
                  font=("Helvetica", 12, "bold"),
                  bg=st.PRIMARY, fg=st.TEXT_LIGHT, relief="flat",
                  activebackground=st.PRIMARY_LT,
                  activeforeground=st.TEXT_LIGHT,
                  cursor="hand2", command=self._login, pady=10
                  ).pack(fill="x")

        e1.bind("<Return>", lambda e: self.e2.focus())
        self.e2.bind("<Return>", lambda e: self._login())
        e1.focus()

        tk.Label(outer, text="Default: admin / admin123",
                 font=st.FONT_SMALL, bg=st.PRIMARY,
                 fg="#7fafd4").pack(pady=(14, 0))

    def _toggle_pw(self):
        self.e2.configure(show="" if self._show_var.get() else "●")

    def _forgot(self):
        ForgotPasswordDialog(self)

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            self.error_var.set("Please enter username and password.")
            return
        row = db.fetch_one(
            "SELECT * FROM users WHERE username=? AND password=? AND is_active=1",
            (username, db.hash_password(password))
        )
        if not row:
            self.error_var.set("Invalid credentials. Please try again.")
            return
        self.destroy()
        app = MainApp(row)
        app.mainloop()


# ─── Main Application Window ──────────────────────────────────────────────────

NAV_ITEMS = [
    ("🏠  Dashboard",        "dashboard"),
    ("👥  Members",           "members"),
    ("📊  Shares",            "shares"),
    ("💰  Savings",           "savings"),
    ("🏦  Loans",             "loans"),
    ("📒  Accounting",        "accounting"),
    ("💵  Daily Transactions", "transactions"),
    ("📄  Reports",           "reports"),
]

ADMIN_ONLY = ["accounting"]


class MainApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title("Sahakari MIS – Cooperative Management System")
        self.configure(bg=st.BG_MAIN)
        self._maximize()
        st.configure_styles()
        self._current_frame = None
        self._build()
        self._show_page("dashboard")

    def _maximize(self):
        try:
            self.state("zoomed")
        except Exception:
            self.geometry("1280x800")

    def _build(self):
        header = tk.Frame(self, bg=st.BG_HEADER, height=54)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(header, text="🏦 Sahakari MIS",
                 font=("Helvetica", 15, "bold"),
                 bg=st.BG_HEADER,
                 fg=st.TEXT_LIGHT).pack(side="left", padx=18)

        right = tk.Frame(header, bg=st.BG_HEADER)
        right.pack(side="right", padx=16)
        role_text = "Admin" if self.user["role"] == "admin" else "Staff"
        tk.Label(right,
                 text=f"👤 {self.user['full_name']}  [{role_text}]",
                 font=st.FONT_NORMAL, bg=st.BG_HEADER,
                 fg="#b8d4f0").pack(side="left")
        tk.Button(right, text="  Logout  ",
                  font=st.FONT_SMALL, bg=st.DANGER, fg=st.TEXT_LIGHT,
                  relief="flat", activebackground="#c0392b",
                  cursor="hand2",
                  command=self._logout).pack(side="left", padx=(14, 0))

        body    = tk.Frame(self, bg=st.BG_MAIN)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=st.BG_SIDEBAR, width=210)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=st.BG_SIDEBAR, height=12).pack()

        self._nav_buttons = {}
        for label, key in NAV_ITEMS:
            if key in ADMIN_ONLY and self.user["role"] != "admin":
                continue
            btn = tk.Button(
                sidebar, text=label,
                font=("Helvetica", 10),
                bg=st.BG_SIDEBAR, fg=st.TEXT_LIGHT,
                relief="flat", anchor="w", padx=16, pady=10,
                activebackground=st.HOVER_NAV,
                activeforeground=st.TEXT_LIGHT,
                cursor="hand2", bd=0,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x")
            self._nav_buttons[key] = btn

        tk.Frame(sidebar, bg=st.HOVER_NAV, height=1).pack(
            fill="x", padx=14, pady=8)
        tk.Label(sidebar, text="v1.1 © 2025 Sahakari MIS",
                 font=("Helvetica", 8), bg=st.BG_SIDEBAR,
                 fg="#4a6a8a").pack(side="bottom", pady=10)

        self.content = tk.Frame(body, bg=st.BG_MAIN)
        self.content.pack(fill="both", expand=True)

    def _show_page(self, key):
        for k, btn in self._nav_buttons.items():
            btn.configure(
                bg=st.BG_SIDEBAR if k != key else st.HOVER_NAV,
                font=("Helvetica", 10) if k != key
                else ("Helvetica", 10, "bold"))

        if self._current_frame:
            self._current_frame.destroy()
            self._current_frame = None

        mod   = load_module(key)
        frame = mod.create_frame(self.content, self.user)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            login = LoginWindow()
            login.mainloop()


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.initialize_database()
    app = LoginWindow()
    app.mainloop()
