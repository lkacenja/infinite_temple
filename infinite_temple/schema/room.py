from typing import List, Literal

from pydantic import BaseModel, Field

class Point(BaseModel):
    x: int = Field(..., ge=0, le=1000)
    y: int = Field(..., ge=0, le=1000)

class Segment(BaseModel):
    coord_1: Point
    coord_2: Point

class Room(BaseModel):
    id: int = Field(description="Unique identifier for the room in the series")
    walls: List[Segment] = Field(min_length=10, max_length=100, description="Walls making up the passage")

class MapSequence(BaseModel):
    rooms: List[Room] = Field(min_length=2, description="List of rooms forming a connected sequence")