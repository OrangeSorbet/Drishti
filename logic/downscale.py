# logic/downscale.py — Compression / downscale logic for Drishti

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional
from logic.media_info import FFMPEG_PATH


# ─────────────────────────────────────────────────────────────────────────────
#  Image downscale
# ─────────────────────────────────────────────────────────────────────────────
def downscale_image(
    input_path: str,
    output_path: str,
    scale_percent: int = 50,        # 1–100 (% of original)
    quality: int = 85,              # 1–100 (JPEG quality or equivalent)
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _run():
        try:
            if on_progress: on_progress(10, "Downscaling image…")
            vf_parts = []

            if target_width or target_height:
                w = target_width  or -2
                h = target_height or -2
                vf_parts.append(f"scale={w}:{h}:flags=lanczos")
            elif scale_percent != 100:
                vf_parts.append(f"scale=iw*{scale_percent/100}:ih*{scale_percent/100}:flags=lanczos")

            ext = Path(output_path).suffix.lower()
            extra = []
            if ext in (".jpg", ".jpeg"):
                extra = ["-q:v", str(int((100-quality)/5 + 2))]
            elif ext == ".webp":
                extra = ["-quality", str(quality)]
            elif ext == ".png":
                compress = max(0, min(9, int((100-quality)/11)))
                extra = ["-compression_level", str(compress)]

            cmd = [FFMPEG_PATH, "-y", "-i", input_path]
            if vf_parts:
                cmd += ["-vf", ",".join(vf_parts)]
            cmd += extra + [output_path]

            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr)
            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)
        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  Video downscale / compress
# ─────────────────────────────────────────────────────────────────────────────
def downscale_video(
    input_path: str,
    output_path: str,
    # Rookie
    quality_percent: Optional[int] = None,   # 1–100
    # Novice / Veteran
    target_width: Optional[int]    = None,
    target_height: Optional[int]   = None,
    target_bitrate_kbps: Optional[float] = None,
    crf: Optional[int]             = None,   # 0-51, lower = better
    target_fps: Optional[float]    = None,
    target_size_mb: Optional[float]= None,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _run():
        try:
            if on_progress: on_progress(10, "Compressing video…")

            vf_parts = []
            encode_args = ["-c:v", "libx264", "-preset", "medium"]

            # resolution
            if target_width or target_height:
                w = target_width  or -2
                h = target_height or -2
                vf_parts.append(f"scale={w}:{h}:flags=lanczos")

            # FPS
            if target_fps:
                vf_parts.append(f"fps={target_fps}")

            # quality mode
            if target_size_mb:
                from logic.media_info import get_info
                info = get_info(input_path)
                dur = info.duration_s or 1
                kbps = (target_size_mb * 8192) / dur
                encode_args += ["-b:v", f"{kbps:.0f}k", "-pass", "1",
                                 "-an", "-f", "null", os.devnull]
                # two-pass encoding
                cmd1 = [FFMPEG_PATH, "-y", "-i", input_path] + encode_args
                subprocess.run(cmd1, capture_output=True)
                encode_args = ["-c:v", "libx264", "-preset", "medium",
                                "-b:v", f"{kbps:.0f}k", "-pass", "2"]
            elif target_bitrate_kbps:
                encode_args += ["-b:v", f"{target_bitrate_kbps:.0f}k"]
            elif crf is not None:
                encode_args += ["-crf", str(crf)]
            elif quality_percent is not None:
                # map 100%→crf18, 1%→crf51
                mapped_crf = int(18 + (100 - quality_percent) * (51-18) / 99)
                encode_args += ["-crf", str(max(0, min(51, mapped_crf)))]

            cmd = [FFMPEG_PATH, "-y", "-i", input_path]
            if vf_parts:
                cmd += ["-vf", ",".join(vf_parts)]
            cmd += encode_args + ["-c:a", "aac", "-b:a", "128k", output_path]

            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr)
            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)
        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  Audio compress
# ─────────────────────────────────────────────────────────────────────────────
def downscale_audio(
    input_path: str,
    output_path: str,
    quality_percent: Optional[int] = None,
    target_bitrate_kbps: Optional[float] = None,
    target_sample_rate: Optional[int] = None,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _run():
        try:
            if on_progress: on_progress(20, "Compressing audio…")
            cmd = [FFMPEG_PATH, "-y", "-i", input_path]
            if target_bitrate_kbps:
                cmd += ["-b:a", f"{target_bitrate_kbps:.0f}k"]
            elif quality_percent is not None:
                kbps = int(32 + quality_percent * (320-32) / 100)
                cmd += ["-b:a", f"{kbps}k"]
            if target_sample_rate:
                cmd += ["-ar", str(target_sample_rate)]
            cmd.append(output_path)
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr)
            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)
        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  PDF compress
# ─────────────────────────────────────────────────────────────────────────────
def downscale_pdf(
    input_path: str,
    output_path: str,
    quality_percent: int = 70,
    dpi: int = 150,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _run():
        try:
            if on_progress: on_progress(20, "Compressing PDF…")
            # gs settings map
            if quality_percent >= 80:   setting = "/prepress"
            elif quality_percent >= 60: setting = "/printer"
            elif quality_percent >= 40: setting = "/ebook"
            else:                       setting = "/screen"

            for gs in ("gswin64c","gswin32c","gs"):
                try:
                    cmd = [gs, "-dNOPAUSE","-dBATCH","-dQUIET",
                           f"-dPDFSETTINGS={setting}",
                           f"-dColorImageResolution={dpi}",
                           "-sDEVICE=pdfwrite",
                           f"-sOutputFile={output_path}",
                           input_path]
                    r = subprocess.run(cmd, capture_output=True, text=True)
                    if r.returncode == 0:
                        if on_progress: on_progress(100, "Done!")
                        if on_done:     on_done(True, output_path)
                        return
                except FileNotFoundError:
                    continue
            raise RuntimeError("Ghostscript not found. Install GhostScript to compress PDFs.")
        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()