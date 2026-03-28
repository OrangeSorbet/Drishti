# main.py — Drishti Media Studio
# Entry point. Run: python main.py
# Build: pyinstaller --onefile --windowed --icon=assets/icon.ico main.py
from pathlib import Path
import tkinter as tk
import sys
import os

# ── ensure bundled paths work under PyInstaller ────────────────────────────
if getattr(sys, "frozen", False):
    # Running as a PyInstaller bundle
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

os.chdir(_BASE)

# ── TkinterDnD2 optional bootstrap ────────────────────────────────────────
# If tkinterdnd2 is installed, use it as the root Tk class for drag-and-drop
try:
    import tkinterdnd2 as _tkdnd
    _ROOT_CLS = _tkdnd.Tk
except ImportError:
    _ROOT_CLS = None

# ── Dark title-bar on Windows ─────────────────────────────────────────────
def _apply_dark_titlebar(win):
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass

def main():
    if _ROOT_CLS is not None:
        import ui.mainscreen as _ms
        _ms.MainScreen.__bases__ = (_ROOT_CLS,)

    from ui.mainscreen import MainScreen

    # ── ICON SETUP ─────────────────────────────
    app = MainScreen()
    app.withdraw()

    BASE_DIR = Path(_BASE)
    icon_ico = BASE_DIR / "assets" / "drishti.ico"
    icon_png = BASE_DIR / "assets" / "logo.png"

    try:
        app.iconbitmap(default=str(icon_ico))
    except:
        pass

    try:
        icon_img = tk.PhotoImage(file=icon_png)
        app.iconphoto(True, icon_img)
        app._icon_img = icon_img
    except:
        pass

    app.deiconify()
    # ──────────────────────────────────────────

    _apply_dark_titlebar(app)
    app.mainloop()

if __name__ == "__main__":
    main()