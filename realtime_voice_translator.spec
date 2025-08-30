# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['realtime_voice_translator.py'],
    pathex=[],
    binaries=[],
    datas=[('translator_config.json', '.'), ('icon.ico', '.'), ('icon.png', '.')],
    hiddenimports=['google.generativeai', 'tkinter', 'pyaudio', 'numpy', 'openai'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='realtime_voice_translator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
