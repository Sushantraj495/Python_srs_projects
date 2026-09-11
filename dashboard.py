import tkinter as tk
from tkinter import ttk
from datetime import datetime
import database as db
import styles as st


def create_frame(parent, user):
    frame = tk.Frame(parent, bg=st.BG_MAIN)
    DashboardPage(frame, user)
    return frame


class DashboardPage:
    def __init__(self, parent, user):
        self.parent = parent
        self.user = user
        self._build()

    def _build(self):
        # Header bar
        hdr = tk.Frame(self.parent, bg=st.BG_CARD, height=60)
        hdr.pack(fill="x", padx=0)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Dashboard  –  Overview",
                 font=st.FONT_HEADING, bg=st.BG_CARD,
                 fg=st.PRIMARY).pack(side="left", padx=20, pady=16)
        now = datetime.now().strftime("%A, %d %B %Y   %I:%M %p")
        tk.Label(hdr, text=now, font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(side="right", padx=20)

        tk.Frame(self.parent, bg=st.BORDER, height=1).pack(fill="x")

        scroll_canvas = tk.Canvas(self.parent, bg=st.BG_MAIN,
                                  highlightthickness=0)
        vsb = ttk.Scrollbar(self.parent, orient="vertical",
                            command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        scroll_canvas.pack(fill="both", expand=True)

        inner = tk.Frame(scroll_canvas, bg=st.BG_MAIN)
        win_id = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(event):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        inner.bind("<Configure>", on_configure)

        def on_canvas_resize(event):
            scroll_canvas.itemconfig(win_id, width=event.width)
        scroll_canvas.bind("<Configure>", on_canvas_resize)

        self._fill(inner)

    def _fill(self, parent):
        stats = db.get_dashboard_stats()

        tk.Label(parent, text="  📊  Key Statistics",
                 font=("Helvetica", 13, "bold"),
                 bg=st.BG_MAIN, fg=st.PRIMARY).pack(anchor="w", padx=20, pady=(16, 6))

        # ── Stats cards row 1 ────────────────────────────────────────────────
        row1 = tk.Frame(parent, bg=st.BG_MAIN)
        row1.pack(fill="x", padx=20)

        cards_r1 = [
            ("Total Members", str(stats["total_members"]), "👥", st.PRIMARY),
            ("Male Members",  str(stats["male_members"]),  "♂",  "#2e86c1"),
            ("Female Members",str(stats["female_members"]),"♀",  "#8e44ad"),
            ("Share Capital",  f"Rs {stats['share_value']:,.0f}", "📜", "#16a085"),
        ]
        for i, (title, value, icon, color) in enumerate(cards_r1):
            row1.columnconfigure(i, weight=1)
            self._stat_card(row1, title, value, icon, color, i, 0)

        row2 = tk.Frame(parent, bg=st.BG_MAIN)
        row2.pack(fill="x", padx=20, pady=(10, 0))

        cards_r2 = [
            ("Total Savings",     f"Rs {stats['total_savings']:,.2f}", "💰", st.SUCCESS),
            ("Active Loans",      str(stats["active_loans"]),          "🏦", st.DANGER),
            ("Loan Outstanding",  f"Rs {stats['loan_outstanding']:,.2f}","📋", "#e67e22"),
            ("Shares Issued",     str(stats["total_shares"]),           "📊", "#2980b9"),
        ]
        for i, (title, value, icon, color) in enumerate(cards_r2):
            row2.columnconfigure(i, weight=1)
            self._stat_card(row2, title, value, icon, color, i, 0)

        # ── Today's cashflow ─────────────────────────────────────────────────
        tk.Label(parent, text="  💵  Today's Cash Flow",
                 font=("Helvetica", 13, "bold"),
                 bg=st.BG_MAIN, fg=st.PRIMARY).pack(anchor="w", padx=20, pady=(20, 6))

        cash_row = tk.Frame(parent, bg=st.BG_MAIN)
        cash_row.pack(fill="x", padx=20)
        net = stats["today_income"] - stats["today_expense"]

        for i, (title, value, color) in enumerate([
            ("Today's Income",  f"Rs {stats['today_income']:,.2f}",  st.SUCCESS),
            ("Today's Expense", f"Rs {stats['today_expense']:,.2f}", st.DANGER),
            ("Net Cash Flow",   f"Rs {net:,.2f}",                    st.PRIMARY if net >= 0 else st.DANGER),
        ]):
            cash_row.columnconfigure(i, weight=1)
            c = tk.Frame(cash_row, bg=st.BG_CARD, relief="flat",
                         highlightbackground=st.BORDER, highlightthickness=1)
            c.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            tk.Label(c, text=title, font=st.FONT_SMALL,
                     bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(pady=(14, 2))
            tk.Label(c, text=value, font=("Helvetica", 18, "bold"),
                     bg=st.BG_CARD, fg=color).pack(pady=(0, 14))

        # ── Charts ───────────────────────────────────────────────────────────
        tk.Label(parent, text="  📈  Visual Overview",
                 font=("Helvetica", 13, "bold"),
                 bg=st.BG_MAIN, fg=st.PRIMARY).pack(anchor="w", padx=20, pady=(20, 6))

        chart_row = tk.Frame(parent, bg=st.BG_MAIN)
        chart_row.pack(fill="x", padx=20, pady=(0, 20))
        chart_row.columnconfigure(0, weight=1)
        chart_row.columnconfigure(1, weight=1)

        # Member gender bar chart
        self._member_chart(chart_row, stats, 0)
        # Financial summary chart
        self._finance_chart(chart_row, stats, 1)

        # ── Recent members ───────────────────────────────────────────────────
        tk.Label(parent, text="  👥  Recent Members",
                 font=("Helvetica", 13, "bold"),
                 bg=st.BG_MAIN, fg=st.PRIMARY).pack(anchor="w", padx=20, pady=(4, 6))

        tbl_frame = tk.Frame(parent, bg=st.BG_CARD,
                             highlightbackground=st.BORDER, highlightthickness=1)
        tbl_frame.pack(fill="x", padx=20, pady=(0, 20))

        cols = ("No.", "Member No", "Name", "Gender", "Phone", "Join Date", "Status")
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=6)
        for col in cols:
            tree.heading(col, text=col)
        tree.column("No.",       width=40,  anchor="center")
        tree.column("Member No", width=90,  anchor="center")
        tree.column("Name",      width=180)
        tree.column("Gender",    width=70,  anchor="center")
        tree.column("Phone",     width=110)
        tree.column("Join Date", width=100, anchor="center")
        tree.column("Status",    width=80,  anchor="center")
        tree.pack(fill="x", padx=1, pady=1)

        rows = db.fetch_all(
            "SELECT member_no,full_name,gender,phone,join_date,status FROM members ORDER BY id DESC LIMIT 10"
        )
        for i, r in enumerate(rows, 1):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end",
                        values=(i, r["member_no"], r["full_name"], r["gender"],
                                r["phone"] or "-", r["join_date"], r["status"].upper()),
                        tags=(tag,))
        tree.tag_configure("even", background=st.ALT_ROW)
        tree.tag_configure("odd",  background=st.BG_CARD)

    def _stat_card(self, parent, title, value, icon, color, col, row_idx):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.grid(row=row_idx, column=col, padx=6, pady=4, sticky="nsew")

        top = tk.Frame(card, bg=color, height=5)
        top.pack(fill="x")

        body = tk.Frame(card, bg=st.BG_CARD)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(body, bg=st.BG_CARD)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text=title, font=st.FONT_SMALL,
                 bg=st.BG_CARD, fg=st.TEXT_MUTED).pack(anchor="w")
        tk.Label(left, text=value, font=("Helvetica", 17, "bold"),
                 bg=st.BG_CARD, fg=color).pack(anchor="w", pady=(4, 0))

        tk.Label(body, text=icon, font=("Helvetica", 26),
                 bg=st.BG_CARD, fg=color).pack(side="right", padx=8)

    def _member_chart(self, parent, stats, col):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
        tk.Label(card, text="Member Breakdown", font=st.FONT_SUB,
                 bg=st.BG_CARD, fg=st.PRIMARY).pack(pady=(12, 6))

        canvas = tk.Canvas(card, width=300, height=180,
                           bg=st.BG_CARD, highlightthickness=0)
        canvas.pack(padx=16, pady=(0, 12))

        total  = max(stats["total_members"], 1)
        male   = stats["male_members"]
        female = stats["female_members"]
        other  = stats["other_members"]

        bar_x, bar_y, bar_w = 30, 20, 60
        max_h = 130

        for idx, (label, count, color) in enumerate([
            ("Male",   male,   "#2e86c1"),
            ("Female", female, "#8e44ad"),
            ("Other",  other,  "#16a085"),
            ("Total",  total,  st.PRIMARY),
        ]):
            h   = int(max_h * count / total) if total else 4
            h   = max(h, 4)
            x   = bar_x + idx * (bar_w + 14)
            top = bar_y + max_h - h
            canvas.create_rectangle(x, top, x + bar_w, bar_y + max_h,
                                    fill=color, outline="")
            canvas.create_text(x + bar_w // 2, top - 8,
                               text=str(count), font=("Helvetica", 9, "bold"),
                               fill=st.TEXT_DARK)
            canvas.create_text(x + bar_w // 2, bar_y + max_h + 12,
                               text=label, font=("Helvetica", 8),
                               fill=st.TEXT_MUTED)

    def _finance_chart(self, parent, stats, col):
        card = tk.Frame(parent, bg=st.BG_CARD,
                        highlightbackground=st.BORDER, highlightthickness=1)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
        tk.Label(card, text="Financial Summary (Rs)", font=st.FONT_SUB,
                 bg=st.BG_CARD, fg=st.PRIMARY).pack(pady=(12, 6))

        canvas = tk.Canvas(card, width=340, height=180,
                           bg=st.BG_CARD, highlightthickness=0)
        canvas.pack(padx=16, pady=(0, 12))

        items = [
            ("Savings",   stats["total_savings"],     st.SUCCESS),
            ("Loans Out", stats["loan_outstanding"],  st.DANGER),
            ("Share Cap", stats["share_value"],       "#2980b9"),
        ]
        mx = max((v for _, v, _ in items), default=1) or 1
        bar_x, bar_y, bar_w = 40, 20, 60
        max_h = 130

        for idx, (label, value, color) in enumerate(items):
            h = int(max_h * value / mx) if mx else 4
            h = max(h, 4)
            x   = bar_x + idx * (bar_w + 28)
            top = bar_y + max_h - h
            canvas.create_rectangle(x, top, x + bar_w, bar_y + max_h,
                                    fill=color, outline="")
            display = f"{value/1000:.0f}K" if value >= 1000 else f"{value:.0f}"
            canvas.create_text(x + bar_w // 2, top - 8,
                               text=display, font=("Helvetica", 9, "bold"),
                               fill=st.TEXT_DARK)
            canvas.create_text(x + bar_w // 2, bar_y + max_h + 12,
                               text=label, font=("Helvetica", 8),
                               fill=st.TEXT_MUTED)
