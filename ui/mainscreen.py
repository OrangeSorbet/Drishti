# ui/mainscreen.py — Root window, navigation, drag-and-drop overlay

import tkinter as tk
from pathlib import Path
from typing import Optional

from ui.theme import *
from ui.components import BreathingBackground, _rounded_rect

# Lazy imports to avoid circular deps
_CatalogueScreen = None
_ProductScreen   = None


def _get_catalogue():
    global _CatalogueScreen
    if _CatalogueScreen is None:
        from ui.catalogue import CatalogueScreen
        _CatalogueScreen = CatalogueScreen
    return _CatalogueScreen


def _get_product():
    global _ProductScreen
    if _ProductScreen is None:
        from ui.product import ProductScreen
        _ProductScreen = ProductScreen
    return _ProductScreen


class MainScreen(tk.Tk):
    """Root Tk window for Drishti."""

    APP_NAME = "Drishti"
    WIDTH    = 960
    HEIGHT   = 720

    def __init__(self):
        super().__init__()
        self.title(self.APP_NAME)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(820, 600)
        self.configure(bg=BG_DARK)

        # Centre on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self.WIDTH)  // 2
        y  = (sh - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self._current_screen: Optional[tk.Frame] = None
        self._drop_overlay:   Optional[tk.Frame] = None
        self._build_root()
        self._setup_dnd()
        self._show_home()

    # ─────────────────────────────────────────────────────────────────────────
    #  Root layout
    # ─────────────────────────────────────────────────────────────────────────
    def _build_root(self):
        # Breathing gradient background canvas
        self._bg_canvas = BreathingBackground(self)
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Header bar
        self._header = _HeaderBar(self)
        self._header.place(relx=0, rely=0, relwidth=1)
        self._header.lift()

        # Content area (below header)
        self._content = tk.Frame(self, bg=BG_DARK)
        self._content.place(relx=0, rely=0, relwidth=1, relheight=1,
                             y=_HeaderBar.HEIGHT)

    # ─────────────────────────────────────────────────────────────────────────
    #  Screen navigation
    # ─────────────────────────────────────────────────────────────────────────
    def _show_home(self):
        self._switch_to(
            _get_catalogue()(self._content,
                              on_select=self._show_product)
        )

    def _show_product(self, mode: str, media_type: str):
        ps = _get_product()(self._content, mode=mode,
                             on_back=self._show_home)
        self._switch_to(ps)

    def _switch_to(self, frame: tk.Frame):
        if self._current_screen:
            self._current_screen.destroy()
        self._current_screen = frame
        frame.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  Drag & drop
    # ─────────────────────────────────────────────────────────────────────────
    def _setup_dnd(self):
        try:
            # tkinterdnd2 if available
            import tkinterdnd2  # noqa
            self._setup_dnd_tkdnd()
        except ImportError:
            # Fall back to basic file path entry hint only
            pass

    def _setup_dnd_tkdnd(self):
        """Wire up TkinterDnD2 drag-and-drop if installed."""
        from tkinterdnd2 import DND_FILES
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
        self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        self.dnd_bind("<<Drop>>",       self._on_drop)

    def _on_drag_enter(self, event=None):
        self._show_drop_overlay()

    def _on_drag_leave(self, event=None):
        self._hide_drop_overlay()

    def _on_drop(self, event=None):
        self._hide_drop_overlay()
        if event is None: return
        data = event.data.strip().strip("{}")
        # extract first file path
        paths = self.tk.splitlist(event.data) if hasattr(event, "data") else []
        if not paths:
            paths = [data]
        path = paths[0].strip()
        if path and self._current_screen:
            if hasattr(self._current_screen, "accept_drop"):
                self._current_screen.accept_drop(path)
            else:
                # Navigate to best product screen first
                from logic.media_info import detect_type
                mtype = detect_type(path)
                ps = _get_product()(self._content, mode="upscale",
                                     on_back=self._show_home)
                self._switch_to(ps)
                ps.accept_drop(path)

    def _show_drop_overlay(self):
        if self._drop_overlay: return
        ov = _DropOverlay(self)
        ov.place(relx=0, rely=0, relwidth=1, relheight=1)
        ov.lift()
        self._drop_overlay = ov

    def _hide_drop_overlay(self):
        if self._drop_overlay:
            self._drop_overlay.destroy()
            self._drop_overlay = None


# ─────────────────────────────────────────────────────────────────────────────
#  Header bar
# ─────────────────────────────────────────────────────────────────────────────
class _HeaderBar(tk.Frame):
    HEIGHT = 80

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_ELEVATED,
                          height=self.HEIGHT, **kw)
        self.pack_propagate(False)

        inner = tk.Frame(self, bg=BG_ELEVATED)
        inner.pack(fill="both", expand=True, padx=PAD, pady=0)

        # Logo / wordmark
        logo_fr = tk.Frame(inner, bg=BG_ELEVATED)
        logo_fr.pack(side="left", pady=8)

        # Logo
        BASE_DIR = Path(__file__).resolve().parents[1]
        logo_path = BASE_DIR / "assets" / "logo.png"

        logo_img = tk.PhotoImage(file=logo_path).subsample(20, 20)

        tk.Label(logo_fr, image=logo_img, bg=BG_ELEVATED)\
            .pack(side="left", padx=(0,8), pady=4)

        self.logo_img = logo_img  # IMPORTANT: prevent garbage collection

        tk.Label(logo_fr, text="Drishti",
                 font=("Helvetica Neue",20,"bold"),
                 fg=TEXT_PRIMARY, bg=BG_ELEVATED
                 ).pack(side="left")
        tk.Label(logo_fr, text="  media studio",
                 font=("Helvetica Neue",11),
                 fg=TEXT_MUTED, bg=BG_ELEVATED
                 ).pack(side="left", pady=4)

        # Divider at bottom of header
        div = tk.Canvas(self, height=1, bg=BG_ELEVATED,
                         highlightthickness=0)
        div.pack(side="bottom", fill="x")
        div.bind("<Configure>",
                 lambda e: div.create_line(0,0,e.width,0, fill=BORDER))


