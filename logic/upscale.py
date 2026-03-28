# logic/upscale.py — Upscaling logic for Drishti

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional
from logic.media_info import FFMPEG_PATH, _BASE_DIR

BASE_DIR = Path(__file__).resolve().parents[1]

ESRGAN_PATH = BASE_DIR / "Real-ESRGAN" / "realesrgan-ncnn-vulkan.exe"

if not ESRGAN_PATH.exists():
    raise FileNotFoundError(f"Real-ESRGAN not found at:\n{ESRGAN_PATH}")

ESRGAN_PATH = str(ESRGAN_PATH)
if not Path(ESRGAN_PATH).exists():
    ESRGAN_PATH = "realesrgan-ncnn-vulkan"

# ── Standard upscale scales ───────────────────────────────────────────────────
ESRGAN_SCALES = [2, 4]          # real-esrgan supports 2x and 4x natively


# ─────────────────────────────────────────────────────────────────────────────
#  Image upscale via Real-ESRGAN
# ─────────────────────────────────────────────────────────────────────────────
def upscale_image(
    input_path: str,
    output_path: str,
    scale: int = 4,
    model: str = "realesrgan-x4plus",
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    """
    Upscale a single image using Real-ESRGAN.
    Runs in a background thread; calls on_progress(pct, msg) and on_done(success, msg).
    """
    def _run():
        try:
            if on_progress: on_progress(5, "Launching Real-ESRGAN…")

            # pick model based on scale
            chosen_model = model
            if scale == 2:
                chosen_model = "realesrgan-x4plus"   # re-uses 4x, then we resize down
            elif scale == 4:
                chosen_model = "realesrgan-x4plus"

            # for non-standard scales: upscale 4x then resize to target
            w_target = h_target = None
            esrgan_out = output_path
            needs_resize = scale not in ESRGAN_SCALES

            if scale == 2:
                # upscale 4x, then resize to 2x
                base, ext = os.path.splitext(output_path)
                esrgan_out = base + "_4x_tmp" + ext
                from logic.media_info import get_info
                info = get_info(input_path)
                w_target = info.width  * 2
                h_target = info.height * 2
            elif needs_resize:
                from logic.media_info import get_info
                info = get_info(input_path)
                base, ext = os.path.splitext(output_path)
                esrgan_out = base + "_4x_tmp" + ext
                w_target = info.width  * scale
                h_target = info.height * scale

            cmd = [
                ESRGAN_PATH,
                "-i", input_path,
                "-o", esrgan_out,
                "-n", chosen_model,
            ]
            if on_progress: on_progress(15, "Running AI upscale…")

            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or "Real-ESRGAN failed")

            # resize if needed
            if w_target and h_target and esrgan_out != output_path:
                if on_progress: on_progress(80, "Resizing to target scale…")
                resize_cmd = [
                    FFMPEG_PATH, "-y", "-i", esrgan_out,
                    "-vf", f"scale={w_target}:{h_target}:flags=lanczos",
                    output_path
                ]
                r2 = subprocess.run(resize_cmd, capture_output=True, text=True)
                os.remove(esrgan_out)
                if r2.returncode != 0:
                    raise RuntimeError(r2.stderr)

            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)

        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  Video upscale — frame-extract → ESRGAN each frame → reassemble
