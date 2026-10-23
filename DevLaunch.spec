# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.png', 'assets'),   # 👈 add this
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# ============================================================
# LIBRARY FILTER — fixes "corrupted double-linked list" on X11
# ============================================================
# PyInstaller bundles libxcb-cursor.so.0, but the system ALSO has it.
# When Qt forces the X11 backend, both copies load → heap corruption.
# Solution: let the SYSTEM provide these libs, not the bundle.
# ============================================================

EXCLUDE_LIBS = [
    "libxcb-cursor",     # ← the one that's crashing
    # Uncomment the lines below ONLY if you still get crashes:
    # "libstdc++",       # C++ ABI mismatch
    # "libgcc_s",        # GCC runtime mismatch
    # "libxcb.so",       # Core XCB mismatch
    # "libX11",          # X11 client mismatch
]

def _keep(entry):
    """entry is (dest_name, src_name, typecode) — filter by dest_name."""
    name = entry[0]
    return not any(lib in name for lib in EXCLUDE_LIBS)

a.binaries = [x for x in a.binaries if _keep(x)]

# ============================================================


pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DevLaunch',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DevLaunch',
)