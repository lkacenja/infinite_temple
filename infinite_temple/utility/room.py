import json

from infinite_temple.schema import room as room_schema
from infinite_temple.schema.room import RoomSequenceFullGeometry, RoomConnection
from infinite_temple.schema.config import GameConfig
from infinite_temple.sprites.wall import Wall

class RoomManager:
    """
    Manages room transitions using portal-based connections.
    """

    def __init__(self, room_sequence: RoomSequenceFullGeometry):
        """
        Initialize the room manager.

        Args:
            room_sequence: RoomSequenceFullGeometry with rooms and portal connections
        """
        self.room_sequence = room_sequence
        self.current_room_id = 0

        # Build connection lookup: (room_id, portal_id) -> RoomConnection
        self.connection_map = {}
        for conn in room_sequence.connections:
            key = (conn.from_room, conn.from_portal)
            self.connection_map[key] = conn

            # Add bidirectional connection for backward navigation
            reverse_key = (conn.to_room, conn.to_portal)
            reverse_conn = RoomConnection(
                from_room=conn.to_room,
                from_portal=conn.to_portal,
                to_room=conn.from_room,
                to_portal=conn.from_portal
            )
            self.connection_map[reverse_key] = reverse_conn


    def get_current_room(self):
        """Get the current room object."""
        return self.room_sequence.rooms[self.current_room_id]

    def check_transition(self, player, debug=False):
        """
        Check if player has triggered a portal and handle transition.

        Args:
            player: Player instance with x, y coordinates
            debug: Print debug information

        Returns:
            True if a transition occurred, False otherwise
        """
        current_room = self.get_current_room()

        # Debug: check if player is outside room bounds
        if debug and (player.x < -100 or player.x > 1100 or player.y < -100 or player.y > 1100):
            print(f"Player position: ({player.x:.1f}, {player.y:.1f})")
            print(f"Current room: {current_room.name} (id={self.current_room_id})")
            print(f"Available portals: {list(current_room.portals.keys())}")

        # Check each portal in the current room
        for portal_id, portal in current_room.portals.items():
            if debug and (player.x < -100 or player.x > 1100 or player.y < -100 or player.y > 1100):
                rect = portal.trigger_rect
                print(f"  Portal '{portal_id}': trigger_rect=({rect.x}, {rect.y}, {rect.width}, {rect.height})")
                print(f"    Would contain player? {rect.contains(player.x, player.y)}")

            if portal.trigger_rect.contains(player.x, player.y):
                # Find the connection for this portal
                connection_key = (self.current_room_id, portal_id)
                connection = self.connection_map.get(connection_key)

                if debug:
                    print(f"  Portal '{portal_id}' triggered! Connection: {connection}")

                if connection:
                    # Get the destination room and portal
                    dest_room = self.room_sequence.rooms[connection.to_room]
                    dest_portal = dest_room.portals[connection.to_portal]

                    if debug:
                        print(f"  Transitioning to room {connection.to_room} ({dest_room.name}) via portal '{connection.to_portal}'")

                    # Transition to new room
                    self.current_room_id = connection.to_room

                    # Spawn player at destination portal
                    player.x = dest_portal.spawn_point.x
                    player.y = dest_portal.spawn_point.y

                    return True

        return False


def load_map_file(file: str):
    with open(file, "r") as f:
        map_json = json.loads(f.read())
    return room_schema.RoomSequence.model_validate(map_json)


def build_room_sequence(room_file: str, config: GameConfig) -> RoomSequenceFullGeometry:
    """Load map file and build full room geometry with portals and connections"""
    room_sequence = load_map_file(room_file)
    map_size = config.display_width
    return room_schema.build_full_geometry(room_sequence, map_size=map_size)


def render_room(room, sprite_group, config, debug: bool = False):
    """Render a RoomTemplate by creating wall sprites"""
    if debug:
        print(f"Room: {room.name}")
    for segment in room.walls:
        sprite_group.add(Wall(segment, config))