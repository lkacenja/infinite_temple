"""
Temple repository for managing temple configurations.

Handles loading, listing, and organizing temple configurations without
managing game state (roguelike - no save/load).
"""

import json
from pathlib import Path
from typing import Optional

from infinite_temple.schema.temple import TempleConfiguration, TempleCatalog
from infinite_temple.paths import get_temples_dir


class TempleRepository:
    """
    Manages temple configurations (immutable assets).

    This repository handles:
    - Loading temple configurations
    - Listing available temples
    - Managing the temple catalog

    Does NOT handle:
    - Game state (roguelike - no save/load)
    - Mid-run progress (permadeath)
    """

    def __init__(self, base_dir: str = None):
        """
        Initialize the temple repository.

        Args:
            base_dir: Base directory containing temple folders (default: from paths module)
        """
        if base_dir is None:
            self.base_dir = get_temples_dir()
        else:
            self.base_dir = Path(base_dir)
        self.catalog_file = self.base_dir / "catalog.json"

    def save_temple(self, temple: TempleConfiguration):
        """
        Add temple to catalog.

        Args:
            temple: TempleConfiguration to add to catalog

        Note:
            The temple's actual files should already be saved by the generation pipeline.
            This method only updates the catalog index.
        """
        catalog = self.load_catalog()

        # Check if temple already exists in catalog
        existing = catalog.get_temple(temple.temple_id)
        if existing:
            # Update existing entry
            catalog.temples = [t for t in catalog.temples if t.temple_id != temple.temple_id]

        catalog.add_temple(temple)
        self._save_catalog(catalog)

    def load_temple(self, temple_id: str) -> Optional[TempleConfiguration]:
        """
        Load a temple configuration by ID.

        Args:
            temple_id: Unique temple identifier

        Returns:
            TempleConfiguration or None if not found

        Example:
            >>> repo = TempleRepository()
            >>> temple = repo.load_temple("temple_1234567890")
            >>> print(temple.narrative.title)
        """
        temple_dir = self.base_dir / temple_id
        config_file = temple_dir / "config.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
            return TempleConfiguration.model_validate(config_data)
        except Exception as e:
            print(f"Error loading temple {temple_id}: {e}")
            return None

    def load_catalog(self) -> TempleCatalog:
        """
        Load the temple catalog.

        Returns:
            TempleCatalog with all indexed temples

        Note:
            If catalog doesn't exist, scans temple directories and builds it.
        """
        if self.catalog_file.exists():
            try:
                with open(self.catalog_file, "r") as f:
                    catalog_data = json.load(f)
                return TempleCatalog.model_validate(catalog_data)
            except Exception as e:
                print(f"Warning: Error loading catalog, rebuilding: {e}")

        # Catalog doesn't exist or is corrupted, rebuild it
        return self._rebuild_catalog()

    def list_temples(self, sort_by: str = "created_at") -> list[TempleConfiguration]:
        """
        List all temples, optionally sorted.

        Args:
            sort_by: Sort key ('created_at' or 'room_count')

        Returns:
            List of TempleConfiguration objects

        Example:
            >>> repo = TempleRepository()
            >>> temples = repo.list_temples(sort_by="created_at")
            >>> for temple in temples:
            ...     print(f"{temple.narrative.title} ({temple.room_count} rooms)")
        """
        catalog = self.load_catalog()
        return catalog.list_temples(sort_by=sort_by)

    def delete_temple(self, temple_id: str):
        """
        Remove temple from catalog and delete its files.

        Args:
            temple_id: Temple to delete

        Warning:
            This permanently deletes all temple files!
        """
        # Remove from catalog
        catalog = self.load_catalog()
        catalog.temples = [t for t in catalog.temples if t.temple_id != temple_id]
        self._save_catalog(catalog)

        # Delete temple directory
        temple_dir = self.base_dir / temple_id
        if temple_dir.exists():
            import shutil
            shutil.rmtree(temple_dir)

    def _save_catalog(self, catalog: TempleCatalog):
        """Save catalog to disk."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with open(self.catalog_file, "w") as f:
            f.write(catalog.model_dump_json(indent=2))

    def _rebuild_catalog(self) -> TempleCatalog:
        """
        Rebuild catalog by scanning temple directories.

        Returns:
            New TempleCatalog
        """
        catalog = TempleCatalog()

        if not self.base_dir.exists():
            return catalog

        # Scan for temple directories
        for temple_dir in self.base_dir.iterdir():
            if not temple_dir.is_dir():
                continue

            config_file = temple_dir / "config.json"
            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        config_data = json.load(f)
                    temple = TempleConfiguration.model_validate(config_data)
                    catalog.add_temple(temple)
                except Exception as e:
                    print(f"Warning: Skipping invalid temple {temple_dir.name}: {e}")

        # Save rebuilt catalog
        self._save_catalog(catalog)

        return catalog


if __name__ == "__main__":
    # Test the repository
    import sys

    repo = TempleRepository()

    print("="*80)
    print("TEMPLE REPOSITORY")
    print("="*80)
    print()

    # List all temples
    temples = repo.list_temples(sort_by="created_at")

    if not temples:
        print("No temples found in repository.")
        print("Generate temples from within the game.")
    else:
        print(f"Found {len(temples)} temple(s):\n")
        for i, temple in enumerate(temples, 1):
            print(f"{i}. {temple.temple_id}")
            print(f"   Title: {temple.narrative.title}")
            print(f"   Rooms: {temple.room_count}")
            print(f"   Created: {temple.created_at}")
            print()

    # If temple_id provided, show details
    if len(sys.argv) > 1:
        temple_id = sys.argv[1]
        print("="*80)
        print(f"LOADING TEMPLE: {temple_id}")
        print("="*80)
        print()

        temple = repo.load_temple(temple_id)
        if temple:
            print(f"Title: {temple.narrative.title}")
            print(f"Rooms: {temple.room_count}")
            print(f"\nBackstory:")
            print(temple.narrative.backstory)
            print(f"\nAtmosphere: {temple.narrative.atmosphere}")
            print(f"Visual Theme: {temple.narrative.visual_theme}")
            print(f"\nAssets:")
            print(f"  - Map: {temple.map_file}")
            print(f"  - Music: {temple.audio_file}")
            print(f"  - Title: {temple.title_svg_file}")
            print(f"  - Game Over: {temple.gameover_svg_file}")
        else:
            print(f"Temple '{temple_id}' not found.")
