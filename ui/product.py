# ui/product.py — Processing screen (Upscale / Downscale) with Rookie/Novice/Veteran tabs

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, Optional

from ui.theme import *
from ui.components import (
    RoundedButton, GhostButton, LabelledSlider,
    MediaInfoPanel, ModeTabs, HSep, StyledEntry, _rounded_rect
)
from logic.media_info import MediaInfo, get_info, estimate_output_info
from logic.interpolate import get_valid_fps_steps, UPSCALE_FPS_STEPS, DOWNSCALE_FPS_STEPS


# Common resolutions
COMMON_RES = [
    (320, 240), (640, 480), (854, 480), (1280, 720),
    (1920, 1080), (2560, 1440), (3840, 2160), (7680, 4320)
]

class ProductScreen(tk.Frame):
    """
    Full processing screen for one mode ('upscale' or 'downscale')
    and all media types.
    """
    def __init__(self, parent, mode: str,
                 on_back: Optional[Callable] = None, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._mode    = mode         # 'upscale' | 'downscale'
        self._on_back = on_back
        self._input_path  = tk.StringVar()
        self._output_path = tk.StringVar()
        self._info: Optional[MediaInfo] = None
        self._processing = False
        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    #  Layout
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_ELEVATED)
        hdr.pack(fill="x", padx=0, pady=0)
        inner_hdr = tk.Frame(hdr, bg=BG_ELEVATED)
        inner_hdr.pack(fill="x", padx=PAD, pady=12)

        GhostButton(inner_hdr, "← Back", command=self._go_back,
                    width=90, height=34, font=FONT_SMALL
                    ).pack(side="left", padx=(0,12))

        icon  = "⬆️" if self._mode == "upscale" else "⬇️"
        label = "Upscale" if self._mode == "upscale" else "Downscale"
        tk.Label(inner_hdr, text=f"{icon}  {label}",
                 font=FONT_HEADING, fg=TEXT_PRIMARY, bg=BG_ELEVATED
                 ).pack(side="left")

        # Body (split: left = controls, right = info panels)
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # ── Left column ───────────────────────────────────────────────────
        left = tk.Frame(body, bg=BG_DARK, width=520)
        left.pack(side="left", fill="both", expand=True, padx=(0,12))
        left.pack_propagate(False)

        # File input
        self._build_file_io(left)
        HSep(left).pack(fill="x", pady=12)

        # Mode tabs
        self._tabs = ModeTabs(left)
        self._tabs.pack(fill="both", expand=True)
        self._build_rookie_tab(self._tabs.page(0))
        self._build_novice_tab(self._tabs.page(1))
        self._build_veteran_tab(self._tabs.page(2))

        # ── Right column ──────────────────────────────────────────────────
        right = tk.Frame(body, bg=BG_DARK, width=300)
        right.pack(side="right", fill="y", padx=(12,0))
        right.pack_propagate(False)

        self._info_in  = MediaInfoPanel(right, title="Input")
        self._info_in.pack(fill="x", pady=(0,12))
        self._info_out = MediaInfoPanel(right, title="Output (estimated)")
        self._info_out.pack(fill="x", pady=(0,12))

        # Action button + progress
        self._btn_label = "Upscale!" if self._mode == "upscale" else "Compress!"
        self._action_btn = RoundedButton(
            right, self._btn_label, command=self._start,
            width=260, height=50,
            bg_color=ACCENT if self._mode=="upscale" else ACCENT2,
            font=FONT_HEADING
        )
        self._action_btn.pack(pady=(8,4))

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_lbl = tk.Label(right, text="", font=FONT_SMALL,
                                       fg=TEXT_SECONDARY, bg=BG_DARK)
        self._progress_lbl.pack()

        self._prog_canvas = tk.Canvas(right, height=6, bg=BG_ELEVATED,
                                       highlightthickness=0)
        self._prog_canvas.pack(fill="x", pady=(2,4))

    # ─────────────────────────────────────────────────────────────────────────
    def _build_file_io(self, parent):
        # Input row
        in_fr = tk.Frame(parent, bg=BG_DARK)
        in_fr.pack(fill="x", pady=(0,6))
        tk.Label(in_fr, text="Input", font=FONT_SMALL,
                 fg=TEXT_SECONDARY, bg=BG_DARK, width=6, anchor="w"
                 ).pack(side="left")
        self._in_entry = StyledEntry(in_fr, placeholder="Path or drag file here…",
                                     textvariable=self._input_path)
        self._in_entry.pack(side="left", fill="x", expand=True, padx=(4,6), ipady=5)
        GhostButton(in_fr, "Browse", command=self._browse_input,
                    width=80, height=32, font=FONT_SMALL
                    ).pack(side="right")
        self._input_path.trace_add("write", lambda *_: self._on_input_changed())

        # Output row
        out_fr = tk.Frame(parent, bg=BG_DARK)
        out_fr.pack(fill="x", pady=(0,6))
        tk.Label(out_fr, text="Output", font=FONT_SMALL,
                 fg=TEXT_SECONDARY, bg=BG_DARK, width=6, anchor="w"
                 ).pack(side="left")
        self._out_entry = StyledEntry(out_fr, placeholder="Save path…",
                                      textvariable=self._output_path)
        self._out_entry.pack(side="left", fill="x", expand=True, padx=(4,6), ipady=5)
        GhostButton(out_fr, "Browse", command=self._browse_output,
                    width=80, height=32, font=FONT_SMALL
                    ).pack(side="right")

    # ─────────────────────────────────────────────────────────────────────────
    def _build_rookie_tab(self, page):
        page.config(bg=BG_DARK)
        tk.Label(page, text="One slider does it all — drag towards your goal.",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_DARK
                 ).pack(anchor="w", padx=8, pady=(12,4))

        lbl = ("More Quality  ←→  Balanced  ←→  Smaller File"
               if self._mode == "downscale"
               else "Balanced  ←→  Higher Quality")
        tk.Label(page, text=lbl, font=FONT_SMALL,
                 fg=TEXT_SECONDARY, bg=BG_DARK
                 ).pack(anchor="w", padx=8)

        self._rookie_quality = LabelledSlider(
            page, "Quality / Compression",
            from_=1, to=100, initial=70,
            unit="%", on_change=self._on_param_change, width=380
        )
        self._rookie_quality.pack(padx=12, pady=12, fill="x")

        # FPS slider for video (shown dynamically)
        self._rookie_fps_frame = tk.Frame(page, bg=BG_DARK)
        self._rookie_fps_frame.pack(padx=12, fill="x")
        tk.Label(self._rookie_fps_frame, text="Framerate",
                 font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_DARK
                 ).pack(anchor="w")
        self._rookie_fps = tk.Scale(
            self._rookie_fps_frame, orient="horizontal",
            bg=BG_DARK, fg=TEXT_PRIMARY, troughcolor=BG_ELEVATED,
            highlightthickness=0, sliderlength=18,
            from_=5, to=120, resolution=0.001,
            command=lambda _: self._on_param_change()
        )
        self._rookie_fps.set(30)
        self._rookie_fps.pack(fill="x")
        self._rookie_fps_frame.pack_forget()

    def _build_novice_tab(self, page):
        page.config(bg=BG_DARK)
        tk.Label(page,
                 text="Fine-tune resolution and quality independently.",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_DARK
                 ).pack(anchor="w", padx=8, pady=(12,4))

        self._novice_res = LabelledSlider(
            page, "Resolution Scale",
            from_=10, to=400 if self._mode=="upscale" else 100,
            initial=200 if self._mode=="upscale" else 50,
            unit="%", on_change=self._on_param_change, width=380
        )
        self._novice_res.pack(padx=12, pady=(12,0), fill="x")

        self._novice_quality = LabelledSlider(
            page, "Quality  (← compress · balanced · quality →)",
            from_=1, to=100, initial=70,
            unit="%", on_change=self._on_param_change, width=380
        )
        self._novice_quality.pack(padx=12, pady=12, fill="x")

        # FPS
        self._novice_fps_frame = tk.Frame(page, bg=BG_DARK)
        self._novice_fps_frame.pack(padx=12, fill="x")
        tk.Label(self._novice_fps_frame, text="Framerate",
                 font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_DARK
                 ).pack(anchor="w")
        self._novice_fps = tk.Scale(
            self._novice_fps_frame, orient="horizontal",
            bg=BG_DARK, fg=TEXT_PRIMARY, troughcolor=BG_ELEVATED,
            highlightthickness=0, sliderlength=18,
            from_=5, to=120, resolution=0.001,
            command=lambda _: self._on_param_change()
        )
        self._novice_fps.set(30)
        self._novice_fps.pack(fill="x")
        self._novice_fps_frame.pack_forget()

    def _build_veteran_tab(self, page):
        page.config(bg=BG_DARK)
        tk.Label(page, text="Full manual control.",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_DARK
                 ).pack(anchor="w", padx=8, pady=(12,4))

        # Resolution row
        res_fr = tk.Frame(page, bg=BG_DARK)
        self._vet_res_fr = res_fr
        res_fr.pack(fill="x", padx=12, pady=(8,0))
        tk.Label(res_fr, text="Resolution (W × H)", font=FONT_SMALL,
                 fg=TEXT_SECONDARY, bg=BG_DARK).pack(anchor="w")
        row = tk.Frame(res_fr, bg=BG_DARK)
        row.pack(fill="x")
        self._vet_width  = StyledEntry(row, placeholder="Width",  width=8)
        self._vet_width.pack(side="left", padx=(0,4), ipady=4)
        tk.Label(row, text="×", fg=TEXT_MUTED, bg=BG_DARK, font=FONT_BODY).pack(side="left")
        self._vet_height = StyledEntry(row, placeholder="Height", width=8)
        self._vet_height.pack(side="left", padx=(4,12), ipady=4)
        # quick presets
        for w, h in [(1280,720),(1920,1080),(3840,2160)]:
            GhostButton(row, f"{h}p",
                        command=lambda W=w,H=h: self._set_res(W,H),
                        width=52, height=28, font=FONT_SMALL
                        ).pack(side="left", padx=2)

        # Bitrate row
        br_fr = tk.Frame(page, bg=BG_DARK)
        self._vet_bitrate_fr = br_fr
        br_fr.pack(fill="x", padx=12, pady=(10,0))
        self._vet_bitrate = LabelledSlider(
            br_fr, "Bitrate",
            from_=100, to=50000, initial=5000,
            unit=" kbps", on_change=self._on_param_change, width=360
        )
        self._vet_bitrate.pack()

        # Target size row
        sz_fr = tk.Frame(page, bg=BG_DARK)
        self._vet_targetsize_fr = sz_fr
        sz_fr.pack(fill="x", padx=12, pady=(6,0))
        self._vet_targetsize = LabelledSlider(
            sz_fr, "Target Size",
            from_=1, to=8000, initial=0,
            unit=" MB", on_change=self._on_param_change, width=360
        )
        self._vet_targetsize.pack()

        # FPS (video only)
        self._vet_fps_frame = tk.Frame(page, bg=BG_DARK)
        self._vet_fps_frame.pack(fill="x", padx=12, pady=(6,0))
        tk.Label(self._vet_fps_frame, text="Framerate",
                 font=FONT_SMALL, fg=TEXT_SECONDARY, bg=BG_DARK).pack(anchor="w")
        self._vet_fps = tk.Scale(
            self._vet_fps_frame, orient="horizontal",
            bg=BG_DARK, fg=TEXT_PRIMARY, troughcolor=BG_ELEVATED,
            highlightthickness=0, sliderlength=18,
            from_=5, to=120, resolution=0.001,
            command=lambda _: self._on_param_change()
        )
        self._vet_fps.set(30)
        self._vet_fps.pack(fill="x")
        self._vet_fps_frame.pack_forget()

    def _refresh_veteran_controls(self):
        """Show/hide Veteran tab controls based on media type."""
        if not self._info:
            return
        m = self._info.media_type
        is_video    = m == "video"
        is_audio    = m == "audio"
        is_doc      = m == "document"
        has_bitrate = is_video or is_audio
        has_res     = is_video or is_image

        is_image = m == "image"
        has_res  = is_video or is_image

        # resolution row — only for image/video
        res_widget = self._vet_width.master.master  # the res_fr frame
        if has_res:
            res_widget.pack(fill="x", padx=12, pady=(8,0))
        else:
            res_widget.pack_forget()

        # bitrate — video and audio only
        if has_bitrate:
            self._vet_bitrate.master.pack(fill="x", padx=12, pady=(10,0))
        else:
            self._vet_bitrate.master.pack_forget()

        # target size — video only
        if is_video:
            self._vet_targetsize.master.pack(fill="x", padx=12, pady=(6,0))
        else:
            self._vet_targetsize.master.pack_forget()

    # ─────────────────────────────────────────────────────────────────────────
    #  Events
    # ─────────────────────────────────────────────────────────────────────────
    def _go_back(self):
        if self._on_back: self._on_back()

    def _browse_input(self):
        path = filedialog.askopenfilename(title="Select input file")
        if path:
            self._input_path.set(path)

    def _browse_output(self):
        inp = self._input_path.get()
        ext = Path(inp).suffix if inp else ".mp4"
        path = filedialog.asksaveasfilename(
            title="Save output as",
            defaultextension=ext,
            initialfile=f"drishti_output{ext}"
        )
        if path:
            self._output_path.set(path)

    def _on_input_changed(self):
        p = self._input_path.get()
        if os.path.isfile(p):
            self._info = get_info(p)
            self._populate_info_panel(self._info_in, self._info)
            self._refresh_ui_for_media()
            self._suggest_output_path(p)
            self._on_param_change()

    def _suggest_output_path(self, inp):
        p = Path(inp)
        suffix = f"_drishti_{self._mode}"
        out = p.parent / (p.stem + suffix + p.suffix)
        self._output_path.set(str(out))

    def _refresh_ui_for_media(self):
        if not self._info:
            return
        m = self._info.media_type

        is_video = m == "video"
        is_image = m == "image"
        is_audio = m == "audio"
        is_doc   = m == "document"

        # ── FPS sliders (video only) ──────────────────────────────────────────
        fps = self._info.fps or 30.0
        steps = get_valid_fps_steps(fps, self._mode) if is_video else []
        for frame, slider in [
            (self._rookie_fps_frame, self._rookie_fps),
            (self._novice_fps_frame, self._novice_fps),
            (self._vet_fps_frame,    self._vet_fps),
        ]:
            if is_video and steps:
                slider.config(from_=min(steps), to=max(steps))
                slider.set(fps)
                frame.pack(fill="x", padx=12)
            else:
                frame.pack_forget()

        # ── Disable tabs that don't apply ────────────────────────────────────
        # Rookie: always available
        # Novice: not useful for audio (no resolution) or documents
        # Veteran: not useful for documents
        tab_states = {
            0: True,                        # Rookie — always
            1: not is_doc,                  # Novice — hide for PDF
            2: not is_doc,                  # Veteran — hide for PDF
        }
        for idx, enabled in tab_states.items():
            btn = self._tabs._btns[idx]
            if enabled:
                btn.config(fg=TEXT_SECONDARY, cursor="hand2")
                btn.bind("<Button-1>", lambda _, i=idx: self._tabs._select(i))
            else:
                btn.config(fg=TEXT_MUTED, cursor="")
                btn.unbind("<Button-1>")

        # If current tab is now disabled, switch to Rookie
        if not tab_states.get(self._tabs._active, True):
            self._tabs._select(0)

        # ── Novice: hide resolution slider for audio ──────────────────────────
        if is_audio:
            self._novice_res.pack_forget()
        else:
            self._novice_res.pack(padx=12, pady=(12,0), fill="x")

        # ── Veteran: show/hide controls per type ─────────────────────────────
        show_res     = is_image or is_video
        show_bitrate = is_audio or is_video
        show_size    = is_video

        # resolution frame is res_fr inside veteran page
        for widget, show in [
            (self._vet_res_fr,        show_res),
            (self._vet_bitrate_fr,    show_bitrate),
            (self._vet_targetsize_fr, show_size),
        ]:
            if show:
                widget.pack(fill="x", padx=12, pady=(8,0))
            else:
                widget.pack_forget()

    def _on_param_change(self, *_):
        if not self._info: return
        try:
            est = self._build_estimate()
            self._populate_info_panel(self._info_out, est)
        except Exception:
            pass

    def _build_estimate(self) -> MediaInfo:
        info = self._info
        tab  = self._tabs._active  # 0=rookie 1=novice 2=veteran

        w = h = None
        bitrate = None
        fps_val = None
        quality = 70

        if tab == 0:
            quality = int(self._rookie_quality.get())
            if info.media_type == "video":
                fps_val = self._rookie_fps.get()
        elif tab == 1:
            res_pct = self._novice_res.get() / 100
            quality = int(self._novice_quality.get())
            if info.width: w = int(info.width  * res_pct)
            if info.height: h = int(info.height * res_pct)
            if info.media_type == "video":
                fps_val = self._novice_fps.get()
        elif tab == 2:
            try: w = int(self._vet_width.real_value())
            except: pass
            try: h = int(self._vet_height.real_value())
            except: pass
            bitrate = self._vet_bitrate.get()
            if info.media_type == "video":
                fps_val = self._vet_fps.get()

        return estimate_output_info(
            info,
            scale_w=w, scale_h=h,
            target_bitrate_kbps=bitrate,
            target_fps=fps_val
        )

    def _populate_info_panel(self, panel: MediaInfoPanel, info: MediaInfo):
        panel.set_field("Type", info.media_type.title())
        panel.set_field("Size", info.size_str)

        if info.media_type == "document":
            panel.set_field("Pages", str(info.pages) if info.pages else "—")
            # clear irrelevant fields
            panel.set_field("Resolution", "—")
            panel.set_field("Bitrate",    "—")
            panel.set_field("FPS",        "—")
            panel.set_field("Duration",   "—")
            return

        if info.media_type == "image":
            panel.set_field("Resolution", info.resolution_str)
            panel.set_field("Bitrate",    "—")
            panel.set_field("FPS",        "—")
            panel.set_field("Duration",   "—")
            panel.set_field("Pages",      "—")
            return

        if info.media_type == "audio":
            panel.set_field("Resolution", "—")
            panel.set_field("Bitrate",    info.bitrate_str)
            panel.set_field("FPS",        "—")
            panel.set_field("Duration",   info.duration_str)
            panel.set_field("Pages",      "—")
            return

        # video
        panel.set_field("Resolution", info.resolution_str)
        panel.set_field("Bitrate",    info.bitrate_str)
        panel.set_field("FPS",        info.fps_str)
        panel.set_field("Duration",   info.duration_str)
        panel.set_field("Pages",      "—")
        
    def _set_res(self, w, h):
        self._vet_width.delete(0,"end");  self._vet_width.insert(0, str(w))
        self._vet_height.delete(0,"end"); self._vet_height.insert(0, str(h))
        self._on_param_change()

    # ─────────────────────────────────────────────────────────────────────────
    #  Start processing
    # ─────────────────────────────────────────────────────────────────────────
    def _start(self):
        if self._processing: return
        inp  = self._input_path.get()
        out  = self._output_path.get()
        if not inp or not os.path.isfile(inp):
            messagebox.showerror("No input", "Please select a valid input file.")
            return
        if not out:
            messagebox.showerror("No output", "Please specify an output path.")
            return
        if not self._info:
            self._info = get_info(inp)

        self._processing = True
        self._action_btn.configure_text("Processing…")
        self._dispatch(inp, out)

    def _dispatch(self, inp, out):
        info     = self._info
        tab      = self._tabs._active
        m_type   = info.media_type

        kw = dict(on_progress=self._on_progress, on_done=self._on_done)

        if self._mode == "upscale":
            self._dispatch_upscale(inp, out, tab, m_type, info, kw)
        else:
            self._dispatch_downscale(inp, out, tab, m_type, info, kw)

    def _dispatch_upscale(self, inp, out, tab, m_type, info, kw):
        from logic.upscale import (upscale_image, upscale_video,
                                    upscale_audio, upscale_pdf)
        if m_type == "image":
            scale = self._get_scale_factor(tab, info)
            upscale_image(inp, out, scale=scale, **kw)
        elif m_type == "video":
            scale   = self._get_scale_factor(tab, info)
            fps_val = self._get_fps(tab, info)
            upscale_video(inp, out, scale=scale, target_fps=fps_val, **kw)
        elif m_type == "audio":
            sr  = 48000 if tab == 0 else 96000
            br  = 320
            upscale_audio(inp, out, target_sample_rate=sr,
                          target_bitrate_kbps=br, **kw)
        elif m_type == "document":
            upscale_pdf(inp, out, **kw)
        else:
            # try generic image upscale
            upscale_image(inp, out, scale=2, **kw)

    def _dispatch_downscale(self, inp, out, tab, m_type, info, kw):
        from logic.downscale import (downscale_image, downscale_video,
                                      downscale_audio, downscale_pdf)
        if m_type == "image":
            q = self._get_quality(tab)
            scale_pct = int(self._novice_res.get()) if tab >= 1 else 75
            downscale_image(inp, out, scale_percent=scale_pct, quality=q, **kw)
        elif m_type == "video":
            fps_val = self._get_fps(tab, info)
            if tab == 0:
                downscale_video(inp, out,
                                quality_percent=int(self._rookie_quality.get()),
                                target_fps=fps_val, **kw)
            elif tab == 1:
                res_pct = self._novice_res.get() / 100
                w = int(info.width*res_pct)  if info.width  else None
                h = int(info.height*res_pct) if info.height else None
                downscale_video(inp, out, target_width=w, target_height=h,
                                crf=int(50 - self._novice_quality.get()/2),
                                target_fps=fps_val, **kw)
            else:
                try: w = int(self._vet_width.real_value())
                except: w = None
                try: h = int(self._vet_height.real_value())
                except: h = None
                br = self._vet_bitrate.get() or None
                sz = self._vet_targetsize.get() or None
                downscale_video(inp, out, target_width=w, target_height=h,
                                target_bitrate_kbps=br,
                                target_size_mb=sz if sz and sz > 0 else None,
                                target_fps=fps_val, **kw)
        elif m_type == "audio":
            q = self._get_quality(tab)
            if tab == 2:
                br = self._vet_bitrate.get()
                downscale_audio(inp, out, target_bitrate_kbps=br, **kw)
            else:
                downscale_audio(inp, out, quality_percent=q, **kw)
        elif m_type == "document":
            q = self._get_quality(tab)
            downscale_pdf(inp, out, quality_percent=q, **kw)
        else:
            downscale_image(inp, out, quality_percent=self._get_quality(tab), **kw)

    def _get_quality(self, tab):
        if tab == 0: return int(self._rookie_quality.get())
        if tab == 1: return int(self._novice_quality.get())
        return 75

    def _get_scale_factor(self, tab, info):
        if tab == 0: return 2 if self._rookie_quality.get() < 50 else 4
        if tab == 1:
            pct = self._novice_res.get()
            return 4 if pct >= 200 else 2
        # veteran: derive from width/height
        try:
            tw = int(self._vet_width.real_value())
            if info.width: return max(1, round(tw / info.width))
        except: pass
        return 2

    def _get_fps(self, tab, info):
        if not info or info.media_type != "video": return None
        if tab == 0: return self._rookie_fps.get() if self._rookie_fps_frame.winfo_ismapped() else None
        if tab == 1: return self._novice_fps.get() if self._novice_fps_frame.winfo_ismapped() else None
        return self._vet_fps.get() if self._vet_fps_frame.winfo_ismapped() else None

    # ─────────────────────────────────────────────────────────────────────────
    #  Progress callbacks (called from background threads)
    # ─────────────────────────────────────────────────────────────────────────
    def _on_progress(self, pct: int, msg: str):
        self.after(0, lambda: self._update_progress(pct, msg))

    def _update_progress(self, pct, msg):
        self._progress_lbl.config(text=msg)
        self._prog_canvas.delete("all")
        w = self._prog_canvas.winfo_width() or 280
        filled = int(w * pct / 100)
        self._prog_canvas.create_rectangle(0,0,w,6, fill=BG_ELEVATED, outline="")
        if filled > 0:
            self._prog_canvas.create_rectangle(0,0,filled,6, fill=ACCENT, outline="")

    def _on_done(self, success: bool, msg: str):
        self.after(0, lambda: self._finish(success, msg))

    def _finish(self, success, msg):
        self._processing = False
        self._action_btn.configure_text(self._btn_label)
        if success:
            self._update_progress(100, "✓ Complete!")
            # refresh output info
            out = self._output_path.get()
            if os.path.isfile(out):
                out_info = get_info(out)
                self._populate_info_panel(self._info_out, out_info)
            messagebox.showinfo("Done!", f"Saved to:\n{msg}")
        else:
            self._update_progress(0, "")
            messagebox.showerror("Error", f"Processing failed:\n{msg}")

    # ─────────────────────────────────────────────────────────────────────────
    #  Drag & drop (called from mainscreen)
    # ─────────────────────────────────────────────────────────────────────────
    def accept_drop(self, path: str):
        self._input_path.set(path)