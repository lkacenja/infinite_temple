"""
Temple generation data models.

This module defines schemas for temple configurations, narratives,
and statistics in a roguelike temple exploration game.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TempleNarrative(BaseModel):
    """Generated narrative/lore from seed words"""
    title: str = Field(
        description="Evocative temple name (e.g., 'The Sunken Sanctuary of Whispers')"
    )
    backstory: str = Field(
        min_length=200,
        max_length=2000,
        description="Temple lore/history that informs atmosphere and design (200-2000 characters)"
    )
    atmosphere: str = Field(
        description="Short atmospheric descriptor for music generation (e.g., 'dark and dusty stone passages')"
    )
    visual_theme: str = Field(
        description="Visual style descriptor for SVG generation (e.g., 'angular gothic architecture', 'organic flowing curves')"
    )


class TempleConfiguration(BaseModel):
    """Immutable temple definition - all generated assets for a temple"""

    # Identity
    temple_id: str = Field(
        description="Unique identifier (timestamp or UUID)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this temple was generated"
    )

    # Generation inputs
    seed_words: list[str] = Field(
        min_length=3,
        max_length=3,
        description="Three seed words provided by user"
    )

    # Generated narrative (drives everything)
    narrative: TempleNarrative = Field(
        description="Story and atmosphere generated from seeds"
    )

    # Asset file references (relative to project root)
    map_file: str = Field(
        description="Path to room sequence JSON (e.g., 'maps/temples/temple_abc123/map.json')"
    )
    audio_file: str = Field(
        description="Path to ambient music JSON (e.g., 'maps/temples/temple_abc123/audio.json')"
    )
    title_svg_file: str = Field(
        description="Path to title screen SVG (e.g., 'maps/temples/temple_abc123/title.svg')"
    )
    gameover_svg_file: str = Field(
        description="Path to game over SVG (e.g., 'maps/temples/temple_abc123/gameover.svg')"
    )

    # Metadata for browsing/selection
    estimated_duration_minutes: int = Field(
        default=10,
        description="Estimated playtime"
    )
    room_count: int = Field(
        description="Total number of rooms in sequence"
    )


class TempleStats(BaseModel):
    """Optional: Track statistics across runs (not game state)"""
    temple_id: str = Field(
        description="References TempleConfiguration.temple_id"
    )
    total_attempts: int = Field(
        default=0,
        description="How many times this temple has been played"
    )
    completions: int = Field(
        default=0,
        description="How many times this temple has been beaten"
    )
    fastest_time: Optional[float] = Field(
        default=None,
        description="Best completion time in seconds"
    )
    last_played: datetime = Field(
        default_factory=datetime.now,
        description="When this temple was last played"
    )


class TempleCatalog(BaseModel):
    """Index of all generated temples"""
    temples: list[TempleConfiguration] = Field(
        default_factory=list,
        description="All available temple configurations"
    )

    def add_temple(self, temple: TempleConfiguration):
        """Add a new temple to catalog"""
        self.temples.append(temple)

    def get_temple(self, temple_id: str) -> Optional[TempleConfiguration]:
        """Retrieve temple by ID"""
        return next((t for t in self.temples if t.temple_id == temple_id), None)

    def list_temples(self, sort_by: str = "created_at") -> list[TempleConfiguration]:
        """
        List all temples, optionally sorted.

        Args:
            sort_by: Sort key ('created_at' or 'room_count')

        Returns:
            Sorted list of temples
        """
        if sort_by == "created_at":
            return sorted(self.temples, key=lambda t: t.created_at, reverse=True)
        elif sort_by == "room_count":
            return sorted(self.temples, key=lambda t: t.room_count, reverse=True)
        return self.temples
