.PHONY: help setup setup-deps sync run build clean

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  setup       Full setup (system deps + Python deps)"
	@echo "  setup-deps  Install system dependencies (macOS only)"
	@echo "  sync        Install Python dependencies via uv"
	@echo "  run         Run the game"
	@echo "  build       Build standalone executable"
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

# Build standalone executable
build:
	uv run --extra build pyinstaller game.spec

# Clean build artifacts
clean:
	rm -rf build dist __pycache__
