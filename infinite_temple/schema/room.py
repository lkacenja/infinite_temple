from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Point(BaseModel):
    x: int = Field(..., ge=0, le=10000)
    y: int = Field(..., ge=0, le=10000)


class Rectangle(BaseModel):
    """Rectangular area for portal triggers"""
    x: int = Field(..., description="Top-left x coordinate")
    y: int = Field(..., description="Top-left y coordinate")
    width: int = Field(..., gt=0, description="Width of rectangle")
    height: int = Field(..., gt=0, description="Height of rectangle")

    def contains(self, px: float, py: float) -> bool:
        """Check if point (px, py) is inside this rectangle"""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)


class Segment(BaseModel):
    coord_1: Point
    coord_2: Point


class Portal(BaseModel):
    """Defines an entrance/exit in a room"""
    id: str = Field(..., description="Unique identifier within the room (e.g., 'north', 'south', 'east_upper')")
    trigger_rect: Rectangle = Field(..., description="Area where player triggers transition")
    spawn_point: Point = Field(..., description="Where player spawns when entering through this portal")
    direction: str = Field(..., description="Direction for player repositioning: 'UP', 'DOWN', 'LEFT', 'RIGHT'")


class RoomTemplate(BaseModel):
    """Data-driven room definition"""
    name: str = Field(..., description="Template name")
    walls: List[Segment] = Field(..., min_length=1, max_length=100, description="Walls making up the room")
    portals: Dict[str, Portal] = Field(..., description="Portal ID -> Portal object")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional room data (mood, difficulty, etc.)")


class RoomConnection(BaseModel):
    """Explicit connection between two rooms"""
    from_room: int = Field(..., description="Source room index")
    from_portal: str = Field(..., description="Source portal ID")
    to_room: int = Field(..., description="Destination room index")
    to_portal: str = Field(..., description="Destination portal ID")


class RoomSequenceFullGeometry(BaseModel):
    """Portal-based room sequence with explicit connections and full geometry"""
    rooms: List[RoomTemplate] = Field(min_length=1, description="List of room templates")
    connections: List[RoomConnection] = Field(min_length=0, description="Explicit portal connections between rooms")


class Room(BaseModel):
    id: int = Field(description="Unique identifier for the room in the series")
    walls: List[Segment] = Field(min_length=1, max_length=100, description="Walls making up the passage")


class BranchPath(BaseModel):
    """Represents a branching path off the main sequence"""
    fork_main_room_index: int = Field(description="Index in main path where branch starts")
    fork_portal: str = Field(description="Direction of branch portal (north/south/east/west)")
    branch_rooms: List[str] = Field(description="Sequence of room template names for this branch")
    rejoin_main_room_index: Optional[int] = Field(default=None, description="Index where branch rejoins main path (None for dead-end)")
    rejoin_portal: Optional[str] = Field(default=None, description="Direction of rejoin portal")


class RoomSequence(BaseModel):
    """Simple sequence of room template names"""
    rooms: List[str] = Field(
        min_length=2,
        description="List of room template names: 'start', 'horizontal', 'vertical', 'elbow_top_left', 'elbow_top_right', 'elbow_bottom_left', 'elbow_bottom_right', 'elbow_left_top', 'elbow_left_bottom', 'elbow_right_top', 'elbow_right_bottom'"
    )
    branch_paths: Optional[List[BranchPath]] = Field(default=None, description="Branch paths forking from main sequence")


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


class DeadEndWest(Room):
    """Dead end with chamber - entered from west, chamber on east side"""

    def __init__(self, room_id: int, map_size: int = 1000):
        chamber_size = 400
        corridor_width = int(map_size * 0.2)

        # Corridor bounds (centered vertically)
        corridor_y_start = (map_size - corridor_width) // 2
        corridor_y_end = corridor_y_start + corridor_width

        # Chamber on the east side
        chamber_x_start = map_size - chamber_size - 100  # 500
        chamber_x_end = map_size - 100  # 900
        chamber_y_start = (map_size - chamber_size) // 2  # 300
        chamber_y_end = chamber_y_start + chamber_size  # 700

        walls = [
            # Corridor top wall (from west edge to chamber)
            Segment(coord_1=Point(x=0, y=corridor_y_start), coord_2=Point(x=chamber_x_start, y=corridor_y_start)),
            # Chamber top wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=chamber_y_start)),
            # Chamber right wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),
            # Chamber bottom wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_end), coord_2=Point(x=chamber_x_start, y=chamber_y_end)),
            # Corridor bottom wall (from chamber to west edge)
            Segment(coord_1=Point(x=chamber_x_start, y=corridor_y_end), coord_2=Point(x=0, y=corridor_y_end)),
            # Chamber left wall upper (from chamber top to corridor)
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start), coord_2=Point(x=chamber_x_start, y=corridor_y_start)),
            # Chamber left wall lower (from corridor to chamber bottom)
            Segment(coord_1=Point(x=chamber_x_start, y=corridor_y_end), coord_2=Point(x=chamber_x_start, y=chamber_y_end)),
        ]

        super().__init__(id=room_id, walls=walls)


