from typing import List

from pydantic import BaseModel, Field



class Note(BaseModel):
    """A single note in a musical sequence."""
    pitch: str = Field(
        description="Note pitch in format: 'c4', 'd#5', 'eb3', or 'r' for rest. "
                    "Format is: note letter (a-g) + optional accidental (# or b) + octave (3-6)"
    )
    duration: int = Field(
        description="Note duration: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth. "
                    "Use negative for dotted notes: -4=dotted quarter, -2=dotted half"
    )


class Voice(BaseModel):
    """A single melodic voice/layer in the composition."""
    name: str = Field(description="Descriptive name for this voice (e.g., 'melody', 'bass', 'pad')")
    notes: List[Note] = Field(description="Sequence of notes for this voice")


class AmbientMusic(BaseModel):
    """A complete ambient music composition with multiple voices."""
    title: str = Field(description="Descriptive title for the piece")
    key: str = Field(description="Musical key (e.g., 'C Major', 'A Minor', 'D Dorian')")
    tempo_bpm: int = Field(
        ge=60,
        le=120,
        description="Tempo in beats per minute. 60-80 for calm, 80-100 for neutral, 100-120 for energetic"
    )
    mood: str = Field(description="Brief mood description (e.g., 'peaceful and natural', 'dark and ominous')")
    duration_seconds: float = Field(description="Actual duration of the piece in seconds")
    voices: List[Voice] = Field(
        min_length=2,
        max_length=4,
        description="2-4 melodic voices that harmonize together"
    )
