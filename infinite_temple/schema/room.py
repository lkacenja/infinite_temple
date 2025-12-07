from pydantic import BaseModel, Field
from typing import List


class Point(BaseModel):
    x: int = Field(..., ge=0, le=1000)
    y: int = Field(..., ge=0, le=1000)


class Segment(BaseModel):
    coord_1: Point
    coord_2: Point


class Room(BaseModel):
    id: int = Field(description="Unique identifier for the room in the series")
    walls: List[Segment] = Field(min_length=1, max_length=100, description="Walls making up the passage")


class HydratedRoomSequence(BaseModel):
    rooms: List[Room] = Field(min_length=2, description="List of rooms forming a connected sequence")


class RoomSequence(BaseModel):
    """Simple sequence of room template names"""
    rooms: List[str] = Field(
        min_length=2,
        description="List of room template names: 'start', 'horizontal', 'vertical', 'elbow_top_left', 'elbow_top_right', 'elbow_bottom_left', 'elbow_bottom_right', 'elbow_left_top', 'elbow_left_bottom', 'elbow_right_top', 'elbow_right_bottom'"
    )


# Template classes
class HorizontalPassage(Room):
    """Horizontal corridor running left to right across the map"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)
        y_start = (map_size - corridor_width) // 2
        y_end = y_start + corridor_width

        walls = [
            # Top wall
            Segment(coord_1=Point(x=0, y=y_start), coord_2=Point(x=map_size, y=y_start)),
            # Bottom wall
            Segment(coord_1=Point(x=0, y=y_end), coord_2=Point(x=map_size, y=y_end))
        ]

        super().__init__(id=room_id, walls=walls)


class VerticalPassage(Room):
    """Vertical corridor running top to bottom across the map"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)
        x_start = (map_size - corridor_width) // 2
        x_end = x_start + corridor_width

        walls = [
            # Left wall
            Segment(coord_1=Point(x=x_start, y=0), coord_2=Point(x=x_start, y=map_size)),
            # Right wall
            Segment(coord_1=Point(x=x_end, y=0), coord_2=Point(x=x_end, y=map_size))
        ]

        super().__init__(id=room_id, walls=walls)


class StartRoom(Room):
    """Starting room with a 400x400 square in the center and a horizontal passage exiting right"""

    def __init__(self, room_id: int, map_size: int = 1000):
        square_size = 400
        corridor_width = int(map_size * 0.2)

        # Center the square
        square_start = (map_size - square_size) // 2
        square_end = square_start + square_size

        # Corridor exits from the right side of the square, centered vertically
        corridor_y_start = (map_size - corridor_width) // 2
        corridor_y_end = corridor_y_start + corridor_width

        walls = [
            # Top wall of square (left portion, before corridor)
            Segment(coord_1=Point(x=square_start, y=square_start), coord_2=Point(x=square_end, y=square_start)),
            # Right wall of square (upper portion, above corridor)
            Segment(coord_1=Point(x=square_end, y=square_start), coord_2=Point(x=square_end, y=corridor_y_start)),
            # Top wall of corridor (from square to right edge)
            Segment(coord_1=Point(x=square_end, y=corridor_y_start), coord_2=Point(x=map_size, y=corridor_y_start)),
            # Bottom wall of corridor (from right edge to square)
            Segment(coord_1=Point(x=map_size, y=corridor_y_end), coord_2=Point(x=square_end, y=corridor_y_end)),
            # Right wall of square (lower portion, below corridor)
            Segment(coord_1=Point(x=square_end, y=corridor_y_end), coord_2=Point(x=square_end, y=square_end)),
            # Bottom wall of square
            Segment(coord_1=Point(x=square_end, y=square_end), coord_2=Point(x=square_start, y=square_end)),
            # Left wall of square
            Segment(coord_1=Point(x=square_start, y=square_end), coord_2=Point(x=square_start, y=square_start))
        ]

        super().__init__(id=room_id, walls=walls)