class DeadEndEast(Room):
    """Dead end with chamber - entered from east, chamber on west side"""

    def __init__(self, room_id: int, map_size: int = 1000):
        chamber_size = 400
        corridor_width = int(map_size * 0.2)

        # Corridor bounds (centered vertically)
        corridor_y_start = (map_size - corridor_width) // 2
        corridor_y_end = corridor_y_start + corridor_width

        # Chamber on the west side
        chamber_x_start = 100  # 100
        chamber_x_end = 100 + chamber_size  # 500
        chamber_y_start = (map_size - chamber_size) // 2  # 300
        chamber_y_end = chamber_y_start + chamber_size  # 700

        walls = [
            # Corridor top wall (from east edge to chamber)
            Segment(coord_1=Point(x=map_size, y=corridor_y_start), coord_2=Point(x=chamber_x_end, y=corridor_y_start)),
            # Chamber top wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_start), coord_2=Point(x=chamber_x_start, y=chamber_y_start)),
            # Chamber left wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start), coord_2=Point(x=chamber_x_start, y=chamber_y_end)),
            # Chamber bottom wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_end), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),
            # Corridor bottom wall (from chamber to east edge)
            Segment(coord_1=Point(x=chamber_x_end, y=corridor_y_end), coord_2=Point(x=map_size, y=corridor_y_end)),
            # Chamber right wall upper (from chamber top to corridor)
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=corridor_y_start)),
            # Chamber right wall lower (from corridor to chamber bottom)
            Segment(coord_1=Point(x=chamber_x_end, y=corridor_y_end), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),
        ]

        super().__init__(id=room_id, walls=walls)


class DeadEndNorth(Room):
    """Dead end with chamber - entered from north, chamber on south side"""

    def __init__(self, room_id: int, map_size: int = 1000):
        chamber_size = 400
        corridor_width = int(map_size * 0.2)

        # Corridor bounds (centered horizontally)
        corridor_x_start = (map_size - corridor_width) // 2
        corridor_x_end = corridor_x_start + corridor_width

        # Chamber on the south side
        chamber_y_start = map_size - chamber_size - 100  # 500
        chamber_y_end = map_size - 100  # 900
        chamber_x_start = (map_size - chamber_size) // 2  # 300
        chamber_x_end = chamber_x_start + chamber_size  # 700

        walls = [
            # Corridor left wall (from north edge to chamber)
            Segment(coord_1=Point(x=corridor_x_start, y=0), coord_2=Point(x=corridor_x_start, y=chamber_y_start)),
            # Chamber left wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start), coord_2=Point(x=chamber_x_start, y=chamber_y_end)),
            # Chamber bottom wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_end), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),
            # Chamber right wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_end), coord_2=Point(x=chamber_x_end, y=chamber_y_start)),
            # Corridor right wall (from chamber to north edge)
            Segment(coord_1=Point(x=corridor_x_end, y=chamber_y_start), coord_2=Point(x=corridor_x_end, y=0)),
            # Chamber top wall left (from chamber left to corridor)
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start), coord_2=Point(x=corridor_x_start, y=chamber_y_start)),
            # Chamber top wall right (from corridor to chamber right)
            Segment(coord_1=Point(x=corridor_x_end, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=chamber_y_start)),
        ]

        super().__init__(id=room_id, walls=walls)


