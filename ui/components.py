# ui/components.py — Reusable styled widgets for Drishti

import tkinter as tk
from tkinter import ttk
from ui.theme import *


# ─────────────────────────────────────────────────────────────────────────────
#  Rounded-rectangle button (canvas-based, iOS pill aesthetic)
# ─────────────────────────────────────────────────────────────────────────────
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=180, height=44,
                 radius=14, bg_color=ACCENT, text_color=TEXT_PRIMARY,
                 font=FONT_SUBHEAD, hover_color=None, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"] if "bg" in parent.keys() else BG_DARK,
                         highlightthickness=0, **kw)
        self._text      = text
        self._command   = command
        self._radius    = radius
        self._bg        = bg_color
        self._hover     = hover_color or _lighten(bg_color)
        self._fg        = text_color
        self._font      = font
        self._width         = width
        self._height         = height
        self._pressed   = False
        self._draw(self._bg)
        self.bind("<Enter>",         self._on_enter)
        self.bind("<Leave>",         self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, color):
        self.delete("all")
        r, w, h = self._radius, self._width, self._height
        _rounded_rect(self, 1, 1, w-1, h-1, r, fill=color, outline="")
        self.create_text(w//2, h//2, text=self._text,
                         fill=self._fg, font=self._font)

    def _on_enter(self, _):
        self._draw(self._hover)
        self.config(cursor="hand2")

    def _on_leave(self, _):
        self._draw(self._bg)

    def _on_press(self, _):
        self._pressed = True
        self._draw(_darken(self._bg))

    def _on_release(self, _):
        if self._pressed:
            self._pressed = False
            self._draw(self._hover)
            if self._command:
                self._command()

    def configure_text(self, text):
        self._text = text
        self._draw(self._bg)


# ─────────────────────────────────────────────────────────────────────────────
#  Outlined ghost button
# ─────────────────────────────────────────────────────────────────────────────
class GhostButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=160, height=40,
                 radius=12, border_color=ACCENT, text_color=ACCENT,
                 font=FONT_BODY, **kw):
        bg = parent["bg"] if "bg" in parent.keys() else BG_DARK
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, **kw)
        self._text   = text
        self._cmd    = command
        self._r      = radius
        self._bc     = border_color
        self._fc     = text_color
        self._font   = font
        self._width      = width
        self._height      = height
        self._bg     = bg
        self._draw(False)
        self.bind("<Enter>",           lambda _: self._draw(True))
        self.bind("<Leave>",           lambda _: self._draw(False))
        self.bind("<ButtonRelease-1>", lambda _: command() if command else None)

    def _draw(self, hovered):
        self.delete("all")
        fill = BG_HOVER if hovered else self._bg
        _rounded_rect(self, 1, 1, self._width-1, self._height-1, self._r,
                      fill=fill, outline=self._bc, width=1)
        self.create_text(self._width//2, self._height//2, text=self._text,
                         fill=self._fc, font=self._font)


# ─────────────────────────────────────────────────────────────────────────────
#  Labelled slider with editable entry
# ─────────────────────────────────────────────────────────────────────────────
class LabelledSlider(tk.Frame):
    """A slider + label + optional editable textbox combination."""
    def __init__(self, parent, label, from_, to, initial=None,
                 steps=None, unit="", resolution=1,
                 on_change=None, show_entry=True, width=320, **kw):
        super().__init__(parent, bg=BG_CARD, **kw)
        self._from    = from_
        self._to      = to
        self._unit    = unit
        self._steps   = steps
        self._cb      = on_change

        # label row
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=4)
        tk.Label(top, text=label, font=FONT_SMALL, fg=TEXT_SECONDARY,
                 bg=BG_CARD).pack(side="left")
        self._val_lbl = tk.Label(top, text="", font=FONT_SMALL,
                                 fg=ACCENT_BRIGHT, bg=BG_CARD)
        self._val_lbl.pack(side="right")

        # slider
        self._var = tk.DoubleVar(value=initial if initial is not None
                                 else (from_+to)/2)
        style = ttk.Style()
        style.configure("Drishti.Horizontal.TScale",
                        background=BG_CARD, troughcolor=BG_ELEVATED,
                        sliderlength=18)
        self._slider = ttk.Scale(self, from_=from_, to=to,
                                 orient="horizontal",
                                 variable=self._var,
                                 style="Drishti.Horizontal.TScale",
                                 length=width,
                                 command=self._on_slide)
        self._slider.pack(padx=4, pady=(2, 4))

        # optional min/max markers
        mark_fr = tk.Frame(self, bg=BG_CARD)
        mark_fr.pack(fill="x", padx=4)
        tk.Label(mark_fr, text=f"{from_}{unit}", font=("Helvetica Neue",9),
                 fg=TEXT_MUTED, bg=BG_CARD).pack(side="left")
        tk.Label(mark_fr, text=f"{to}{unit}", font=("Helvetica Neue",9),
                 fg=TEXT_MUTED, bg=BG_CARD).pack(side="right")

        self._on_slide(None)

    def _on_slide(self, _):
        raw = self._var.get()
        if self._steps:
            # snap to nearest allowed step
            nearest = min(self._steps, key=lambda x: abs(x - raw))
            raw = nearest
            self._var.set(raw)
        self._val_lbl.config(text=f"{self._fmt(raw)}{self._unit}")
        if self._cb:
            self._cb(raw)

    def _fmt(self, v):
        return int(v) if v == int(v) else f"{v:.2f}"

    def get(self):
        return self._var.get()

    def set(self, v):
        self._var.set(v)
        self._on_slide(None)