class ElbowBottomLeft(Room):
    """L-shaped corridor entering from bottom and exiting left"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Vertical section centered horizontally
        v_x_start = (map_size - corridor_width) // 2
        v_x_end = v_x_start + corridor_width

        # Horizontal section centered vertically
        h_y_start = (map_size - corridor_width) // 2
        h_y_end = h_y_start + corridor_width

        walls = [
            # Vertical section - left wall (from bottom to elbow)
            Segment(coord_1=Point(x=v_x_start, y=map_size), coord_2=Point(x=v_x_start, y=h_y_end)),
            # Vertical section - right wall (from bottom to elbow)
            Segment(coord_1=Point(x=v_x_end, y=map_size), coord_2=Point(x=v_x_end, y=h_y_start)),
            # Horizontal section - bottom wall (from elbow to left edge)
            Segment(coord_1=Point(x=v_x_start, y=h_y_end), coord_2=Point(x=0, y=h_y_end)),
            # Horizontal section - top wall (from left edge to elbow)
            Segment(coord_1=Point(x=0, y=h_y_start), coord_2=Point(x=v_x_end, y=h_y_start))
        ]

        super().__init__(id=room_id, walls=walls)


class ElbowLeftBottom(ElbowBottomLeft):
    def __init__(self, room_id: int, map_size: int = 1000):
        super().__init__(room_id, map_size)

class ElbowBottomRight(Room):
    """L-shaped corridor entering from bottom and exiting right"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Vertical section centered horizontally
        v_x_start = (map_size - corridor_width) // 2
        v_x_end = v_x_start + corridor_width

        # Horizontal section centered vertically
        h_y_start = (map_size - corridor_width) // 2
        h_y_end = h_y_start + corridor_width

        walls = [
            # Vertical section - left wall (from bottom to elbow)
            Segment(coord_1=Point(x=v_x_start, y=map_size), coord_2=Point(x=v_x_start, y=h_y_start)),
            # Vertical section - right wall (from bottom to elbow)
            Segment(coord_1=Point(x=v_x_end, y=map_size), coord_2=Point(x=v_x_end, y=h_y_end)),
            # Horizontal section - bottom wall (from elbow to right edge)
            Segment(coord_1=Point(x=v_x_start, y=h_y_start), coord_2=Point(x=map_size, y=h_y_start)),
            # Horizontal section - top wall (from right edge to elbow)
            Segment(coord_1=Point(x=map_size, y=h_y_end), coord_2=Point(x=v_x_end, y=h_y_end))
        ]

        super().__init__(id=room_id, walls=walls)


class ElbowLeftTop(Room):
    """L-shaped corridor entering from left and exiting top"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Horizontal section centered vertically
        h_y_start = (map_size - corridor_width) // 2
        h_y_end = h_y_start + corridor_width

        # Vertical section centered horizontally
        v_x_start = (map_size - corridor_width) // 2
        v_x_end = v_x_start + corridor_width

        walls = [
            # Horizontal section - top wall (from left edge to elbow)
            Segment(coord_1=Point(x=0, y=h_y_start), coord_2=Point(x=v_x_start, y=h_y_start)),
            # Horizontal section - bottom wall (from left edge to elbow)
            Segment(coord_1=Point(x=0, y=h_y_end), coord_2=Point(x=v_x_end, y=h_y_end)),
            # Vertical section - left wall (from elbow to top edge)
            Segment(coord_1=Point(x=v_x_start, y=h_y_start), coord_2=Point(x=v_x_start, y=0)),
            # Vertical section - right wall (from elbow to top edge)
            Segment(coord_1=Point(x=v_x_end, y=h_y_end), coord_2=Point(x=v_x_end, y=0))
        ]

        super().__init__(id=room_id, walls=walls)

class ElbowTopLeft(ElbowLeftTop):
    def __init__(self, room_id: int, map_size: int = 1000):
        super().__init__(room_id, map_size=map_size)


class ElbowRightTop(Room):
    """L-shaped corridor entering from right and exiting top"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Horizontal section centered vertically
        h_y_start = (map_size - corridor_width) // 2
        h_y_end = h_y_start + corridor_width

        # Vertical section centered horizontally
        v_x_start = (map_size - corridor_width) // 2
        v_x_end = v_x_start + corridor_width

        walls = [
            # Horizontal section - top wall (from right edge to elbow)
            Segment(coord_1=Point(x=map_size, y=h_y_start), coord_2=Point(x=v_x_end, y=h_y_start)),
            # Horizontal section - bottom wall (from right edge to elbow)
            Segment(coord_1=Point(x=map_size, y=h_y_end), coord_2=Point(x=v_x_start, y=h_y_end)),
            # Vertical section - left wall (from elbow to top edge)
            Segment(coord_1=Point(x=v_x_start, y=h_y_end), coord_2=Point(x=v_x_start, y=0)),
            # Vertical section - right wall (from elbow to top edge)
            Segment(coord_1=Point(x=v_x_end, y=h_y_start), coord_2=Point(x=v_x_end, y=0))
        ]

        super().__init__(id=room_id, walls=walls)

