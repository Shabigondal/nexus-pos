# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build specification for Nexus POS & Inventory Control Workspace
#
# Build with:
#     pyinstaller nexus_pos.spec
#
# Output:
#     dist/NexusPOS/NexusPOS.exe   (folder build - faster startup, recommended)

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden_imports = []
hidden_imports += collect_submodules('customtkinter')
hidden_imports += collect_submodules('tkcalendar')
hidden_imports += collect_submodules('xhtml2pdf')
hidden_imports += collect_submodules('reportlab')
hidden_imports += collect_submodules('tkinterweb')
hidden_imports += [
    'PIL._tkinter_finder',
    'google_auth_oauthlib.flow',
    'google.auth.transport.requests',
    'googleapiclient.discovery',
    'googleapiclient.http',
]

datas = []
datas += collect_data_files('customtkinter')
datas += collect_data_files('tkcalendar')
datas += collect_data_files('tkinterweb')

# Bundle the assets folder (shop logo, etc.) so it's available next to the exe
datas += [('assets', 'assets')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
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
    name='NexusPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexusPOS',
)
