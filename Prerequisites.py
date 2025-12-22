import os
import sys
import subprocess
from pathlib import Path
import shutil

# ==== CONFIG ====
REQUIREMENTS_TXT = """\
torch==1.13.1+cpu
torchvision==0.14.1+cpu
basicsr==1.4.2
facexlib==0.2.5
gfpgan==1.3.5
numpy==1.23.5
opencv-python
Pillow
tqdm
psutil
GPUtil
tk
scipy>=1.7,<1.11
setuptools>=65.0.0
wheel
"""
EXTRA_INDEX = "https://download.pytorch.org/whl/cpu"
VENV_DIR = Path("venv")
PYTHON_EXE = VENV_DIR / "Scripts" / "python.exe" if os.name == "nt" else VENV_DIR / "bin" / "python3"

# ==== FUNCTIONS ====

def create_venv():
    if not VENV_DIR.exists():
        print("🔹 Creating Python 3.10 virtual environment...")
        # Try to use current python if it's 3.10, else look for python3.10 in PATH
        if sys.version_info[:2] == (3, 10):
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        else:
            # Try to find python3.10 in PATH
            py310 = shutil.which("python3.10") or shutil.which("python3.10.exe")
            if not py310:
                print("❌ Python 3.10 not found. Please install Python 3.10 and add it to your PATH.")
                sys.exit(1)
            subprocess.check_call([py310, "-m", "venv", str(VENV_DIR)])
        print("✅ Virtual environment created.")
    else:
        print("ℹ️  Virtual environment already exists.")

def write_requirements():
    req_file = Path("requirements.txt")
    req_file.write_text(REQUIREMENTS_TXT)
    print("✅ requirements.txt written.")

def install_requirements():
    print("🔹 Upgrading pip, setuptools, wheel...")
    subprocess.check_call([str(PYTHON_EXE), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    print("🔹 Installing all requirements...")
    subprocess.check_call([
        str(PYTHON_EXE), "-m", "pip", "install", "-r", "requirements.txt",
        "--extra-index-url", EXTRA_INDEX
    ])
    print("✅ All requirements installed in venv.")

def main():
    import shutil

    print("=== Real-ESRGAN Prerequisite Installer ===\n")
    # Warn if not on Python 3.10
    if sys.version_info[:2] != (3, 10):
        print("⚠️  WARNING: You are running Python {}.{}. It's recommended to run this script with Python 3.10.".format(*sys.version_info[:2]))
    create_venv()
    write_requirements()
    install_requirements()
    print("\n🎉 Setup complete! To activate your environment, run:\n")
    if os.name == "nt":
        print(r"venv\Scripts\activate")
    else:
        print(r"source venv/bin/activate")
    print("\nThen run your Main.py as usual.")
    print("If you use VS Code, select the venv Python interpreter before running Main.py.")

if __name__ == "__main__":
    main()
