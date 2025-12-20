import json

from infinite_temple.schema import room as room_schema
from infinite_temple.schema.room import HydratedRoomSequence
from infinite_temple.sprites.wall import Wall

class RoomManager:
    """
    Manages room transitions by tracking which edge the player entered from.
    """

    def __init__(self, room_sequence):
        """
        Initialize the room manager.

        Args:
            room_sequence: HydratedRoomSequence with all rooms
        """
        self.room_sequence = room_sequence
        self.current_room_id = 0
        self.entry_edge = None  # Track which edge player entered current room from
        self.direction = 1  # 1 for forward, -1 for backward

    def get_current_room(self):
        """Get the current room object."""
        return self.room_sequence.rooms[self.current_room_id]

    def start_room(self, entry_edge="CENTER"):
        """
        Set the initial room and entry edge.

        Args:
            entry_edge: "LEFT", "RIGHT", "TOP", "BOTTOM", or "CENTER" for starting room
        """
        self.current_room_id = 0
        self.entry_edge = entry_edge
        self.direction = 1  # Start moving forward

    def check_transition(self, player, map_size=1000):
        """
        Check if player has crossed a room boundary and handle transition.

        Args:
            player: Player instance with x, y coordinates
            map_size: Size of the map (default 1000)

        Returns:
            True if a transition occurred, False otherwise
        """
        corridor_width = int(map_size * 0.2)
        center = map_size // 2
        corridor_start = center - corridor_width // 2
        corridor_end = center + corridor_width // 2

        exit_edge = None

        # Determine which edge (if any) the player has crossed
        if player.x > map_size and corridor_start <= player.y <= corridor_end:
            exit_edge = "RIGHT"
        elif player.x < 0 and corridor_start <= player.y <= corridor_end:
            exit_edge = "LEFT"
        elif player.y > map_size and corridor_start <= player.x <= corridor_end:
            exit_edge = "BOTTOM"
        elif player.y < 0 and corridor_start <= player.x <= corridor_end:
            exit_edge = "TOP"

        # No edge crossed, still in room
        if exit_edge is None:
            return False

        # Check if direction changed: exiting through entry edge means reversing direction
        if exit_edge == self.entry_edge:
            # Direction change detected - flip the direction flag
            self.direction *= -1

        # Use the current direction for room transition
        new_room_id = self.current_room_id + self.direction

        # The new entry edge is the opposite of the exit edge
        new_entry_edge = self._get_opposite_edge(exit_edge)

        # Perform transition
        self.current_room_id = new_room_id
        self.entry_edge = new_entry_edge

        # Reposition player to opposite edge
        self._reposition_player(player, new_entry_edge, map_size)
        return True

    def _get_opposite_edge(self, edge):
        """Get the opposite edge."""
        opposites = {
            "LEFT": "RIGHT",
            "RIGHT": "LEFT",
            "TOP": "BOTTOM",
            "BOTTOM": "TOP"
        }
        return opposites.get(edge)

    def _reposition_player(self, player, entry_edge, map_size):
        """
        Reposition player to the entry edge of the new room.

        Args:
            player: Player instance
            entry_edge: Which edge the player is entering from
            map_size: Size of the map
        """
        if entry_edge == "LEFT":
            player.x = 0
        elif entry_edge == "RIGHT":
            player.x = map_size
        elif entry_edge == "TOP":
            player.y = 0
        elif entry_edge == "BOTTOM":
            player.y = map_size


def load_map_file(file: str):
    with open(file, "r") as f:
        map_json = json.loads(f.read())
    return room_schema.RoomSequence.model_validate(map_json)


def build_room_sequence(room_file: str):
    active_map = load_map_file(room_file)
    hydrated_rooms = []
    for i, room_name in enumerate(active_map.rooms):
        room_class = getattr(room_schema, room_schema.room_classes[room_name])
        hydrated_rooms.append(room_class(i, 1000))
    return HydratedRoomSequence(rooms=hydrated_rooms)

def render_room(room, sprite_group, config, debug: bool = False):
    if debug:
        print(room_manager.current_room_id, " ", room.__class__.__name__)
    for segment in room.walls:
        sprite_group.add(Wall(segment, config))