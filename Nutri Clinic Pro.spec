# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_submodules


python_lib = Path(sys.base_prefix) / 'Lib'


a = Analysis(
    ['run_app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('database/migrations', 'database/migrations'),
        (str(python_lib / 'sqlite3'), 'sqlite3'),
        ('icone.png', '.'),
    ],
    hiddenimports=collect_submodules('nutri_app') + [
        'sqlite3',
        '_sqlite3',
    ],
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
    [],
    exclude_binaries=True,
    name='Nutri Clinic Pro',
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
    icon=['icone.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nutri Clinic Pro',
)
