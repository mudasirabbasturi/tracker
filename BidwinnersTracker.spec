# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.pyw'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Include the src folder (ui.py, tracker.py)
        ('src', 'src'),
        # Include the assets folder (icons, etc.)
        ('assets', 'assets'),
        # config.json will be placed by the installer separately
    ],
    hiddenimports=[
        'pystray._win32',
        'PIL._tkinter_finder',
        'customtkinter',
        'win32api',
        'win32con',
        'winreg',
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
    name='BidwinnersTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # Single file exe - no folder needed
    onefile=True,
    console=False,           # No terminal window shown
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # Uncomment and add your .ico file
    icon='assets/icon.ico',
)
