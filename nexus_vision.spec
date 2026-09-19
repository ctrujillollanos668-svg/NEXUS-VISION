# -*- mode: python ; coding: utf-8 -*-
"""
Especificación de Compilación para PyInstaller — NEXUS VISION
Permite empaquetar toda la aplicación Python, el Frontend Web y los Modelos en un ejecutable binario para Windows.
"""
from pathlib import Path

block_cipher = None

added_files = [
    ('frontend', 'frontend'),
    ('models', 'models'),
    ('storage', 'storage'),
    ('.env.example', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespans',
        'uvicorn.lifespans.on',
        'engineio.async_drivers.asgi',
        'torch',
        'torchvision',
        'ultralytics',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
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
    [],
    exclude_binaries=True,
    name='NexusVision',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexusVision',
)