class DeadEndSouth(Room):
    """Dead end with chamber - entered from south, chamber on north side"""

    def __init__(self, room_id: int, map_size: int = 1000):
        chamber_size = 400
        corridor_width = int(map_size * 0.2)

        # Corridor bounds (centered horizontally)
        corridor_x_start = (map_size - corridor_width) // 2
        corridor_x_end = corridor_x_start + corridor_width

        # Chamber on the north side
        chamber_y_start = 100  # 100
        chamber_y_end = 100 + chamber_size  # 500
        chamber_x_start = (map_size - chamber_size) // 2  # 300
        chamber_x_end = chamber_x_start + chamber_size  # 700

        walls = [
            # Corridor left wall (from south edge to chamber)
            Segment(coord_1=Point(x=corridor_x_start, y=map_size), coord_2=Point(x=corridor_x_start, y=chamber_y_end)),
            # Chamber left wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_end), coord_2=Point(x=chamber_x_start, y=chamber_y_start)),
            # Chamber top wall
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=chamber_y_start)),
            # Chamber right wall
            Segment(coord_1=Point(x=chamber_x_end, y=chamber_y_start), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),
            # Corridor right wall (from chamber to south edge)
            Segment(coord_1=Point(x=corridor_x_end, y=chamber_y_end), coord_2=Point(x=corridor_x_end, y=map_size)),
            # Chamber bottom wall left (from chamber left to corridor)
            Segment(coord_1=Point(x=chamber_x_start, y=chamber_y_end), coord_2=Point(x=corridor_x_start, y=chamber_y_end)),
            # Chamber bottom wall right (from corridor to chamber right)
            Segment(coord_1=Point(x=corridor_x_end, y=chamber_y_end), coord_2=Point(x=chamber_x_end, y=chamber_y_end)),
        ]

        super().__init__(id=room_id, walls=walls)


