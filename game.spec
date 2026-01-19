# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

# Bundle assets with the executable
datas = [
    ('assets', 'assets'),
]

# Hidden imports that PyInstaller doesn't detect automatically
hiddenimports = [
    # SVG rendering
    'cairosvg',
    'cairocffi',
    'PIL',
    'PIL.Image',
    # Pydantic
    'pydantic',
    'pydantic.deprecated.decorator',
    'pydantic_core',
    # Game engine
    'pygame',
    'pygame.locals',
    # Audio synthesis
    'tomita',
    'tomita.legacy',
    'tomita.legacy.pysynth_c',
    'pedalboard',
    # LLM
    'openai',
    'anthropic',
    'tenacity',
    # Standard library used dynamically
    'json',
    'pathlib',
]

a = Analysis(
    ['game.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # Not needed, reduces size
        'unittest',
        'test',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InfiniteTemple',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Infinite Temple.app',
        icon=None,  # Add icon later: 'assets/icon.icns'
        bundle_identifier='org.infinitetemple.game',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'CFBundleName': 'Infinite Temple',
        },
    )
