from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden_imports = collect_submodules('tkinterdnd2')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/logo.ico', 'assets'),
        ('assets/logo.png', 'assets'),

        # Bundle Real-ESRGAN
        ('Real-ESRGAN/*', 'Real-ESRGAN'),

        # Bundle FFmpeg
        ('ffmpeg/*', 'ffmpeg'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Drishti',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Drishti'
)