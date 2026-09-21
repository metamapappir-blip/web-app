# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build description for PCScope.

Produces two single-file executables from one analysis pass:

    PCScope.exe      windowed GUI  (no console window)
    PCScopeCLI.exe   console build for scripts / CI

Build with::

    pyinstaller --noconfirm --clean pcscope.spec
"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "psutil",
    "arabic_reshaper",
    "bidi",
    "bidi.algorithm",
    "multiprocessing",
    "multiprocessing.spawn",
]

for package in ("arabic_reshaper", "bidi"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    for item in package_hidden:
        if item not in hiddenimports:
            hiddenimports.append(item)

icon = "assets/pcscope.ico"

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test", "pytest", "numpy", "PIL"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe_gui = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PCScope",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

exe_cli = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PCScopeCLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
