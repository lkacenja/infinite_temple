# Runtime hook to help cairocffi find bundled Cairo library
import sys
import os
import ctypes.util

if getattr(sys, 'frozen', False):
    # Get the bundle directory
    bundle_dir = sys._MEIPASS

    # Store original find_library
    _original_find_library = ctypes.util.find_library

    if sys.platform == 'darwin':
        # macOS library mappings
        lib_mapping = {
            'cairo': ['libcairo.2.dylib', 'libcairo.dylib'],
            'pango': ['libpango-1.0.0.dylib', 'libpango-1.0.dylib'],
            'pangocairo': ['libpangocairo-1.0.0.dylib', 'libpangocairo-1.0.dylib'],
            'gobject-2.0': ['libgobject-2.0.0.dylib', 'libgobject-2.0.dylib'],
            'glib-2.0': ['libglib-2.0.0.dylib', 'libglib-2.0.dylib'],
        }
    elif sys.platform == 'win32':
        # Windows library mappings
        lib_mapping = {
            'cairo': ['libcairo-2.dll', 'cairo.dll'],
            'cairo-2': ['libcairo-2.dll'],
            'libcairo-2': ['libcairo-2.dll'],
            'pango': ['libpango-1.0-0.dll', 'pango-1.0.dll'],
            'pangocairo': ['libpangocairo-1.0-0.dll'],
            'gobject-2.0': ['libgobject-2.0-0.dll'],
            'glib-2.0': ['libglib-2.0-0.dll'],
        }
    else:
        lib_mapping = {}

    def _patched_find_library(name):
        # Check if the library exists in our bundle first
        if name in lib_mapping:
            for lib_name in lib_mapping[name]:
                lib_path = os.path.join(bundle_dir, lib_name)
                if os.path.exists(lib_path):
                    return lib_path

        # Fall back to original behavior
        return _original_find_library(name)

    # Apply the patch
    ctypes.util.find_library = _patched_find_library

    # Windows: Also add bundle dir to DLL search path
    if sys.platform == 'win32':
        os.add_dll_directory(bundle_dir)
