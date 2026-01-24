# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import glob

block_cipher = None

# Bundle assets with the executable
datas = [
    ('assets', 'assets'),
]

# Find Cairo and related libraries for bundling
binaries = []

if sys.platform == 'darwin':
    # macOS: Find homebrew libraries
    # ARM Macs use /opt/homebrew, Intel uses /usr/local
    homebrew_lib = '/opt/homebrew/lib' if os.path.exists('/opt/homebrew/lib') else '/usr/local/lib'

    # Libraries needed for cairosvg
    lib_patterns = [
        'libcairo*.dylib',
        'libpango*.dylib',
        'libgobject*.dylib',
        'libglib*.dylib',
        'libfontconfig*.dylib',
        'libfreetype*.dylib',
        'libpixman*.dylib',
        'libpng*.dylib',
        'libharfbuzz*.dylib',
        'libfribidi*.dylib',
        'libintl*.dylib',
    ]

    for pattern in lib_patterns:
        for lib_path in glob.glob(os.path.join(homebrew_lib, pattern)):
            # Include both actual files and symlinks - PyInstaller will resolve them
            if os.path.exists(lib_path):
                binaries.append((lib_path, '.'))

elif sys.platform == 'win32':
    # Windows: Find Cairo and related DLLs
    # Check build_libs first (downloaded by 'make build-deps'), then common install locations
    win_lib_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_libs', 'gtk', 'bin'),
        r'C:\msys64\mingw64\bin',
        r'C:\GTK\bin',
        r'C:\Program Files\GTK3-Runtime Win64\bin',
        r'C:\Program Files (x86)\GTK3-Runtime\bin',
    ]

    # Also check PATH
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    win_lib_paths.extend(path_dirs)

    dll_patterns = [
        'libcairo-2.dll',
        'libpango*.dll',
        'libgobject*.dll',
        'libglib*.dll',
        'libfontconfig*.dll',
        'libfreetype*.dll',
        'libpixman*.dll',
        'libpng*.dll',
        'libharfbuzz*.dll',
        'libfribidi*.dll',
        'libintl*.dll',
        'zlib*.dll',
        'libffi*.dll',
    ]

    for lib_dir in win_lib_paths:
        if os.path.isdir(lib_dir):
            for pattern in dll_patterns:
                for dll_path in glob.glob(os.path.join(lib_dir, pattern)):
                    if os.path.isfile(dll_path):
                        binaries.append((dll_path, '.'))
            # If we found cairo, we likely have all deps from this dir
            if os.path.exists(os.path.join(lib_dir, 'libcairo-2.dll')):
                break

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
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_cairo.py'],
    excludes=[
        'tkinter',  # Not needed, reduces size
        'unittest',
        'test',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

if sys.platform == 'darwin':
    # macOS: Use onedir mode for .app bundle
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='InfiniteTemple',
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
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='InfiniteTemple',
    )

    app = BUNDLE(
        coll,
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

else:
    # Windows: Use onefile mode
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
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
