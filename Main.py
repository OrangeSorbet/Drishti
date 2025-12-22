import os
import subprocess
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil
import psutil
import GPUtil

# =========================
# CONFIGURATION
# =========================

BASE_DIR = Path(__file__).parent.resolve()
FFMPEG_PATH = BASE_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"
REALESRGAN_SCRIPT_PATH = BASE_DIR / "Real-ESRGAN" / "inference_realesrgan.py"
PYTHON_EXEC = BASE_DIR / "venv" / "Scripts" / "python.exe"

FRAMES_DIR = BASE_DIR / "frames"
UPSCALED_FRAMES_DIR = BASE_DIR / "upscaled_frames"
OUTPUT_DIR = BASE_DIR / "output_video"

RESOLUTIONS = [
    ("144p", 256),
    ("240p", 426),
    ("360p", 640),
    ("480p", 854),
    ("720p", 1280),
    ("1080p", 1920),
    ("2K", 2048),
    ("4K", 3840),
    ("8K", 7680)
]
FRAMERATES = [24, 30, 45, 60, 120, 144]

MODELS = [
    "RealESRGAN_x4plus",
    "RealESRGAN_x4plus_anime_6B",
    "RealESRGAN_x2plus"
]

# =========================
# UTILITY FUNCTIONS
# =========================

def is_within_base(path):
    try:
        Path(path).resolve().relative_to(BASE_DIR)
        return True
    except ValueError:
        return False