class TJunctionHorizontalNorth(Room):
    """T-junction: horizontal corridor (west-east) with north branch"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Horizontal corridor bounds
        h_y_start = (map_size - corridor_width) // 2  # 400
        h_y_end = h_y_start + corridor_width  # 600

        # North branch bounds (centered horizontally)
        n_x_start = (map_size - corridor_width) // 2  # 400
        n_x_end = n_x_start + corridor_width  # 600

        walls = [
            # Bottom wall (full width)
            Segment(coord_1=Point(x=0, y=h_y_end), coord_2=Point(x=map_size, y=h_y_end)),
            # Top wall left segment (up to north branch)
            Segment(coord_1=Point(x=0, y=h_y_start), coord_2=Point(x=n_x_start, y=h_y_start)),
            # Top wall right segment (after north branch)
            Segment(coord_1=Point(x=n_x_end, y=h_y_start), coord_2=Point(x=map_size, y=h_y_start)),
            # North branch left wall
            Segment(coord_1=Point(x=n_x_start, y=0), coord_2=Point(x=n_x_start, y=h_y_start)),
            # North branch right wall
            Segment(coord_1=Point(x=n_x_end, y=0), coord_2=Point(x=n_x_end, y=h_y_start))
        ]

        super().__init__(id=room_id, walls=walls)


class TJunctionHorizontalSouth(Room):
    """T-junction: horizontal corridor (west-east) with south branch"""

    def __init__(self, room_id: int, map_size: int = 1000):
        corridor_width = int(map_size * 0.2)

        # Horizontal corridor bounds
        h_y_start = (map_size - corridor_width) // 2  # 400
        h_y_end = h_y_start + corridor_width  # 600

        # South branch bounds (centered horizontally)
        s_x_start = (map_size - corridor_width) // 2  # 400
        s_x_end = s_x_start + corridor_width  # 600

        walls = [
            # Top wall (full width)
            Segment(coord_1=Point(x=0, y=h_y_start), coord_2=Point(x=map_size, y=h_y_start)),
            # Bottom wall left segment (up to south branch)
            Segment(coord_1=Point(x=0, y=h_y_end), coord_2=Point(x=s_x_start, y=h_y_end)),
            # Bottom wall right segment (after south branch)
            Segment(coord_1=Point(x=s_x_end, y=h_y_end), coord_2=Point(x=map_size, y=h_y_end)),
            # South branch left wall
            Segment(coord_1=Point(x=s_x_start, y=h_y_end), coord_2=Point(x=s_x_start, y=map_size)),
            # South branch right wall
            Segment(coord_1=Point(x=s_x_end, y=h_y_end), coord_2=Point(x=s_x_end, y=map_size))
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
    "antechamber_horizontal": "AntechamberHorizontal",
    "dead_end_west": "DeadEndWest",
    "dead_end_east": "DeadEndEast",
    "dead_end_north": "DeadEndNorth",
    "dead_end_south": "DeadEndSouth",
    "tjunction_horizontal_north": "TJunctionHorizontalNorth",
    "tjunction_horizontal_south": "TJunctionHorizontalSouth"
}


# Helper functions for creating portals
def create_horizontal_portals(map_size: int = 1000) -> Dict[str, Portal]:
    """Create portals for horizontal passage (west and east)"""
    corridor_width = int(map_size * 0.2)
    corridor_y_start = (map_size - corridor_width) // 2

    # Portal trigger zones extend beyond room boundaries
    trigger_margin = 50

    return {
        "west": Portal(
            id="west",
            trigger_rect=Rectangle(x=-trigger_margin, y=corridor_y_start, width=trigger_margin, height=corridor_width),
            spawn_point=Point(x=10, y=map_size // 2),
            direction="RIGHT"
        ),
        "east": Portal(
            id="east",
            trigger_rect=Rectangle(x=map_size, y=corridor_y_start, width=trigger_margin, height=corridor_width),
            spawn_point=Point(x=map_size - 10, y=map_size // 2),
            direction="LEFT"
        )
    }


def create_vertical_portals(map_size: int = 1000) -> Dict[str, Portal]:
    """Create portals for vertical passage (north and south)"""
    corridor_width = int(map_size * 0.2)
    corridor_x_start = (map_size - corridor_width) // 2

    trigger_margin = 50

    return {
        "north": Portal(
            id="north",
            trigger_rect=Rectangle(x=corridor_x_start, y=-trigger_margin, width=corridor_width, height=trigger_margin),
            spawn_point=Point(x=map_size // 2, y=10),
            direction="DOWN"
        ),
        "south": Portal(
            id="south",
            trigger_rect=Rectangle(x=corridor_x_start, y=map_size, width=corridor_width, height=trigger_margin),
            spawn_point=Point(x=map_size // 2, y=map_size - 10),
            direction="UP"
        )
    }


def add_portal_to_template(template: RoomTemplate, portal_id: str, map_size: int):
    """Dynamically add a portal to an existing room template and create wall opening"""
    all_portals = {
        **create_horizontal_portals(map_size),
        **create_vertical_portals(map_size)
    }
    if portal_id not in all_portals:
        return

    template.portals[portal_id] = all_portals[portal_id]

    # Create opening in walls for this portal
    corridor_width = int(map_size * 0.2)
    center = map_size // 2

    # Define the opening region based on portal direction
    # We need to find walls that block access to the portal edge
    if portal_id == "north":
        # Opening centered horizontally, need to split horizontal walls above center
        opening_start = (map_size - corridor_width) // 2
        opening_end = opening_start + corridor_width
        is_blocking_wall = lambda w: abs(w.coord_1.y - w.coord_2.y) < 10 and w.coord_1.y < center
        get_pos = lambda w: (min(w.coord_1.x, w.coord_2.x), max(w.coord_1.x, w.coord_2.x))
    elif portal_id == "south":
        opening_start = (map_size - corridor_width) // 2
        opening_end = opening_start + corridor_width
        is_blocking_wall = lambda w: abs(w.coord_1.y - w.coord_2.y) < 10 and w.coord_1.y > center
        get_pos = lambda w: (min(w.coord_1.x, w.coord_2.x), max(w.coord_1.x, w.coord_2.x))
    elif portal_id == "west":
        opening_start = (map_size - corridor_width) // 2
        opening_end = opening_start + corridor_width
        is_blocking_wall = lambda w: abs(w.coord_1.x - w.coord_2.x) < 10 and w.coord_1.x < center
        get_pos = lambda w: (min(w.coord_1.y, w.coord_2.y), max(w.coord_1.y, w.coord_2.y))
    elif portal_id == "east":
        opening_start = (map_size - corridor_width) // 2
        opening_end = opening_start + corridor_width
        is_blocking_wall = lambda w: abs(w.coord_1.x - w.coord_2.x) < 10 and w.coord_1.x > center
        get_pos = lambda w: (min(w.coord_1.y, w.coord_2.y), max(w.coord_1.y, w.coord_2.y))
    else:
        return

    # Process walls - split any that block the opening
    new_walls = []
    for wall in template.walls:
        if not is_blocking_wall(wall):
            new_walls.append(wall)
            continue

        wall_start, wall_end = get_pos(wall)

        # Check if wall overlaps with opening
        if wall_end <= opening_start or wall_start >= opening_end:
            # Wall doesn't overlap with opening, keep it
            new_walls.append(wall)
        else:
            # Wall overlaps - split it around the opening
            if portal_id in ["north", "south"]:
                y = wall.coord_1.y
                # Left segment (if any)
                if wall_start < opening_start:
                    new_walls.append(Segment(
                        coord_1=Point(x=wall_start, y=y),
                        coord_2=Point(x=opening_start, y=y)
                    ))
                # Right segment (if any)
                if wall_end > opening_end:
                    new_walls.append(Segment(
                        coord_1=Point(x=opening_end, y=y),
                        coord_2=Point(x=wall_end, y=y)
                    ))
            else:  # west, east
                x = wall.coord_1.x
                # Top segment (if any)
                if wall_start < opening_start:
                    new_walls.append(Segment(
                        coord_1=Point(x=x, y=wall_start),
                        coord_2=Point(x=x, y=opening_start)
                    ))
                # Bottom segment (if any)
                if wall_end > opening_end:
                    new_walls.append(Segment(
                        coord_1=Point(x=x, y=opening_end),
                        coord_2=Point(x=x, y=wall_end)
                    ))

    template.walls = new_walls


def room_to_template(room, template_name: str, portal_ids: List[str], map_size: int = 1000) -> RoomTemplate:
    """Convert a Room instance to a RoomTemplate with specified portals

    Note: The portal system supports any number of portals per room, enabling:
    - Simple passages (2 portals)
    - Junctions/forks (3+ portals)
    - Dead ends (1 portal)
    - Complex interconnected spaces (4+ portals)
    """
    all_portals = {
        **create_horizontal_portals(map_size),
        **create_vertical_portals(map_size)
    }

    portals = {pid: all_portals[pid] for pid in portal_ids if pid in all_portals}

    return RoomTemplate(
        name=template_name,
        walls=room.walls,
        portals=portals,
        metadata={}
    )


# Portal mapping for each room type (ordered as: [entrance, exit])
ROOM_PORTAL_MAP = {
    "start": ["east"],  # Exits east
    "horizontal": ["west", "east"],  # Enters west, exits east
    "vertical": ["north", "south"],  # Enters north, exits south
    "elbow_top_left": ["west", "north"],  # Enters west, exits north (ElbowLeftTop)
    "elbow_top_right": ["east", "north"],  # Enters east, exits north (ElbowRightTop)
    "elbow_bottom_left": ["south", "west"],  # Enters south, exits west
    "elbow_bottom_right": ["south", "east"],  # Enters south, exits east
    "elbow_left_top": ["west", "north"],  # Enters west, exits north
    "elbow_left_bottom": ["west", "south"],  # Enters west, exits south
    "elbow_right_top": ["east", "north"],  # Enters east, exits north
    "elbow_right_bottom": ["east", "south"],  # Enters east, exits south
    "antechamber_vertical": ["north", "south"],  # Enters north, exits south
    "antechamber_horizontal": ["west", "east"],  # Enters west, exits east
    "dead_end_west": ["west"],  # Enters west, no exit
    "dead_end_east": ["east"],  # Enters east, no exit
    "dead_end_north": ["north"],  # Enters north, no exit
    "dead_end_south": ["south"],  # Enters south, no exit
    "tjunction_horizontal_north": ["west", "east", "north"],  # Horizontal with north branch
    "tjunction_horizontal_south": ["west", "east", "south"]  # Horizontal with south branch
}


def validate_room_sequence(rooms: list[str]) -> tuple[bool, str]:
    """Validate that a room sequence has valid connections.

    Args:
        rooms: List of room template names

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not rooms:
        return False, "Empty room sequence"

    if rooms[0] != "start":
        return False, f"Sequence must start with 'start', got '{rooms[0]}'"

    opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}

    # Track which portal we entered each room through
    current_entry = None

    for i in range(len(rooms) - 1):
        from_room = rooms[i]
        to_room = rooms[i + 1]

        from_portals = ROOM_PORTAL_MAP.get(from_room, [])
        to_portals = ROOM_PORTAL_MAP.get(to_room, [])

        if not from_portals:
            return False, f"Unknown room type at index {i}: '{from_room}'"
        if not to_portals:
            return False, f"Unknown room type at index {i+1}: '{to_room}'"

        # Determine exit portal of from_room
        if from_room.startswith("tjunction_horizontal"):
            # T-junctions on main path behave like horizontal corridors
            if current_entry == "west":
                from_exit = "east"
            elif current_entry == "east":
                from_exit = "west"
            else:
                from_exit = "east"
        elif current_entry and current_entry in from_portals and len(from_portals) == 2:
            from_exit = from_portals[1] if from_portals[0] == current_entry else from_portals[0]
        else:
            from_exit = from_portals[-1] if from_portals else None

        if not from_exit:
            return False, f"Cannot determine exit for room {i} ('{from_room}')"

        # Next room must enter from opposite direction
        to_entry = opposite.get(from_exit)
        if to_entry not in to_portals:
            return False, f"Invalid connection at index {i}: '{from_room}' exits {from_exit}, but '{to_room}' has no {to_entry} portal"

        current_entry = to_entry

    return True, ""


