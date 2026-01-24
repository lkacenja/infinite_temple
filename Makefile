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
# Downloads Cairo DLL needed for cairosvg
CAIRO_URL = https://github.com/preshing/cairo-windows/releases/download/with-tee/cairo-windows-1.17.2.zip

build-deps:
ifeq ($(OS),Windows_NT)
	@echo "Downloading Cairo libraries for Windows..."
	@if not exist "build_libs" mkdir build_libs
	@if not exist "build_libs\gtk" mkdir build_libs\gtk
	@if not exist "build_libs\gtk\bin" mkdir build_libs\gtk\bin
	powershell -Command "Invoke-WebRequest -Uri '$(CAIRO_URL)' -OutFile 'build_libs/cairo.zip'"
	powershell -Command "Expand-Archive -Path 'build_libs/cairo.zip' -DestinationPath 'build_libs' -Force"
	powershell -Command "Copy-Item 'build_libs/cairo-windows-1.17.2/lib/x64/cairo.dll' 'build_libs/gtk/bin/libcairo-2.dll'"
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
