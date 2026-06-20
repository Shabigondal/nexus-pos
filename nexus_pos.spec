# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build specification for Nexus POS & Inventory Control Workspace
#
# Build with:
#     pyinstaller nexus_pos.spec
#
# Output:
#     dist/NexusPOS/NexusPOS.exe   (folder build - faster startup, recommended)

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden_imports = []
hidden_imports += collect_submodules('customtkinter')
hidden_imports += collect_submodules('tkcalendar')
hidden_imports += collect_submodules('xhtml2pdf')
hidden_imports += collect_submodules('reportlab')
hidden_imports += collect_submodules('tkinterweb')

# Local project packages - PyInstaller's static analysis can miss these
# namespace-style imports (database.db_manager, modules.*), so list them
# explicitly to guarantee they get bundled.
hidden_imports += collect_submodules('database')
hidden_imports += collect_submodules('modules')

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

# Bundle the Google Drive OAuth client file (one-time file YOU generate in
# Google Cloud Console - see README/BUILD_GUIDE). If present at build time,
# it ships automatically inside dist/NexusPOS/ next to NexusPOS.exe, so the
# client never has to download, place, or even know this file exists.
if os.path.exists('drive_credentials.json'):
    datas += [('drive_credentials.json', '.')]

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