class ElbowTopRight(ElbowRightTop):
    def __init__(self, room_id: int, map_size: int = 1000):
        super().__init__(room_id, map_size)


class ElbowRightBottom(Room):
    """L-shaped corridor entering from right and exiting bottom"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Horizontal section centered vertically
        h_y_start = (map_size - corridor_width) // 2
        h_y_end = h_y_start + corridor_width

        # Vertical section centered horizontally
        v_x_start = (map_size - corridor_width) // 2
        v_x_end = v_x_start + corridor_width

        walls = [
            # Horizontal section - top wall (from right edge to elbow)
            Segment(coord_1=Point(x=map_size, y=h_y_start), coord_2=Point(x=v_x_start, y=h_y_start)),
            # Horizontal section - bottom wall (from right edge to elbow)
            Segment(coord_1=Point(x=map_size, y=h_y_end), coord_2=Point(x=v_x_end, y=h_y_end)),
            # Vertical section - left wall (from elbow to bottom edge)
            Segment(coord_1=Point(x=v_x_start, y=h_y_start), coord_2=Point(x=v_x_start, y=map_size)),
            # Vertical section - right wall (from bottom edge to elbow)
            Segment(coord_1=Point(x=v_x_end, y=map_size), coord_2=Point(x=v_x_end, y=h_y_end))
        ]

        super().__init__(id=room_id, walls=walls)


class AntechamberVertical(Room):
    """Large rectangular chamber with vertical corridors entering from top and exiting bottom"""

    def __init__(self, room_id: int, map_size: int = 1000, chamber_width: int = 700, chamber_height: int = 700):
        corridor_width = int(map_size * 0.2)

        # Center the chamber
        chamber_x_start = (map_size - chamber_width) // 2
        chamber_x_end = chamber_x_start + chamber_width
        chamber_y_start = (map_size - chamber_height) // 2
        chamber_y_end = chamber_y_start + chamber_height

        # Vertical corridors centered horizontally
        corridor_x_start = (map_size - corridor_width) // 2
        corridor_x_end = corridor_x_start + corridor_width

        walls = [
            # Top corridor - left wall (from top edge to chamber)
            Segment(coord_1=Point(x=corridor_x_start, y=0), coord_2=Point(x=corridor_x_start, y=chamber_y_start)),
            # Top corridor - right wall (from top edge to chamber)
            Segment(coord_1=Point(x=corridor_x_end, y=0), coord_2=Point(x=corridor_x_end, y=chamber_y_start)),

            # Chamber - top wall (left side of corridor entrance)
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start),
                    coord_2=Point(x=corridor_x_start, y=chamber_y_start)),
            # Chamber - top wall (right side of corridor entrance)
            Segment(coord_1=Point(x=corridor_x_end, y=chamber_y_start),
                    coord_2=Point(x=chamber_x_end, y=chamber_y_start)),

            # Chamber - right wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),

            # Chamber - bottom wall (right side of corridor exit)
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_end), coord_2=Point(x=corridor_x_end, y=chamber_y_end)),
            # Chamber - bottom wall (left side of corridor exit)
            Segment(coord_1=Point(x=corridor_x_start, y=chamber_y_end),
                    coord_2=Point(x=chamber_x_start, y=chamber_y_end)),

            # Chamber - left wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_end),
                    coord_2=Point(x=chamber_x_start, y=chamber_y_start)),

            # Bottom corridor - left wall (from chamber to bottom edge)
            Segment(coord_1=Point(x=corridor_x_start, y=chamber_y_end), coord_2=Point(x=corridor_x_start, y=map_size)),
            # Bottom corridor - right wall (from chamber to bottom edge)
            Segment(coord_1=Point(x=corridor_x_end, y=chamber_y_end), coord_2=Point(x=corridor_x_end, y=map_size))
        ]

        super().__init__(id=room_id, walls=walls)


class AntechamberHorizontal(Room):
    """Large rectangular chamber with horizontal corridors entering from left and exiting right"""

    def __init__(self, room_id: int, map_size: int = 1000, chamber_width: int = 700, chamber_height: int = 700):
        corridor_width = int(map_size * 0.2)

        # Center the chamber
        chamber_x_start = (map_size - chamber_width) // 2
        chamber_x_end = chamber_x_start + chamber_width
        chamber_y_start = (map_size - chamber_height) // 2
        chamber_y_end = chamber_y_start + chamber_height

        # Horizontal corridors centered vertically
        corridor_y_start = (map_size - corridor_width) // 2
        corridor_y_end = corridor_y_start + corridor_width

        walls = [
            # Left corridor - top wall (from left edge to chamber)
            Segment(coord_1=Point(x=0, y=corridor_y_start), coord_2=Point(x=chamber_x_start, y=corridor_y_start)),
            # Left corridor - bottom wall (from left edge to chamber)
            Segment(coord_1=Point(x=0, y=corridor_y_end), coord_2=Point(x=chamber_x_start, y=corridor_y_end)),

            # Chamber - left wall (top side of corridor entrance)
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start),
                    coord_2=Point(x=chamber_x_start, y=corridor_y_start)),
            # Chamber - left wall (bottom side of corridor entrance)
            Segment(coord_1=Point(x=chamber_x_start, y=corridor_y_end),
                    coord_2=Point(x=chamber_x_start, y=chamber_y_end)),

            # Chamber - bottom wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_end), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),

            # Chamber - right wall (bottom side of corridor exit)
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_end), coord_2=Point(x=chamber_x_end, y=corridor_y_end)),
            # Chamber - right wall (top side of corridor exit)
            Segment(coord_1=Point(x=chamber_x_end, y=corridor_y_start),
                    coord_2=Point(x=chamber_x_end, y=chamber_y_start)),

            # Chamber - top wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_start),
                    coord_2=Point(x=chamber_x_start, y=chamber_y_start)),

            # Right corridor - top wall (from chamber to right edge)
            Segment(coord_1=Point(x=chamber_x_end, y=corridor_y_start), coord_2=Point(x=map_size, y=corridor_y_start)),
            # Right corridor - bottom wall (from chamber to right edge)
            Segment(coord_1=Point(x=chamber_x_end, y=corridor_y_end), coord_2=Point(x=map_size, y=corridor_y_end))
        ]

        super().__init__(id=room_id, walls=walls)

room_classes = {
    "start": "StartRoom",
    "horizontal": "HorizontalPassage",
    "vertical": "VerticalPassage",
    "elbow_top_left": "ElbowTopLeft",
    "elbow_top_right": "ElbowTopRight",
    "elbow_bottom_left": "ElbowBottomLeft",
    "elbow_bottom_right": "ElbowBottomRight",
    "elbow_left_top": "ElbowLeftTop",
    "elbow_left_bottom": "ElbowLeftBottom",
    "elbow_right_top": "ElbowRightTop",
    "elbow_right_bottom": "ElbowRightBottom",
    "antechamber_vertical": "AntechamberVertical",
    "antechamber_horizontal": "AntechamberHorizontal"
}
