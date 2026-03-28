# ui/catalogue.py — Main menu / catalogue screen

import tkinter as tk
from typing import Callable, Optional
from ui.theme import *
from ui.components import RoundedButton, HSep, _rounded_rect


class CatalogueScreen(tk.Frame):
    """
    Main catalogue — big category buttons with descriptions.
    Categories: Upscale | Downscale | Enhance (future)
    """

    CATEGORIES = [
        {
            "id":    "upscale",
            "icon":  "✦",
            "title": "Upscale",
            "desc":  "Enlarge and enhance media using AI upscaling (Real-ESRGAN) and audio resampling.",
            "color": ACCENT,
            "items": [
                ("🖼️  Images",   "upscale", "image"),
                ("🎬  Videos",   "upscale", "video"),
                ("🎵  Audio",    "upscale", "audio"),
                ("📄  PDF / Docs","upscale","document"),
            ]
        },
        {
            "id":    "downscale",
            "icon":  "◈",
            "title": "Downscale",
            "desc":  "Compress and reduce file size while preserving as much quality as possible.",
            "color": ACCENT2,
            "items": [
                ("🖼️  Images",   "downscale", "image"),
                ("🎬  Videos",   "downscale", "video"),
                ("🎵  Audio",    "downscale", "audio"),
                ("📄  PDF / Docs","downscale","document"),
            ]
        },
        {
            "id":    "enhance",
            "icon":  "✧",
            "title": "Enhance",
            "desc":  "AI-powered enhancement, denoising, colour grading. Coming soon.",
            "color": ACCENT3,
            "items": []   # future scope
        },
    ]

    def __init__(self, parent,
                 on_select: Optional[Callable[[str, str], None]] = None,
                 **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._on_select = on_select
        self._build_ui()

    def _build_ui(self):
        # Page title
        tk.Label(self, text="What would you like to do?",
                 font=FONT_HEADING, fg=TEXT_SECONDARY, bg=BG_DARK
                 ).pack(anchor="w", padx=PAD, pady=(PAD, PAD_SM))

        for i, cat in enumerate(self.CATEGORIES):
            self._build_category_card(cat)
            if i < len(self.CATEGORIES)-1:
                HSep(self, color=BORDER).pack(fill="x", padx=PAD, pady=10)

    def _build_category_card(self, cat):
        card = tk.Frame(self, bg=BG_CARD,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x", padx=PAD, pady=4)

        # Category header
        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 4))

        icon_lbl = tk.Label(hdr, text=cat["icon"],
                             font=("Helvetica Neue", 22),
                             fg=cat["color"], bg=BG_CARD)
        icon_lbl.pack(side="left", padx=(0, 10))

        title_fr = tk.Frame(hdr, bg=BG_CARD)
        title_fr.pack(side="left", fill="x", expand=True)
        tk.Label(title_fr, text=cat["title"],
                 font=FONT_SUBHEAD, fg=TEXT_PRIMARY, bg=BG_CARD
                 ).pack(anchor="w")
        tk.Label(title_fr, text=cat["desc"],
                 font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_CARD,
                 wraplength=420, justify="left"
                 ).pack(anchor="w")

        if not cat["items"]:
            # Future scope badge
            badge = tk.Label(card, text="  Coming Soon  ",
                             font=FONT_SMALL,
                             fg=cat["color"], bg=BG_ELEVATED,
                             padx=8, pady=3)
            badge.pack(anchor="w", padx=PAD_SM, pady=(0, PAD_SM))
            return

        # Sub-items row
        sub_fr = tk.Frame(card, bg=BG_CARD)
        sub_fr.pack(fill="x", padx=PAD_SM, pady=(4, PAD_SM))

        for label, mode, media_type in cat["items"]:
            btn = _SubItemButton(sub_fr, label=label,
                                  color=cat["color"],
                                  command=lambda m=mode, t=media_type:
                                      self._on_select(m, t) if self._on_select else None)
            btn.pack(side="left", padx=(0, 8), pady=2)


class _SubItemButton(tk.Canvas):
    """Pill-shaped sub-item button for each media type."""
    _W, _H, _R = 148, 38, 10

    def __init__(self, parent, label, color, command=None, **kw):
        super().__init__(parent, width=self._W, height=self._H,
                         bg=BG_CARD, highlightthickness=0, **kw)
        self._label   = label
        self._color   = color
        self._command = command
        self._draw(False)
        self.bind("<Enter>",           lambda _: self._draw(True))
        self.bind("<Leave>",           lambda _: self._draw(False))
        self.bind("<ButtonRelease-1>", lambda _: self._command() if self._command else None)
        self.config(cursor="hand2")

    def _draw(self, hovered):
        self.delete("all")
        fill    = self._color if hovered else BG_ELEVATED
        outline = self._color
        fg      = BG_DARK if hovered else TEXT_PRIMARY
        _rounded_rect(self, 1, 1, self._W-1, self._H-1, self._R,
                      fill=fill, outline=outline, width=1)
        self.create_text(self._W//2, self._H//2, text=self._label,
                         fill=fg, font=FONT_SMALL)