# ─────────────────────────────────────────────────────────────────────────────
#  Drop overlay
# ─────────────────────────────────────────────────────────────────────────────
class _DropOverlay(tk.Canvas):
    """Full-screen dotted-border drop target with animated message."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_DARK,
                          highlightthickness=0, **kw)
        self._alpha_step = 0
        self._draw_static()
        self._pulse()

    def _draw_static(self):
        self.delete("all")
        w = self.winfo_reqwidth()  or 960
        h = self.winfo_reqheight() or 720
        if w < 100: w = 960
        if h < 100: h = 720

        # Semi-transparent overlay
        self.create_rectangle(0, 0, w, h,
                               fill=BG_DARK, stipple="gray50", outline="")

        # Dotted rounded rectangle (dashes)
        pad = 40
        self.create_rectangle(pad, pad, w-pad, h-pad,
                               outline=ACCENT, width=2, dash=(10,8))

        # Icon
        self.create_text(w//2, h//2 - 60,
                          text="⬇",
                          font=("Helvetica Neue", 64),
                          fill=ACCENT)
        # Main message
        self.create_text(w//2, h//2 + 20,
                          text="Drop it like it's hot",
                          font=("Helvetica Neue", 28, "bold"),
                          fill=TEXT_PRIMARY)
        # Sub message
        self.create_text(w//2, h//2 + 60,
                          text="Drop any media file to get started",
                          font=("Helvetica Neue", 14),
                          fill=TEXT_SECONDARY)

    def _pulse(self):
        """Pulse the border colour."""
        self._alpha_step = (self._alpha_step + 1) % 60
        t   = self._alpha_step / 60
        import math
        s   = 0.5 + 0.5 * math.sin(t * 2 * math.pi)
        # interpolate ACCENT brightness
        r   = int(0x7c + (0xff - 0x7c) * s)
        g   = int(0x6a + (0x9d - 0x6a) * s)
        b   = int(0xf7 + (0xff - 0xf7) * s)
        col = f"#{r:02x}{g:02x}{b:02x}"
        try:
            self.itemconfig("pulse_border", outline=col)
        except Exception:
            pass
        self.after(40, self._pulse)

    def _draw_dashed_rect(self, x1, y1, x2, y2, dash, color, width, tag):
        self.create_rectangle(x1, y1, x2, y2,
                               outline=color, width=width,
                               dash=dash, tags=tag)