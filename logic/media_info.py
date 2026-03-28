# logic/media_info.py — Extract metadata from media files

import os
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ── locate ffprobe next to ffmpeg ─────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent
FFMPEG_PATH  = str(_BASE_DIR / "Upscale-Basic" / "ffmpeg" / "ffmpeg.exe")
FFPROBE_PATH = str(_BASE_DIR / "Upscale-Basic" / "ffmpeg" / "ffprobe.exe")

# fallback to system ffmpeg if the bundled one isn't found
if not Path(FFPROBE_PATH).exists():
    FFPROBE_PATH = "ffprobe"
if not Path(FFMPEG_PATH).exists():
    FFMPEG_PATH  = "ffmpeg"

# Media type categories
IMAGE_EXTS = {".jpg",".jpeg",".png",".bmp",".tiff",".tif",".webp",
              ".gif",".ico",".heic",".heif",".avif",".svg"}
VIDEO_EXTS = {".mp4",".mkv",".avi",".mov",".wmv",".flv",".webm",
              ".m4v",".mpg",".mpeg",".3gp",".ts",".mts",".m2ts"}
AUDIO_EXTS = {".mp3",".wav",".flac",".aac",".ogg",".m4a",".wma",
              ".opus",".aiff",".ape",".alac"}
DOC_EXTS   = {".pdf",".tiff",".tif"}


@dataclass
class MediaInfo:
    path:        str       = ""
    media_type:  str       = "unknown"   # image | video | audio | document
    size_bytes:  int       = 0
    width:       int       = 0
    height:      int       = 0
    duration_s:  float     = 0.0
    fps:         float     = 0.0
    bitrate_kbps:float     = 0.0
    codec:       str       = ""
    channels:    int       = 0
    sample_rate: int       = 0
    pages:       int       = 0
    extra:       dict      = field(default_factory=dict)

    # ── human-friendly helpers ─────────────────────────────────────────────
    @property
    def size_str(self) -> str:
        b = self.size_bytes
        for unit in ("B","KB","MB","GB"):
            if b < 1024: return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"

    @property
    def resolution_str(self) -> str:
        if self.width and self.height:
            return f"{self.width} × {self.height}"
        return "—"

    @property
    def bitrate_str(self) -> str:
        if self.bitrate_kbps:
            if self.bitrate_kbps >= 1000:
                return f"{self.bitrate_kbps/1000:.1f} Mbps"
            return f"{self.bitrate_kbps:.0f} kbps"
        return "—"

    @property
    def fps_str(self) -> str:
        return f"{self.fps:.2f} fps" if self.fps else "—"

    @property
    def duration_str(self) -> str:
        if not self.duration_s: return "—"
        s = int(self.duration_s)
        h, m = divmod(s, 3600)
        m, s2 = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s2:02d}" if h else f"{m:02d}:{s2:02d}"


def detect_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXTS: return "image"
    if ext in VIDEO_EXTS: return "video"
    if ext in AUDIO_EXTS: return "audio"
    if ext == ".pdf":     return "document"
    return "unknown"


def get_info(path: str) -> MediaInfo:
    """Return a MediaInfo for the given file. Never raises — returns partial info."""
    info = MediaInfo(path=path)
    if not os.path.isfile(path):
        return info

    info.size_bytes = os.path.getsize(path)
    info.media_type = detect_type(path)

    if info.media_type == "document":
        info.pages = _count_pdf_pages(path)
        return info

    # use ffprobe for image / video / audio
    raw = _ffprobe(path)
    if raw is None:
        return info

    fmt = raw.get("format", {})
    streams = raw.get("streams", [])

    # duration / bitrate from format
    try:    info.duration_s   = float(fmt.get("duration", 0))
    except: pass
    try:    info.bitrate_kbps = float(fmt.get("bit_rate", 0)) / 1000
    except: pass

    for s in streams:
        codec_type = s.get("codec_type","")
        if codec_type == "video":
            try:    info.width  = int(s.get("width",  0))
            except: pass
            try:    info.height = int(s.get("height", 0))
            except: pass
            info.codec = s.get("codec_name","")
            fps_raw = s.get("r_frame_rate","0/1")
            info.fps = _parse_fps(fps_raw)
        elif codec_type == "audio":
            try:    info.channels    = int(s.get("channels", 0))
            except: pass
            try:    info.sample_rate = int(s.get("sample_rate", 0))
            except: pass
            if not info.codec:
                info.codec = s.get("codec_name","")

    # for pure images ffprobe may give w/h in video stream
    return info


def estimate_output_info(info: MediaInfo,
                          scale_w: Optional[int] = None,
                          scale_h: Optional[int] = None,
                          target_bitrate_kbps: Optional[float] = None,
                          target_fps: Optional[float] = None,
                          target_size_mb: Optional[float] = None) -> MediaInfo:
    out = MediaInfo(
        path=info.path,
        media_type=info.media_type,
        width=scale_w or info.width,
        height=scale_h or info.height,
        fps=target_fps or info.fps,
        codec=info.codec,
        channels=info.channels,
        sample_rate=info.sample_rate,
        duration_s=info.duration_s,
        pages=info.pages,
    )

    if info.media_type == "document":
        out.size_bytes = int(info.size_bytes * 1.4)  # upscale bloats pages
        return out

    if target_bitrate_kbps is not None:
        out.bitrate_kbps = target_bitrate_kbps
    else:
        out.bitrate_kbps = info.bitrate_kbps

    if target_size_mb is not None:
        out.size_bytes = int(target_size_mb * 1024 * 1024)
    elif info.duration_s and out.bitrate_kbps:
        out.size_bytes = int(out.bitrate_kbps * 1000 / 8 * info.duration_s)
    elif info.width and info.height and out.width and out.height:
        ratio = (out.width * out.height) / max(info.width * info.height, 1)
        out.size_bytes = int(info.size_bytes * ratio)
    else:
        out.size_bytes = info.size_bytes

    return out


# ─── private helpers ──────────────────────────────────────────────────────────
def _ffprobe(path: str) -> Optional[dict]:
    try:
        cmd = [FFPROBE_PATH, "-v", "quiet", "-print_format", "json",
               "-show_format", "-show_streams", path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(result.stdout)
    except Exception:
        return None


def _parse_fps(s: str) -> float:
    try:
        if "/" in s:
            a, b = s.split("/")
            return float(a) / float(b) if float(b) else 0.0
        return float(s)
    except Exception:
        return 0.0


def _count_pdf_pages(path: str) -> int:
    try:
        import subprocess
        # use ghostscript or a pure-python fallback
        try:
            import pypdf
            with open(path,"rb") as f:
                return len(pypdf.PdfReader(f).pages)
        except ImportError:
            pass
        # basic raw scan
        with open(path,"rb") as f:
            content = f.read()
        return content.count(b"/Type /Page") or content.count(b"/Type/Page")
    except Exception:
        return 0