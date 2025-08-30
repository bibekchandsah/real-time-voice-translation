# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['realtime_voice_translator.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('translator_config.json', '.'),
        ('icon.ico', '.'),
        ('icon.png', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'threading',
        'queue',
        'time',
        'json',
        'os',
        'pyaudio',
        'wave',
        'base64',
        'io',
        'openai',
        'numpy',
        'datetime',
        'google.generativeai',
        'google.ai.generativelanguage',
        'google.auth',
        'google.auth.transport.requests',
        'google.protobuf',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RealTimeVoiceTranslator_Full',
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
    icon='icon.ico',  # Use the icon file
)