# ─────────────────────────────────────────────────────────────────────────────
def upscale_video(
    input_path: str,
    output_path: str,
    scale: int = 2,
    target_fps: Optional[float] = None,
    model: str = "realesrgan-x4plus",
    crf: int = 18,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    """
    Upscale video: extract frames → ESRGAN → reassemble + optional FPS interpolation.
    Very VRAM/time intensive. Progress reported to on_progress.
    """
    import tempfile, shutil
    from logic.media_info import get_info
    from logic.interpolate import interpolate_video

    def _run():
        tmp_dir = tempfile.mkdtemp(prefix="drishti_upscale_")
        try:
            info = get_info(input_path)
            total_frames = max(1, int(info.fps * info.duration_s))
            frames_dir = os.path.join(tmp_dir, "frames_in")
            up_dir     = os.path.join(tmp_dir, "frames_up")
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(up_dir,     exist_ok=True)

            # 1. Extract frames
            if on_progress: on_progress(5, f"Extracting frames ({info.fps_str})…")
            extract_cmd = [
                FFMPEG_PATH, "-y", "-i", input_path,
                os.path.join(frames_dir, "frame_%06d.png")
            ]
            r = subprocess.run(extract_cmd, capture_output=True)
            if r.returncode != 0:
                raise RuntimeError("Frame extraction failed: " + r.stderr.decode())

            frames = sorted(Path(frames_dir).glob("*.png"))
            n = len(frames)
            if on_progress: on_progress(15, f"Upscaling {n} frames with AI…")

            # 2. ESRGAN each frame (batch)
            esrgan_cmd = [
                ESRGAN_PATH, "-i", frames_dir,
                "-o", up_dir,
                "-n", model,
            ]
            proc = subprocess.run(esrgan_cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError("ESRGAN failed: " + proc.stderr)

            # 3. Reassemble
            if on_progress: on_progress(70, "Reassembling video…")
            intermediate = os.path.join(tmp_dir, "upscaled_raw.mp4")
            fps_str = str(info.fps)
            assemble_cmd = [
                FFMPEG_PATH, "-y",
                "-framerate", fps_str,
                "-i", os.path.join(up_dir, "frame_%06d.png"),
                "-c:v", "libx264", "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                intermediate
            ]
            r2 = subprocess.run(assemble_cmd, capture_output=True)
            if r2.returncode != 0:
                raise RuntimeError("Assembly failed: " + r2.stderr.decode())

            # 4. Mux audio back
            if on_progress: on_progress(85, "Muxing audio…")
            with_audio = os.path.join(tmp_dir, "upscaled_audio.mp4")
            mux_cmd = [
                FFMPEG_PATH, "-y",
                "-i", intermediate,
                "-i", input_path,
                "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a?",
                "-shortest", with_audio
            ]
            subprocess.run(mux_cmd, capture_output=True)
            source_for_interp = with_audio if os.path.exists(with_audio) else intermediate

            # 5. Optional FPS interpolation
            final_out = output_path
            if target_fps and abs(target_fps - info.fps) > 0.5:
                if on_progress: on_progress(90, f"Interpolating to {target_fps:.1f} fps…")
                interp_out = os.path.join(tmp_dir, "interpolated.mp4")
                done_evt   = threading.Event()
                err_holder = []
                def _idone(ok, msg):
                    if not ok: err_holder.append(msg)
                    done_evt.set()
                interpolate_video(source_for_interp, interp_out,
                                   source_fps=info.fps, target_fps=target_fps,
                                   on_done=_idone)
                done_evt.wait(timeout=600)
                if err_holder:
                    raise RuntimeError(err_holder[0])
                source_for_interp = interp_out

            shutil.move(source_for_interp, final_out)
            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, final_out)

        except Exception as e:
            if on_done: on_done(False, str(e))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  Audio upscale — resample to higher sample rate
# ─────────────────────────────────────────────────────────────────────────────
def upscale_audio(
    input_path: str,
    output_path: str,
    target_sample_rate: int = 48000,
    target_bitrate_kbps: int = 320,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _run():
        try:
            if on_progress: on_progress(20, "Resampling audio…")
            cmd = [
                FFMPEG_PATH, "-y", "-i", input_path,
                "-ar", str(target_sample_rate),
                "-b:a", f"{target_bitrate_kbps}k",
                "-af", "aresample=resampler=soxr",
                output_path
            ]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr)
            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)
        except Exception as e:
            if on_done: on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  PDF upscale — render pages at higher DPI then repackage
