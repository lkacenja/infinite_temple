import random

from infinite_temple.sprites.power_up import PowerUp


class PowerUpSpawner:
    """Manages powerup spawning based on room type."""

    def __init__(self, config):
        """
        Initialize powerup spawner.

        Args:
            config: GameConfig instance
        """
        self.config = config
        self.spawned_rooms = set()

    def spawn_for_room(self, room_id, room, entry_portal, powerup_sprites):
        """
        Spawn powerup for a room if conditions are met.

        Args:
            room_id: Current room ID (for tracking spawned rooms)
            room: RoomTemplate instance
            entry_portal: Portal ID player entered from (for corner calculation)
            powerup_sprites: Sprite group for powerups
        """
        if room_id in self.spawned_rooms:
            return

        self.spawned_rooms.add(room_id)

        # TESTING: Spawn all three powerups in start room
        if room.name == "start":
            map_size = self.config.display_width
            center = map_size // 2
            powerup_sprites.add(PowerUp(center - 50, center, PowerUp.HEALTH, room_id, self.config))
            powerup_sprites.add(PowerUp(center, center, PowerUp.SHIELD, room_id, self.config))
            powerup_sprites.add(PowerUp(center + 50, center, PowerUp.AMMO, room_id, self.config))
            return

        should_spawn = self._should_spawn(room.name)

        if not should_spawn:
            return

        power_type = self._choose_type()
        x, y = self._get_spawn_position(room.name, entry_portal)
        powerup = PowerUp(x, y, power_type, room_id, self.config)
        powerup_sprites.add(powerup)

    def _should_spawn(self, room_name):
        """
        Determine if powerup should spawn based on room type.

        Returns:
            bool: True if powerup should spawn
        """
        if "antechamber" in room_name:
            return random.random() < 0.5

        elif room_name.startswith("dead_end"):
            return random.random() < 0.75

        else:
            return random.random() < 0.05

    def _choose_type(self):
        """Randomly choose powerup type."""
        return random.choice([PowerUp.HEALTH, PowerUp.SHIELD, PowerUp.AMMO])

    def _get_spawn_position(self, room_name, entry_portal):
        """
        Calculate spawn position based on room type and entry portal.

        Args:
            room_name: Room template name
            entry_portal: Portal ID player entered from
        """
        map_size = self.config.display_width

        if "antechamber" in room_name:
            return self._get_antechamber_position(entry_portal, map_size)

        elif room_name.startswith("dead_end"):
            return self._get_dead_end_position(room_name, map_size)

        else:
            return (map_size // 2 + random.randint(-50, 50),
                    map_size // 2 + random.randint(-50, 50))

    def _get_antechamber_position(self, entry_portal, map_size):
        """Get position in far corner of antechamber from entry."""
        chamber_size = 700
        chamber_start = (map_size - chamber_size) // 2
        chamber_end = chamber_start + chamber_size
        margin = 80

        corners = {
            "top_left": (chamber_start + margin, chamber_start + margin),
            "top_right": (chamber_end - margin, chamber_start + margin),
            "bottom_left": (chamber_start + margin, chamber_end - margin),
            "bottom_right": (chamber_end - margin, chamber_end - margin),
        }

        if entry_portal == "west":
            far_corners = ["top_right", "bottom_right"]
        elif entry_portal == "east":
            far_corners = ["top_left", "bottom_left"]
        elif entry_portal == "north":
            far_corners = ["bottom_left", "bottom_right"]
        elif entry_portal == "south":
            far_corners = ["top_left", "top_right"]
        else:
            far_corners = list(corners.keys())

        chosen = random.choice(far_corners)
        return corners[chosen]

    def _get_dead_end_position(self, room_name, map_size):
        """Get position in corner of dead end chamber."""
        corridor_width = int(map_size * 0.2)
        corridor_start = (map_size - corridor_width) // 2
        corridor_end = corridor_start + corridor_width
        margin = 40

        if room_name == "dead_end_west":
            corners = [
                (margin, corridor_start + margin),
                (margin, corridor_end - margin),
            ]
        elif room_name == "dead_end_east":
            corners = [
                (map_size - margin, corridor_start + margin),
                (map_size - margin, corridor_end - margin),
            ]
        elif room_name == "dead_end_north":
            corners = [
                (corridor_start + margin, margin),
                (corridor_end - margin, margin),
            ]
        elif room_name == "dead_end_south":
            corners = [
                (corridor_start + margin, map_size - margin),
                (corridor_end - margin, map_size - margin),
            ]
        else:
            return (map_size // 2, map_size // 2)

        return random.choice(corners)