def infer_connection_direction(from_template: str, to_template: str, from_entry: str = None) -> tuple[str, str]:
    """Infer which portals connect based on room template names

    Args:
        from_template: The template name of the source room
        to_template: The template name of the destination room
        from_entry: Which portal was used to ENTER the from_room (to determine which portal to exit)

    Returns: (from_portal_id, to_portal_id)
    """
    from_portals = ROOM_PORTAL_MAP.get(from_template, [])
    to_portals = ROOM_PORTAL_MAP.get(to_template, [])

    # Special handling for T-junction rooms on the main path
    # They should behave like horizontal corridors (west↔east)
    if from_template.startswith("tjunction_horizontal"):
        if from_entry == "west":
            from_exit = "east"
        elif from_entry == "east":
            from_exit = "west"
        else:
            from_exit = "east"  # Default for first connection
    elif from_entry and from_entry in from_portals and len(from_portals) == 2:
        # For rooms with 2 portals, exit through the OTHER portal
        from_exit = from_portals[1] if from_portals[0] == from_entry else from_portals[0]
    else:
        # Use the last portal as the exit (works for start room and first connection)
        from_exit = from_portals[-1] if from_portals else None

    if not from_exit:
        raise ValueError(f"Cannot determine exit portal for {from_template}")

    # The entrance portal of to_room must be opposite to the exit of from_room
    # east ↔ west, north ↔ south
    opposite_map = {
        "east": "west",
        "west": "east",
        "north": "south",
        "south": "north"
    }

    to_entrance = opposite_map.get(from_exit)

    if to_entrance and to_entrance in to_portals:
        return (from_exit, to_entrance)

    raise ValueError(f"Cannot connect {from_template}.{from_exit} to {to_template} (no {to_entrance} portal)")