# ─────────────────────────────────────────────────────────────────────────────
def upscale_pdf(
    input_path: str,
    output_path: str,
    dpi: int = 300,
    scale: int = 2,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    import tempfile, shutil

    def _run():
        tmp_dir = tempfile.mkdtemp(prefix="drishti_pdf_")
        try:
            # Step 1: rasterise PDF pages
            if on_progress: on_progress(10, "Rasterising PDF pages…")
            pages_dir = os.path.join(tmp_dir, "pages")
            os.makedirs(pages_dir, exist_ok=True)
            page_images = _gs_render_pdf(input_path, pages_dir, dpi)

            if not page_images:
                # Ghostscript not available — fallback: use Pillow/pypdf to render
                page_images = _pillow_render_pdf(input_path, pages_dir, dpi)

            if not page_images:
                raise RuntimeError(
                    "Could not rasterise PDF.\n"
                    "Install Ghostscript (gswin64c) or Pillow with pdf2image support."
                )

            if on_progress: on_progress(35, f"Rasterised {len(page_images)} pages. Running ESRGAN…")

            # Step 2: ESRGAN upscale the pages folder
            up_dir = os.path.join(tmp_dir, "upscaled")
            os.makedirs(up_dir, exist_ok=True)
            esrgan_cmd = [
                ESRGAN_PATH,
                "-i", pages_dir,
                "-o", up_dir,
                "-n", "realesrgan-x4plus",
            ]
            proc = subprocess.run(esrgan_cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Real-ESRGAN failed:\n{proc.stderr}")

            # Step 3: collect upscaled images (fall back to originals if ESRGAN produced nothing)
            up_images = sorted(Path(up_dir).glob("*.png"))
            if not up_images:
                up_images = sorted(Path(up_dir).glob("*.jpg"))
            if not up_images:
                # ESRGAN produced nothing — use original rasterised pages
                up_images = page_images

            if not up_images:
                raise RuntimeError("No output images found after ESRGAN step.")

            if on_progress: on_progress(80, f"Compiling {len(up_images)} pages into PDF…")

            # Step 4: compile images → PDF
            try:
                from PIL import Image
            except ImportError:
                raise RuntimeError("Pillow is required to compile the output PDF.\npip install pillow")

            frames = [Image.open(str(p)).convert("RGB") for p in up_images]
            if not frames:
                raise RuntimeError("Could not open upscaled page images.")

            # ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                resolution=dpi,
            )

            if not os.path.isfile(output_path):
                raise RuntimeError(f"Output file was not created at:\n{output_path}")

            if on_progress: on_progress(100, "Done!")
            if on_done:     on_done(True, output_path)

        except Exception as e:
            if on_done: on_done(False, str(e))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    threading.Thread(target=_run, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _gs_render_pdf(pdf_path: str, out_dir: str, dpi: int) -> list:
    for gs in ("gswin64c", "gswin32c", "gs"):
        try:
            cmd = [
                gs, "-dNOPAUSE", "-dBATCH", "-dSAFER",
                "-sDEVICE=png16m",
                f"-r{dpi}",
                f"-sOutputFile={out_dir}/page_%03d.png",
                pdf_path,
            ]
            r = subprocess.run(cmd, capture_output=True, timeout=120)
            if r.returncode == 0:
                pages = sorted(Path(out_dir).glob("*.png"))
                if pages:
                    return pages
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return []

def _pillow_render_pdf(pdf_path: str, out_dir: str, dpi: int) -> list:
    """Fallback: render PDF pages using pdf2image (requires poppler)."""
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=dpi)
        paths = []
        for i, page in enumerate(pages):
            p = os.path.join(out_dir, f"page_{i+1:03d}.png")
            page.save(p, "PNG")
            paths.append(Path(p))
        return paths
    except ImportError:
        return []
    except Exception:
        return []


def _images_to_pdf(img_dir, pdf_out):
    """Compile images in img_dir into a PDF."""
    try:
        from PIL import Image
        imgs = sorted(Path(img_dir).glob("*.png"))
        if not imgs:
            return
        frames = [Image.open(str(p)).convert("RGB") for p in imgs]
        frames[0].save(pdf_out, save_all=True, append_images=frames[1:])
    except ImportError:
        raise RuntimeError("Pillow required for PDF compilation.")