"""Optional MIT-licensed ttkbootstrap native theme on top of existing Tkinter.

The preview remains usable without this cosmetic package (e.g. during offline
source tests), but owner EXE builds pin and bundle it for consistent UX.
No browser shell or new package-install backend is introduced.
"""
from tkinter import ttk


def install_theme(root):
    """Attach the pinned ttkbootstrap theme to the existing Tk root."""
    engine = "tkinter-ttk"
    try:
        import ttkbootstrap
        ttkbootstrap.Style(theme="bootstrap-dark")
        engine = "ttkbootstrap-2.2.6"
    except ImportError:
        ttk.Style(root).theme_use("clam")
    style = ttk.Style(root)
    style.configure("HamApp.Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(15, 11))
    style.configure("HamApp.Secondary.TButton", font=("Segoe UI", 10), padding=(12, 9))
    style.configure("HamApp.Treeview", font=("Segoe UI", 10), rowheight=30)
    style.configure("HamApp.Treeview.Heading", font=("Segoe UI", 10, "bold"))
    return engine
