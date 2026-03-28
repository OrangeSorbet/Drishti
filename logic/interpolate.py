# logic/interpolate.py — FPS interpolation via FFmpeg minterpolate / yadif

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional
from logic.media_info import FFMPEG_PATH

# Allowed FPS values for upscaling (interpolation) and downscaling (frame deletion)
UPSCALE_FPS_STEPS   = [23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0, 120.0]
DOWNSCALE_FPS_STEPS = [5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0, 23.976, 24.0, 25.0, 29.97, 30.0]


def interpolate_video(
    input_path: str,
    output_path: str,
    source_fps: float,
    target_fps: float,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    """
    Interpolate video to a different FPS using FFmpeg minterpolate.
    Upscaling FPS uses motion-compensated interpolation.
    Downscaling FPS uses frame selection (no interpolation needed).
    """
    def _run():
        try:
            if on_progress: on_progress(10, f"Converting to {target_fps:.3f} fps…")

            if target_fps > source_fps:
                # Motion-compensated interpolation (minterpolate)
                vf = (f"minterpolate='mi_mode=mci:mc_mode=aobmc:"
                      f"vsbmc=1:fps={target_fps}'")
            else:
                # Simple frame selection for downscaling
                vf = f"fps={target_fps}"

            cmd = [
                FFMPEG_PATH, "-y",
                "-i", input_path,
                "-vf", vf,
                "-c:v", "libx264",
                "-crf", "17",
                "-preset", "fast",
                "-c:a", "copy",
                output_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr)
            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)
        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def get_valid_fps_steps(current_fps: float, mode: str) -> list[float]:
    """
    Return list of valid FPS values for a slider.
    mode = 'upscale' | 'downscale'
    """
    if mode == "upscale":
        return [f for f in UPSCALE_FPS_STEPS if f >= current_fps - 0.1]
    else:
        return [f for f in DOWNSCALE_FPS_STEPS if f <= current_fps + 0.1]


def fps_change_only(
    input_path: str,
    output_path: str,
    target_fps: float,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    """Standalone FPS-only conversion (no scale change)."""
    from logic.media_info import get_info
    info = get_info(input_path)
    interpolate_video(input_path, output_path,
                      source_fps=info.fps,
                      target_fps=target_fps,
                      on_progress=on_progress,
                      on_done=on_done)