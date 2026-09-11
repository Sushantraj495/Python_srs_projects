from tkinter import ttk

PRIMARY    = "#1a3a5c"
PRIMARY_LT = "#2e5f8a"
SECONDARY  = "#2e86c1"
ACCENT     = "#f39c12"
BG_MAIN    = "#eef2f7"
BG_CARD    = "#ffffff"
BG_SIDEBAR = "#1a3a5c"
BG_HEADER  = "#14304d"
TEXT_DARK  = "#1c2d3e"
TEXT_LIGHT = "#ffffff"
TEXT_MUTED = "#6c757d"
SUCCESS    = "#27ae60"
DANGER     = "#e74c3c"
WARNING    = "#f39c12"
INFO       = "#2980b9"
BORDER     = "#d0d7e2"
HOVER_NAV  = "#2e5f8a"
ALT_ROW    = "#f5f8fc"

FONT_TITLE   = ("Helvetica", 20, "bold")
FONT_HEADING = ("Helvetica", 13, "bold")
FONT_SUB     = ("Helvetica", 11, "bold")
FONT_NORMAL  = ("Helvetica", 10)
FONT_SMALL   = ("Helvetica", 9)
FONT_MONO    = ("Courier New", 10)
FONT_BIG     = ("Helvetica", 22, "bold")


def configure_styles():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("TFrame", background=BG_MAIN)
    style.configure("Card.TFrame", background=BG_CARD, relief="flat")
    style.configure("Sidebar.TFrame", background=BG_SIDEBAR)
    style.configure("Header.TFrame", background=BG_HEADER)

    style.configure("TLabel",
        background=BG_MAIN, font=FONT_NORMAL, foreground=TEXT_DARK)
    style.configure("Card.TLabel",
        background=BG_CARD, font=FONT_NORMAL, foreground=TEXT_DARK)
    style.configure("Heading.TLabel",
        background=BG_CARD, font=FONT_HEADING, foreground=PRIMARY)
    style.configure("Title.TLabel",
        background=BG_MAIN, font=FONT_TITLE, foreground=PRIMARY)
    style.configure("Muted.TLabel",
        background=BG_CARD, font=FONT_SMALL, foreground=TEXT_MUTED)
    style.configure("Header.TLabel",
        background=BG_HEADER, font=FONT_SUB, foreground=TEXT_LIGHT)
    style.configure("Sidebar.TLabel",
        background=BG_SIDEBAR, font=FONT_NORMAL, foreground=TEXT_LIGHT)
    style.configure("Success.TLabel",
        background=BG_CARD, font=FONT_SUB, foreground=SUCCESS)
    style.configure("Danger.TLabel",
        background=BG_CARD, font=FONT_SUB, foreground=DANGER)
    style.configure("Warning.TLabel",
        background=BG_CARD, font=FONT_SUB, foreground=WARNING)

    style.configure("Primary.TButton",
        background=PRIMARY, foreground=TEXT_LIGHT,
        font=FONT_SUB, padding=[14, 7], relief="flat", borderwidth=0)
    style.map("Primary.TButton",
        background=[("active", PRIMARY_LT), ("pressed", PRIMARY_LT)])

    style.configure("Success.TButton",
        background=SUCCESS, foreground=TEXT_LIGHT,
        font=FONT_SUB, padding=[14, 7], relief="flat", borderwidth=0)
    style.map("Success.TButton",
        background=[("active", "#1e8449"), ("pressed", "#1e8449")])

    style.configure("Danger.TButton",
        background=DANGER, foreground=TEXT_LIGHT,
        font=FONT_SUB, padding=[14, 7], relief="flat", borderwidth=0)
    style.map("Danger.TButton",
        background=[("active", "#c0392b"), ("pressed", "#c0392b")])

    style.configure("Warning.TButton",
        background=WARNING, foreground=TEXT_DARK,
        font=FONT_SUB, padding=[14, 7], relief="flat", borderwidth=0)
    style.map("Warning.TButton",
        background=[("active", "#e67e22"), ("pressed", "#e67e22")])

    style.configure("Info.TButton",
        background=INFO, foreground=TEXT_LIGHT,
        font=FONT_SUB, padding=[14, 7], relief="flat", borderwidth=0)
    style.map("Info.TButton",
        background=[("active", "#1a6fa3"), ("pressed", "#1a6fa3")])

    style.configure("Small.TButton",
        background=PRIMARY, foreground=TEXT_LIGHT,
        font=FONT_SMALL, padding=[8, 4], relief="flat", borderwidth=0)
    style.map("Small.TButton",
        background=[("active", PRIMARY_LT)])

    style.configure("Treeview",
        background=BG_CARD, foreground=TEXT_DARK,
        rowheight=28, fieldbackground=BG_CARD,
        font=FONT_NORMAL, borderwidth=0)
    style.configure("Treeview.Heading",
        background=PRIMARY, foreground=TEXT_LIGHT,
        font=FONT_SUB, relief="flat", padding=8)
    style.map("Treeview",
        background=[("selected", SECONDARY)],
        foreground=[("selected", TEXT_LIGHT)])
    style.map("Treeview.Heading",
        background=[("active", PRIMARY_LT)])

    style.configure("TNotebook",
        background=BG_MAIN, borderwidth=0, tabmargins=0)
    style.configure("TNotebook.Tab",
        background="#cdd6e0", foreground=TEXT_DARK,
        padding=[14, 7], font=FONT_NORMAL)
    style.map("TNotebook.Tab",
        background=[("selected", PRIMARY), ("active", PRIMARY_LT)],
        foreground=[("selected", TEXT_LIGHT), ("active", TEXT_LIGHT)])

    style.configure("TEntry",
        fieldbackground=BG_CARD, foreground=TEXT_DARK,
        font=FONT_NORMAL, padding=6, relief="solid", borderwidth=1)

    style.configure("TCombobox",
        fieldbackground=BG_CARD, background=BG_CARD,
        foreground=TEXT_DARK, font=FONT_NORMAL, padding=5)

    style.configure("TScrollbar",
        background=BORDER, troughcolor=BG_MAIN,
        borderwidth=0, relief="flat", arrowsize=13)

    style.configure("TLabelframe",
        background=BG_CARD, relief="solid",
        borderwidth=1, bordercolor=BORDER)
    style.configure("TLabelframe.Label",
        background=BG_CARD, foreground=PRIMARY, font=FONT_SUB)

    style.configure("TSeparator", background=BORDER)
    style.configure("TSpinbox",
        fieldbackground=BG_CARD, foreground=TEXT_DARK,
        font=FONT_NORMAL, padding=5)
