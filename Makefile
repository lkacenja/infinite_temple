.PHONY: help setup setup-deps sync run build build-deps clean

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  setup       Full setup (system deps + Python deps)"
	@echo "  setup-deps  Install system dependencies (macOS only)"
	@echo "  sync        Install Python dependencies via uv"
	@echo "  run         Run the game"
	@echo "  build       Build standalone executable"
	@echo "  build-deps  Download native dependencies for build (Windows)"
	@echo "  clean       Remove build artifacts"

# Install system dependencies (macOS only)
setup-deps:
ifeq ($(shell uname), Darwin)
	brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf cairo
endif

# Install Python dependencies
sync:
	uv sync

# Full setup: system deps + Python deps
setup: setup-deps sync

# Run the game
run:
ifeq ($(shell uname), Darwin)
	DYLD_LIBRARY_PATH=$(shell brew --prefix)/lib uv run python game.py
else
	uv run python game.py
endif

# Download native build dependencies (Windows only)
# Downloads Cairo and GTK DLLs needed for cairosvg
CAIRO_VERSION = 1.17.2
GTK_BUNDLE_URL = https://github.com/nicovank/gtk/releases/download/v$(CAIRO_VERSION)/gtk-3.24.24-windows-x64.zip

build-deps:
ifeq ($(OS),Windows_NT)
	@echo "Downloading Cairo/GTK libraries for Windows..."
	@if not exist "build_libs" mkdir build_libs
	powershell -Command "Invoke-WebRequest -Uri '$(GTK_BUNDLE_URL)' -OutFile 'build_libs/gtk.zip'"
	powershell -Command "Expand-Archive -Path 'build_libs/gtk.zip' -DestinationPath 'build_libs/gtk' -Force"
	@echo "Cairo libraries downloaded to build_libs/gtk/bin"
else
	@echo "build-deps is only needed on Windows"
endif

# Build standalone executable
build:
ifeq ($(OS),Windows_NT)
	@if not exist "build_libs\gtk\bin\libcairo-2.dll" $(MAKE) build-deps
endif
	uv run --extra build pyinstaller game.spec

# Clean build artifacts
clean:
	rm -rf build dist __pycache__ build_libs