def run_cmd(cmd, log):
    log(f">> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        log(result.stdout)
    if result.stderr:
        log(result.stderr)
    if result.returncode != 0:
        log(f"❌ Command failed: {cmd}")

def get_cpu_usage():
    return psutil.cpu_percent(interval=None)

def get_gpu_usage():
    gpus = GPUtil.getGPUs()
    if gpus:
        return gpus[0].load * 100  # First GPU
    return 0.0

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# =========================
# MAIN PROCESSING FUNCTION
# =========================

def process_video(
    video_path, model, outscale, frame_rate, log,
    progress_callback, stats_callback
):
    # Path checks and setup
    video_path = Path(video_path).resolve()
    if not is_within_base(video_path):
        raise PermissionError("File access outside project directory blocked")

    base_name = video_path.stem
    frames_dir = FRAMES_DIR / f"frames_{base_name}"
    upscaled_dir = UPSCALED_FRAMES_DIR / f"upscaled_{base_name}"
    output_video = OUTPUT_DIR / f"{base_name}_upscaled.mp4"
    final_output = OUTPUT_DIR / f"{base_name}_final_8k.mp4"

    # Clean up previous runs for this video
    shutil.rmtree(frames_dir, ignore_errors=True)
    shutil.rmtree(upscaled_dir, ignore_errors=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    upscaled_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log(f"\n=== Processing {video_path.name} ===")
    start_time = time.time()

    # Step 1: Extract frames
    log("Extracting frames...")
    run_cmd(
        f'"{FFMPEG_PATH}" -i "{video_path}" -q:v 1 -vsync 0 "{frames_dir}/frame_%05d.png"', log
    )
    frame_files = sorted(frames_dir.glob("frame_*.png"))
    total_frames = len(frame_files)
    if total_frames == 0:
        log("❌ No frames extracted. Aborting.")
        return

    # Step 2: AI Upscale each frame, track progress
    log("Upscaling frames with Real-ESRGAN...")
    processed_frames = 0

    # Check if model weights exist
    weights_file = BASE_DIR / "Real-ESRGAN" / "weights" / f"{model}.pth"
    if not weights_file.exists():
        log(f"❌ Model weights not found: {weights_file}")
        return

    # Start stats update thread
    stats_running = [True]
    def stats_updater():
        while stats_running[0]:
            elapsed = time.time() - start_time
            cpu = get_cpu_usage()
            gpu = get_gpu_usage()
            stats_callback(elapsed, processed_frames, total_frames, cpu, gpu)
            time.sleep(0.5)
    stats_thread = threading.Thread(target=stats_updater, daemon=True)
    stats_thread.start()

    for frame_file in frame_files:
        # Output path for upscaled frame
        out_name = upscaled_dir / f"{frame_file.stem}_out.png"
        # Run Real-ESRGAN for this frame with tiling and fp32 for CPU
        run_cmd(
            f'"{PYTHON_EXEC}" "{REALESRGAN_SCRIPT_PATH}" -n {model} -i "{frame_file}" --outscale {outscale} --output "{upscaled_dir}" --fp32 --tile 512 --tile_pad 16',
            log
        )
        processed_frames += 1
        progress_callback(processed_frames, total_frames)

    stats_running[0] = False
    stats_thread.join()

    # Step 3: Reassemble video
    log("Reassembling video from upscaled frames...")
    run_cmd(
        f'"{FFMPEG_PATH}" -framerate {frame_rate} -i "{upscaled_dir}/frame_%05d_out.png" '
        f'-c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow "{output_video}"', log
    )

    # Step 4: Add original audio
    log("Adding original audio to upscaled video...")
    run_cmd(
        f'"{FFMPEG_PATH}" -i "{output_video}" -i "{video_path}" -c copy -map 0:v:0 -map 1:a:0 '
        f'-shortest "{final_output}"', log
    )

    elapsed = time.time() - start_time
    log(f"✅ Done: {final_output.name} in {format_time(elapsed)}")

# =========================
# GUI
# =========================

def main():
    root = tk.Tk()
    root.title("8K Portrait Video Upscaler (Batch + AI)")
    root.geometry("900x700")

    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Batch AI Upscaling to 8K using Real-ESRGAN", font=("Arial", 16, "bold")).pack(pady=5)

    # Settings
    settings_frame = tk.Frame(frame)
    settings_frame.pack(pady=5)

    tk.Label(settings_frame, text="Resolution:").grid(row=0, column=0, sticky='e')
    res_var = tk.StringVar(value=RESOLUTIONS[-1][0])
    res_dropdown = ttk.Combobox(settings_frame, textvariable=res_var, values=[r[0] for r in RESOLUTIONS], state="readonly")
    res_dropdown.grid(row=0, column=1)

    tk.Label(settings_frame, text="Framerate:").grid(row=1, column=0, sticky='e')
    fr_var = tk.StringVar(value=str(FRAMERATES[1]))
    fr_dropdown = ttk.Combobox(settings_frame, textvariable=fr_var, values=[str(fr) for fr in FRAMERATES], state="readonly")
    fr_dropdown.grid(row=1, column=1)

    tk.Label(settings_frame, text="Model:").grid(row=2, column=0, sticky='e')
    model_var = tk.StringVar(value=MODELS[0])
    model_dropdown = ttk.Combobox(settings_frame, textvariable=model_var, values=MODELS, state="readonly")
    model_dropdown.grid(row=2, column=1)

    # Log box
    log_box = tk.Text(frame, width=100, height=20, font=("Consolas", 10))
    log_box.pack(pady=10, fill="x")

    # Progress bar and stats
    progress_frame = tk.Frame(frame)
    progress_frame.pack(pady=5, fill="x")

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", padx=5, pady=2)

    stats_label = tk.Label(progress_frame, text="Time: 00:00:00 | Left: --:--:-- | CPU: 0% | GPU: 0% | Frames: 0/0")
    stats_label.pack(pady=2)

    # State
    selected_files = []

    # Logging
    def log(msg):
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        root.update()

    # Progress update
    def update_progress(processed, total):
        percent = (processed / total) * 100 if total else 0
        progress_var.set(percent)
        stats_label.config(text=f"{stats_label.cget('text').split('|')[0]}| Left: --:--:-- | CPU: --% | GPU: --% | Frames: {processed}/{total}")

    # Stats update
    def update_stats(elapsed, processed, total, cpu, gpu):
        left = ((elapsed / processed) * (total - processed)) if processed else 0
        stats_label.config(
            text=f"Time: {format_time(elapsed)} | Left: {format_time(left)} | CPU: {cpu:.1f}% | GPU: {gpu:.1f}% | Frames: {processed}/{total}"
        )

    # File selection
    def select_files():
        files = filedialog.askopenfilenames(
            title="Select Videos",
            initialdir=BASE_DIR,
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        # Filter: Only allow files within BASE_DIR
        filtered = [f for f in files if is_within_base(f)]
        if len(filtered) < len(files):
            messagebox.showwarning("Warning", "Some files were outside the project folder and ignored.")
        if filtered:
            selected_files.clear()
            selected_files.extend(filtered)
            log(f"Selected {len(filtered)} file(s):")
            for f in filtered:
                log(f"  {Path(f).name}")

    # Start processing
    def start_processing():
        if not selected_files:
            messagebox.showerror("No Files", "Please select video files first.")
            return
        try:
            res_label = res_var.get()
            outscale = next(scale for label, scale in RESOLUTIONS if label == res_label)
            fr = int(fr_var.get())
            model = model_var.get()
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        log(f"\nStarting batch processing with {model}, {outscale}px width, {fr} fps...")
        progress_var.set(0)
        stats_label.config(text="Time: 00:00:00 | Left: --:--:-- | CPU: 0% | GPU: 0% | Frames: 0/0")

        def batch_thread():
            for video_path in selected_files:
                try:
                    process_video(
                        video_path, model, outscale, fr, log,
                        update_progress, update_stats
                    )
                except Exception as e:
                    log(f"❌ Error processing {Path(video_path).name}: {e}")
            messagebox.showinfo("Batch Complete", "All videos processed.")

        threading.Thread(target=batch_thread, daemon=True).start()

    # Buttons
    btn_frame = tk.Frame(frame)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Select Videos", command=select_files, width=20).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Start Processing", command=start_processing, width=20).pack(side="left", padx=10)

    root.mainloop()

if __name__ == "__main__":
    main()
