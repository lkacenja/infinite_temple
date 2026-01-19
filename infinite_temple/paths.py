"""
Cross-platform path configuration for Infinite Temple.

Handles:
- Development mode (relative paths from project root)
- Packaged mode (user Documents directory for data, bundled assets)
"""
import sys
import os
from pathlib import Path


def is_packaged() -> bool:
    """Check if running from PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundle_dir() -> Path:
    """Get the directory containing bundled assets (for packaged app)."""
    if is_packaged():
        return Path(sys._MEIPASS)
    # Development mode - project root
    return Path(__file__).parent.parent


def get_assets_dir() -> Path:
    """Get path to audio assets directory."""
    return get_bundle_dir() / "assets"


def get_user_data_dir() -> Path:
    """
    Get user data directory for temples and config.

    Always uses Documents folder:
        - macOS: ~/Documents/InfiniteTemple
        - Windows: Documents\\InfiniteTemple
        - Linux: ~/Documents/InfiniteTemple
    """
    if sys.platform == "darwin":
        # macOS
        base = Path.home() / "Documents"
    elif sys.platform == "win32":
        # Windows - use shell32 to get proper Documents path
        try:
            import ctypes.wintypes
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            # CSIDL_PERSONAL = 5 (Documents folder)
            ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
            base = Path(buf.value)
        except Exception:
            # Fallback
            base = Path.home() / "Documents"
    else:
        # Linux/other
        base = Path.home() / "Documents"

    return base / "InfiniteTemple"


def get_temples_dir() -> Path:
    """Get directory for temple storage. Creates if needed."""
    temples_dir = get_user_data_dir() / "temples"
    temples_dir.mkdir(parents=True, exist_ok=True)
    return temples_dir


def get_config_dir() -> Path:
    """Get directory for user configuration (API keys, settings)."""
    config_dir = get_user_data_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
