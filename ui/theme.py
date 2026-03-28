# ui/theme.py — Drishti Dark Mode Theme

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK      = "#0d0d0f"
BG_CARD      = "#141418"
BG_ELEVATED  = "#1c1c22"
BG_INPUT     = "#22222a"
BG_HOVER     = "#2a2a35"

ACCENT       = "#7c6af7"        # soft violet
ACCENT_BRIGHT= "#9d8fff"
ACCENT_DIM   = "#4a3fa0"
ACCENT2      = "#f76a6a"        # coral red (danger / downscale)
ACCENT3      = "#6af7c8"        # mint (enhance / future)

TEXT_PRIMARY = "#f0f0f5"
TEXT_SECONDARY="#9090a8"
TEXT_MUTED   = "#55556a"
TEXT_ACCENT  = ACCENT_BRIGHT

BORDER       = "#2e2e3d"
BORDER_FOCUS = ACCENT

SUCCESS      = "#6af78a"
WARNING      = "#f7c46a"
ERROR        = "#f76a6a"

# ── Typography ─────────────────────────────────────────────────────────────
FONT_TITLE   = ("Helvetica Neue", 28, "bold")
FONT_HEADING = ("Helvetica Neue", 16, "bold")
FONT_SUBHEAD = ("Helvetica Neue", 13, "bold")
FONT_BODY    = ("Helvetica Neue", 12)
FONT_SMALL   = ("Helvetica Neue", 10)
FONT_MONO    = ("Courier New",    11)
FONT_LOGO    = ("Helvetica Neue", 36, "bold")

# ── Geometry ───────────────────────────────────────────────────────────────
RADIUS       = 14      # corner radius (simulated)
PAD          = 20
PAD_SM       = 10
PAD_XS       = 6

# ── Gradient stops (used in canvas gradient simulation) ───────────────────
GRAD_START   = "#13131a"
GRAD_END     = "#0d0d0f"
GRAD_ACCENT1 = "#1a1535"
GRAD_ACCENT2 = "#0f1a20"