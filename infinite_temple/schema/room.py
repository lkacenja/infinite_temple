from typing import List

from pydantic import BaseModel, Field

class Segment(BaseModel):
    x_1: int = Field(description="X coordinate of the first point of the segment", ge=0, le=1000)
    y_1: int = Field(description="Y coordinate of the first point of the segment", ge=0, le=1000)
    x_2: int = Field(description="X coordinate of the second point of the segment", ge=0, le=1000)
    y_2: int = Field(description="Y coordinate of the second point of the segment", ge=0, le=1000)

class Room(BaseModel):
    walls: List[Segment] = Field(description="Walls that make up a passage through the room.", min_length=20, max_length=100)