# ─────────────────────────────────────────────────────────────────────────────
#  Media info panel (read-only key/value display)
# ─────────────────────────────────────────────────────────────────────────────
class MediaInfoPanel(tk.Frame):
    def __init__(self, parent, title="Media Info", **kw):
        super().__init__(parent, bg=BG_ELEVATED,
                         highlightbackground=BORDER,
                         highlightthickness=1, **kw)
        tk.Label(self, text=title, font=FONT_SUBHEAD,
                 fg=TEXT_SECONDARY, bg=BG_ELEVATED).pack(anchor="w", padx=12, pady=(10,4))
        self._rows: dict[str, tk.Label] = {}
        self._frame = tk.Frame(self, bg=BG_ELEVATED)
        self._frame.pack(fill="x", padx=12, pady=(0,10))

    def set_field(self, key: str, value: str):
        if key not in self._rows:
            row = tk.Frame(self._frame, bg=BG_ELEVATED)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=key+":", font=FONT_SMALL,
                     fg=TEXT_MUTED, bg=BG_ELEVATED, width=14,
                     anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", font=FONT_MONO,
                           fg=TEXT_PRIMARY, bg=BG_ELEVATED, anchor="w")
            lbl.pack(side="left")
            self._rows[key] = lbl
        self._rows[key].config(text=value or "—")

    def clear(self):
        for lbl in self._rows.values():
            lbl.config(text="—")


# ─────────────────────────────────────────────────────────────────────────────
#  Tabbed container (Rookie / Novice / Veteran)
# ─────────────────────────────────────────────────────────────────────────────
class ModeTabs(tk.Frame):
    TABS = ["🎮  Rookie", "🗡️  Novice", "⚔️  Veteran"]

    def __init__(self, parent, on_change=None, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._active  = 0
        self._cb      = on_change
        self._btns    = []
        bar = tk.Frame(self, bg=BG_ELEVATED)
        bar.pack(fill="x")
        for i, label in enumerate(self.TABS):
            btn = tk.Label(bar, text=label, font=FONT_BODY,
                           fg=TEXT_SECONDARY, bg=BG_ELEVATED,
                           padx=18, pady=10, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda _, idx=i: self._select(idx))
            self._btns.append(btn)
        self._pages: list[tk.Frame] = []
        for _ in self.TABS:
            pg = tk.Frame(self, bg=BG_DARK)
            self._pages.append(pg)
        self._select(0)

    def _select(self, idx):
        self._active = idx
        for i, (btn, pg) in enumerate(zip(self._btns, self._pages)):
            if i == idx:
                btn.config(fg=TEXT_PRIMARY, bg=BG_DARK,
                           font=FONT_SUBHEAD)
                pg.pack(fill="both", expand=True, padx=0, pady=0)
            else:
                btn.config(fg=TEXT_SECONDARY, bg=BG_ELEVATED,
                           font=FONT_BODY)
                pg.pack_forget()
        if self._cb:
            self._cb(idx)

    def page(self, idx) -> tk.Frame:
        return self._pages[idx]


# ─────────────────────────────────────────────────────────────────────────────
#  Separator
# ─────────────────────────────────────────────────────────────────────────────
class HSep(tk.Canvas):
    def __init__(self, parent, color=BORDER, **kw):
        super().__init__(parent, height=1, bg=parent["bg"],
                         highlightthickness=0, **kw)
        self.bind("<Configure>", lambda e: self.create_line(
            0, 0, e.width, 0, fill=color))


# ─────────────────────────────────────────────────────────────────────────────
#  Scrollable frame
# ─────────────────────────────────────────────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        canvas = tk.Canvas(self, bg=kw.get("bg", BG_DARK),
                           highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(canvas, bg=kw.get("bg", BG_DARK))
        _id = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(_id, width=e.width))
        self.inner.bind("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))


# ─────────────────────────────────────────────────────────────────────────────
#  Styled entry
# ─────────────────────────────────────────────────────────────────────────────
class StyledEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kw):
        super().__init__(parent,
                         bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=ACCENT,
                         relief="flat", font=FONT_BODY,
                         highlightbackground=BORDER,
                         highlightcolor=BORDER_FOCUS,
                         highlightthickness=1,
                         **kw)
        self._ph = placeholder
        if placeholder:
            self.insert(0, placeholder)
            self.config(fg=TEXT_MUTED)
            self.bind("<FocusIn>",  self._clear_ph)
            self.bind("<FocusOut>", self._restore_ph)

    def _clear_ph(self, _):
        if self.get() == self._ph:
            self.delete(0, "end")
            self.config(fg=TEXT_PRIMARY)

    def _restore_ph(self, _):
        if not self.get():
            self.insert(0, self._ph)
            self.config(fg=TEXT_MUTED)

    def real_value(self):
        v = self.get()
        return "" if v == self._ph else v


