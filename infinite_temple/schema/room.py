from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Point(BaseModel):
    x: int = Field(..., ge=0, le=1000)
    y: int = Field(..., ge=0, le=1000)


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


class RoomSequenceV2(BaseModel):
    """Portal-based room sequence with explicit connections"""
    rooms: List[RoomTemplate] = Field(min_length=1, description="List of room templates")
    connections: List[RoomConnection] = Field(min_length=0, description="Explicit portal connections between rooms")


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
    "antechamber_horizontal": ["west", "east"]  # Enters west, exits east
}


def infer_connection_direction(from_template: str, to_template: str) -> tuple[str, str]:
    """Infer which portals connect based on room template names

    Returns: (from_portal_id, to_portal_id)

    Logic: For consecutive rooms, the "exit" portal of the first room connects
    to the "entrance" portal of the second room. For most rooms, the exit portal
    is the one that wasn't used as the entrance (the "second" portal in the list).
    """
    from_portals = ROOM_PORTAL_MAP.get(from_template, [])
    to_portals = ROOM_PORTAL_MAP.get(to_template, [])

    # For rooms with 2 portals, the exit is typically the second portal
    # (the first portal is usually the entrance from the previous room)
    # For start room with 1 portal, use that portal
    from_exit = from_portals[-1] if from_portals else None
    to_entrance = to_portals[0] if to_portals else None

    if from_exit and to_entrance:
        # Verify these portals can geometrically connect
        # Opposite directions should connect: east↔west, north↔south
        opposite_pairs = {
            ("east", "west"), ("west", "east"),
            ("north", "south"), ("south", "north")
        }

        if (from_exit, to_entrance) in opposite_pairs:
            return (from_exit, to_entrance)

    # Fallback: try priority-based matching
    priority = [
        ("east", "west"),
        ("south", "north"),
        ("west", "east"),
        ("north", "south")
    ]

    for from_p, to_p in priority:
        if from_p in from_portals and to_p in to_portals:
            return (from_p, to_p)

    # Last resort: connect any available portals
    if from_portals and to_portals:
        return (from_portals[-1], to_portals[0])

    raise ValueError(f"Cannot infer connection between {from_template} and {to_template}")


def convert_legacy_map(legacy_sequence: RoomSequence, map_size: int = 1000) -> RoomSequenceV2:
    """Convert old RoomSequence format to new portal-based RoomSequenceV2"""
    import sys
    current_module = sys.modules[__name__]

    room_templates = []
    connections = []

    # Build room templates
    for i, room_name in enumerate(legacy_sequence.rooms):
        room_class_name = room_classes[room_name]
        room_class = getattr(current_module, room_class_name)
        room_instance = room_class(i, map_size)
        portal_ids = ROOM_PORTAL_MAP[room_name]
        template = room_to_template(room_instance, room_name, portal_ids, map_size)
        room_templates.append(template)

    # Build connections between consecutive rooms
    for i in range(len(legacy_sequence.rooms) - 1):
        from_template = legacy_sequence.rooms[i]
        to_template = legacy_sequence.rooms[i + 1]

        from_portal, to_portal = infer_connection_direction(from_template, to_template)

        connection = RoomConnection(
            from_room=i,
            from_portal=from_portal,
            to_room=i + 1,
            to_portal=to_portal
        )
        connections.append(connection)

    return RoomSequenceV2(rooms=room_templates, connections=connections)
