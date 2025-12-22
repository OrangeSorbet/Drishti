===========================================================================
Project Setup Instructions: Python 3.10 Virtual Environment
===========================================================================

1. Install Python 3.10 (https://www.python.org/downloads/release/python-3100/)
   - On Windows: Default path is usually
     C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\python.exe
   - Or, use 'python' if Python 3.10 is in your PATH.

2. Open a terminal in your project folder.

3. Create a virtual environment:
   # Use the full path if needed, or just 'python' if 3.10 is default
   C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\python.exe -m venv venv
   # OR (if python 3.10 is in PATH)
   python -m venv venv

4. Activate the virtual environment:
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate

5. Install dependencies:
   python Prerequisite.py
   # OR
   pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

6. Move original video to Video Upscaler folder

7. Run the main application:
   python Main.py


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

Real-ESRGAN
ffmpeg
===========================================================================
Note:
- Always activate the virtual environment before running Main.py.
- If you use VS Code, select the venv Python interpreter for your workspace.
- For GPU support, adjust torch/torchvision versions and the extra-index-url as needed.
===========================================================================