def build_full_geometry(room_sequence: RoomSequence, map_size: int = 1000) -> RoomSequenceFullGeometry:
    """Convert RoomSequence name list to full geometry with portals and connections"""
    import sys
    current_module = sys.modules[__name__]

    room_templates = []
    connections = []

    # Build room templates
    for i, room_name in enumerate(room_sequence.rooms):
        room_class_name = room_classes[room_name]
        room_class = getattr(current_module, room_class_name)
        room_instance = room_class(i, map_size)
        portal_ids = ROOM_PORTAL_MAP[room_name]
        template = room_to_template(room_instance, room_name, portal_ids, map_size)
        room_templates.append(template)

    # Build connections between consecutive rooms
    # Track which portal was used to enter each room
    entry_portals = [None] * len(room_sequence.rooms)  # entry_portals[i] = portal used to enter room i

    for i in range(len(room_sequence.rooms) - 1):
        from_template = room_sequence.rooms[i]
        to_template = room_sequence.rooms[i + 1]
        from_entry = entry_portals[i]  # How we entered room i

        from_portal, to_portal = infer_connection_direction(from_template, to_template, from_entry)

        # Record that room i+1 will be entered through to_portal
        entry_portals[i + 1] = to_portal

        connection = RoomConnection(
            from_room=i,
            from_portal=from_portal,
            to_room=i + 1,
            to_portal=to_portal
        )
        connections.append(connection)

    # Handle branch paths
    if room_sequence.branch_paths:
        for branch in room_sequence.branch_paths:
            fork_room_idx = branch.fork_main_room_index
            fork_portal = branch.fork_portal

            # Fork rooms are now T-junctions which already have the fork portal
            # Only add portal if it's missing (for backwards compatibility)
            if fork_portal not in room_templates[fork_room_idx].portals:
                add_portal_to_template(room_templates[fork_room_idx], fork_portal, map_size)

            # Pre-compute entry directions for all branch rooms (needed to resolve dead_end)
            opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
            first_branch_entry = opposite[fork_portal]
            branch_entry_portals = [first_branch_entry]

            # Resolve dead_end placeholders and compute entry directions
            resolved_branch_rooms = []
            for j, branch_room_name in enumerate(branch.branch_rooms):
                if branch_room_name == "dead_end":
                    # Resolve to correct dead_end variant based on entry direction
                    entry_dir = branch_entry_portals[j]
                    branch_room_name = f"dead_end_{entry_dir}"

                resolved_branch_rooms.append(branch_room_name)

                # Compute exit direction for next room's entry
                if j < len(branch.branch_rooms) - 1:
                    next_room = branch.branch_rooms[j + 1]
                    if next_room == "dead_end":
                        # Will resolve later, just compute exit from current room
                        room_portals = ROOM_PORTAL_MAP.get(branch_room_name, [])
                        entry_dir = branch_entry_portals[j]
                        if entry_dir in room_portals and len(room_portals) == 2:
                            exit_dir = room_portals[1] if room_portals[0] == entry_dir else room_portals[0]
                        else:
                            exit_dir = room_portals[-1] if room_portals else None
                        branch_entry_portals.append(opposite.get(exit_dir))
                    else:
                        _, to_portal = infer_connection_direction(branch_room_name, next_room, branch_entry_portals[j])
                        branch_entry_portals.append(to_portal)

            # Build room templates for resolved branch rooms
            branch_start_idx = len(room_templates)
            for j, branch_room_name in enumerate(resolved_branch_rooms):
                room_class_name = room_classes[branch_room_name]
                room_class = getattr(current_module, room_class_name)
                room_instance = room_class(branch_start_idx + j, map_size)
                portal_ids = ROOM_PORTAL_MAP[branch_room_name]
                template = room_to_template(room_instance, branch_room_name, portal_ids, map_size)
                room_templates.append(template)

            # Create connection from fork room to first branch room
            connections.append(RoomConnection(
                from_room=fork_room_idx,
                from_portal=fork_portal,
                to_room=branch_start_idx,
                to_portal=first_branch_entry
            ))

            # Create connections between branch rooms
            for j in range(len(resolved_branch_rooms) - 1):
                from_template = resolved_branch_rooms[j]
                to_template = resolved_branch_rooms[j + 1]
                from_entry = branch_entry_portals[j]

                from_portal_dir, to_portal_dir = infer_connection_direction(from_template, to_template, from_entry)

                connections.append(RoomConnection(
                    from_room=branch_start_idx + j,
                    from_portal=from_portal_dir,
                    to_room=branch_start_idx + j + 1,
                    to_portal=to_portal_dir
                ))

            # Handle rejoin if applicable
            if branch.rejoin_main_room_index is not None and branch.rejoin_portal is not None:
                rejoin_room_idx = branch.rejoin_main_room_index
                rejoin_portal = branch.rejoin_portal

                # Add rejoin portal to the rejoin room
                add_portal_to_template(room_templates[rejoin_room_idx], rejoin_portal, map_size)

                # Create connection from last branch room to rejoin room
                last_branch_idx = branch_start_idx + len(resolved_branch_rooms) - 1

                # The exit direction is opposite of the rejoin_portal
                # (validated during branch generation)
                last_branch_exit = opposite[rejoin_portal]

                connections.append(RoomConnection(
                    from_room=last_branch_idx,
                    from_portal=last_branch_exit,
                    to_room=rejoin_room_idx,
                    to_portal=rejoin_portal
                ))

    return RoomSequenceFullGeometry(rooms=room_templates, connections=connections)
