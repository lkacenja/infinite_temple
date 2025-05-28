from typing import Literal

from pydantic import BaseModel, conlist, conint


class Point(BaseModel):
    x: conint(ge=0, le=10)
    y: conint(ge=0, le=10)
    m: Literal['e', 'w', 'h']


class GridDrawing(BaseModel):
    points: conlist(Point)
