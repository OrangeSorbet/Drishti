# Drishti — Media Studio

> **Drishti** (Sanskrit: *दृष्टि* — "vision") is a dark-mode desktop media processing suite.  
> Upscale, downscale, and enhance images, videos, audio, PDFs and more — all in one window.

---

## Project Structure

```
Drishti/
├── main.py                  ← Entry point
├── requirements.txt
├── drishti.spec             ← PyInstaller build spec
│
├── logic/
│   ├── media_info.py        ← Metadata extraction (ffprobe)
│   ├── upscale.py           ← Upscale logic (Real-ESRGAN + ffmpeg)
│   ├── downscale.py         ← Compress/downscale logic (ffmpeg)
│   └── interpolate.py       ← FPS interpolation (ffmpeg minterpolate)
│
├── ui/
│   ├── theme.py             ← Colour palette, fonts, constants
│   ├── components.py        ← Reusable widgets (buttons, sliders, panels)
│   ├── mainscreen.py        ← Root window + drag-and-drop overlay
│   ├── catalogue.py         ← Main menu (Upscale / Downscale / Enhance)
│   └── product.py           ← Processing screen (Rookie/Novice/Veteran tabs)
│
├── ffmpeg/
│   ├── ffmpeg.exe
│   └── ffprobe.exe
└── Real-ESRGAN/
    ├── realesrgan-ncnn-vulkan.exe
    └── models/
```

---

## Setup

### 1. Prerequisites

- Python 3.13.7+
- `ffmpeg.exe` and `ffprobe.exe` in `Upscale-Basic/ffmpeg/`
> Version: 7.1.1-full_build-www.gyan.dev   
OR in command prompt - `winget install "FFmpeg (Essentials Build)"`

- `realesrgan-ncnn-vulkan.exe` in `Upscale-Basic/Real-ESRGAN/`
> [Real-ESRGAN V0.2.5.0](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0)  
`realesrgan-ncnn-vulkan-20220424-(macos/ubuntu/windows).zip`
- [Ghostscript](https://ghostscript.com/releases/gsdnld.html) installed for PDF operations

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

For drag-and-drop support (optional but recommended):
```bash
pip install tkinterdnd2
```

For PDF compression:
- Download and install [Ghostscript](https://www.ghostscript.com/download/gsdnld.html)
> If it wasn't recognized as a function, add to User Variables in PATH -   
Edit the system environment variables -> Environment variables... -> User Variables -> PATH -> New  
`C:\Program Files\gs\gs10.07.0\bin` (replace 10.07.0 with your version)

### 3. Run

```
python main.py
```

---

## Features

### Upscale
| Media     | Method                              |
|-----------|-------------------------------------|
| Image     | Real-ESRGAN (2×/4×) + FFmpeg resize |
| Video     | Frame extract → ESRGAN → reassemble + optional FPS interpolation |
| Audio     | FFmpeg resample (up to 96 kHz / 320 kbps) |
| PDF/Docs  | Ghostscript render → ESRGAN → repackage |

### Downscale / Compress
| Media     | Method                              |
|-----------|-------------------------------------|
| Image     | FFmpeg scale + quality              |
| Video     | libx264 CRF / bitrate / two-pass    |
| Audio     | FFmpeg re-encode (AAC/MP3/Opus)     |
| PDF       | Ghostscript PDF settings            |

### Mode Tabs
- **Rookie** — single quality/compression bar
- **Novice** — resolution scale + quality bars
- **Veteran** — manual resolution, bitrate, target size, FPS

### FPS Control (Video)
- Upscale: motion-compensated interpolation via `minterpolate` (e.g. 30→60fps)
- Downscale: frame selection (e.g. 60→24fps)
- Snaps to industry-standard values: 23.976, 24, 25, 29.97, 30, 48, 60, 120…

### Drag & Drop
- Drag any file onto the app window to load it instantly
- Shows "Drop it like it's hot" overlay with dotted rectangle UI

---

## Build (PyInstaller) (Please use inside virtual env itself)

```
pip install pyinstaller
pyinstaller drishti.spec
```

Output: `dist/Drishti.exe` (single-file Windows executable)

---

## Enhance (Future Scope)

The Enhance category is reserved for upcoming AI-powered features:
- Denoising (video + image)
- Colour grading / LUT application
- Face restoration (GFPGAN)
- Audio denoise / clarity enhancement

---

## Notes

- Video upscaling is very GPU/time intensive. A GPU with Vulkan support is strongly recommended for Real-ESRGAN.
- PDF upscaling requires Ghostscript to be installed separately.
- On macOS/Linux, replace `.exe` paths in `logic/media_info.py` with the appropriate binary names (`ffmpeg`, `ffprobe`, `realesrgan-ncnn-vulkan`).