# ─────────────────────────────────────────────────────────────────────────────
#  Gradient breathing background (canvas animation)
# ─────────────────────────────────────────────────────────────────────────────
class BreathingBackground(tk.Canvas):
    """Animated gradient background using canvas rectangles as colour bands."""
    _STOPS = [
        (0.00, "#0d0d12"),
        (0.35, "#11101d"),
        (0.65, "#0e1420"),
        (1.00, "#0d0d12"),
    ]
    _STEP = 0

    def __init__(self, parent, **kw):
        super().__init__(parent, highlightthickness=0,
                         bg=BG_DARK, **kw)
        self._bands: list[int] = []
        self.bind("<Configure>", self._on_resize)
        self._animate()

    def _on_resize(self, event=None):
        self._draw(self._STEP)

    def _draw(self, step):
        self.delete("bg_band")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        n = 40
        phase = step / 200.0
        for i in range(n):
            t = i / n
            r, g, b = _interp_gradient(self._STOPS, (t + phase) % 1.0)
            color = f"#{r:02x}{g:02x}{b:02x}"
            y0 = int(t * h)
            y1 = int((i+1)/n * h) + 1
            self.create_rectangle(0, y0, w, y1, fill=color, outline="",
                                  tags="bg_band")

    def _animate(self):
        BreathingBackground._STEP = (BreathingBackground._STEP + 1) % 400
        self._draw(self._STEP)
        self.after(50, self._animate)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a canvas."""
    pts = [
        x1+r, y1,  x2-r, y1,
        x2,   y1,  x2,   y1+r,
        x2,   y2-r, x2,  y2,
        x2-r, y2,  x1+r, y2,
        x1,   y2,  x1,   y2-r,
        x1,   y1+r, x1,  y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def _lighten(hex_color, amount=0.15):
    r, g, b = _hex_to_rgb(hex_color)
    r = min(255, int(r + (255-r)*amount))
    g = min(255, int(g + (255-g)*amount))
    b = min(255, int(b + (255-b)*amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def _darken(hex_color, amount=0.2):
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, int(r * (1-amount)))
    g = max(0, int(g * (1-amount)))
    b = max(0, int(b * (1-amount)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)


def _interp_gradient(stops, t):
    """Interpolate colour along gradient stops, t ∈ [0,1]."""
    for i in range(len(stops)-1):
        t0, c0 = stops[i]
        t1, c1 = stops[i+1]
        if t0 <= t <= t1:
            ratio = (t - t0) / (t1 - t0) if t1 != t0 else 0
            r0, g0, b0 = _hex_to_rgb(c0)
            r1, g1, b1 = _hex_to_rgb(c1)
            return (int(r0+(r1-r0)*ratio),
                    int(g0+(g1-g0)*ratio),
                    int(b0+(b1-b0)*ratio))
    return _hex_to_rgb(stops[-1][1])