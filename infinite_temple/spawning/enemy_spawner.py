import random

from infinite_temple.utility.difficulty import calculate_difficulty
from infinite_temple.sprites.priest import Priest
from infinite_temple.sprites.vision import Vision
from infinite_temple.sprites.rubble import Rubble


class EnemySpawner:
    """Manages enemy spawning based on room and difficulty."""

    def __init__(self, config):
        """
        Initialize enemy spawner.

        Args:
            config: GameConfig instance
        """
        self.config = config
        self.spawned_rooms = set()

    def spawn_for_room(self, room_id, room, priest_sprites, vision_sprites, rubble_sprites):
        """
        Spawn enemies for a room if it hasn't spawned yet.

        Args:
            room_id: Current room ID
            room: RoomTemplate instance
            priest_sprites: Sprite group for priests
            vision_sprites: Sprite group for visions
            rubble_sprites: Sprite group for rubble
        """
        # Check if already spawned
        if room_id in self.spawned_rooms:
            return

        self.spawned_rooms.add(room_id)

        difficulty = calculate_difficulty(room_id)

        # Determine if this room should spawn
        should_spawn, count_range = self._should_spawn_enemies(room_id, room.name, difficulty)

        if not should_spawn:
            return

        # Determine how many enemies to spawn
        enemy_count = random.randint(*count_range)

        # Get safe spawn area
        spawn_area = self._get_safe_spawn_area(room.name, self.config.display_width)

        # Track rubble spawned in non-antechamber rooms (max 1)
        is_antechamber = "antechamber" in room.name
        rubble_spawned = 0

        # Spawn enemies
        for _ in range(enemy_count):
            enemy_type = self._choose_enemy_type(difficulty)

            # Skip rubble if we've already spawned 1 in a non-antechamber room
            if enemy_type == "rubble" and not is_antechamber and rubble_spawned >= 1:
                continue

            # Create entity first to know its size (rubble and vision have random sizes)
            if enemy_type == "rubble":
                entity = Rubble(0, 0, room_id, self.config)
                if not is_antechamber:
                    rubble_spawned += 1
            elif enemy_type == "priest":
                entity = Priest(0, 0, room_id, self.config)
            elif enemy_type == "vision":
                entity = Vision(0, 0, room_id, self.config)
            else:
                continue

            # Get safe position accounting for entity radius
            x, y = self._random_position(spawn_area, entity.radius)
            entity.x = x
            entity.y = y

            # Add to appropriate sprite group
            if enemy_type == "rubble":
                rubble_sprites.add(entity)
            elif enemy_type == "priest":
                priest_sprites.add(entity)
            elif enemy_type == "vision":
                vision_sprites.add(entity)

    def _should_spawn_enemies(self, room_id, room_name, difficulty):
        """
        Determine if enemies should spawn and how many.

        Args:
            room_id: Current room ID
            room_name: Room template name
            difficulty: Calculated difficulty level

        Returns:
            Tuple of (should_spawn: bool, count_range: tuple)
        """
        is_antechamber = "antechamber" in room_name

        if difficulty < 3:
            # Early game: only antechambers
            if is_antechamber:
                return (True, (2, 4))
            return (False, (0, 0))

        elif difficulty < 5:
            # Difficulty 3-4: Antechambers common, other rooms rare
            if is_antechamber:
                spawn_chance = 0.8
                count_range = (2, 4)
            else:
                spawn_chance = 0.2 + (difficulty - 3) * 0.1  # 20% at diff 3, 30% at diff 4
                count_range = (1, 3)

            if random.random() < spawn_chance:
                return (True, count_range)
            return (False, (0, 0))

        elif difficulty < 8:
            # Mid game: probabilistic spawning
            spawn_chance = 0.5 + (difficulty - 5) * 0.1
            if random.random() < spawn_chance:
                return (True, (3, 6))
            return (False, (0, 0))

        else:
            # Late game: frequent spawning
            spawn_chance = 0.8 + (difficulty - 8) * 0.1
            if random.random() < spawn_chance:
                return (True, (5, 8))
            return (False, (0, 0))

    def _choose_enemy_type(self, difficulty):
        """
        Choose which enemy type to spawn based on difficulty.

        Args:
            difficulty: Calculated difficulty level

        Returns:
            String: "rubble", "priest", or "vision"
        """
        if difficulty < 3:
            return "rubble"

        elif difficulty < 6:
            # 70% rubble, 30% priest
            return random.choices(
                ["rubble", "priest"],
                weights=[70, 30]
            )[0]

        elif difficulty < 9:
            # 40% rubble, 40% priest, 20% vision
            return random.choices(
                ["rubble", "priest", "vision"],
                weights=[40, 40, 20]
            )[0]

        else:
            # 30% rubble, 40% priest, 30% vision
            return random.choices(
                ["rubble", "priest", "vision"],
                weights=[30, 40, 30]
            )[0]

    def _get_safe_spawn_area(self, room_name, map_size):
        """
        Get safe spawning area for room type.

        Args:
            room_name: Room template name
            map_size: Map size (display width)

        Returns:
            Dict with keys: x_min, x_max, y_min, y_max
        """
        corridor_width = int(map_size * 0.2)
        corridor_start = (map_size - corridor_width) // 2
        corridor_end = corridor_start + corridor_width

        if room_name == "start":
            # Start room: 400x400 square in center
            square_size = 400
            square_start = (map_size - square_size) // 2
            square_end = square_start + square_size
            return {
                'x_min': square_start + 50,
                'x_max': square_end - 50,
                'y_min': square_start + 50,
                'y_max': square_end - 50
            }

        elif room_name == "horizontal":
            # Horizontal corridor: use middle 60% horizontally
            margin = map_size * 0.2
            return {
                'x_min': margin,
                'x_max': map_size - margin,
                'y_min': corridor_start + 20,
                'y_max': corridor_end - 20
            }

        elif room_name == "vertical":
            # Vertical corridor: use middle 60% vertically
            margin = map_size * 0.2
            return {
                'x_min': corridor_start + 20,
                'x_max': corridor_end - 20,
                'y_min': margin,
                'y_max': map_size - margin
            }

        elif room_name.startswith("elbow"):
            # Elbow rooms: use corridor area with margins
            return {
                'x_min': corridor_start + 20,
                'x_max': corridor_end - 20,
                'y_min': corridor_start + 20,
                'y_max': corridor_end - 20
            }

        elif "antechamber" in room_name:
            # Large chamber (700x700)
            chamber_size = 700
            chamber_start = (map_size - chamber_size) // 2
            chamber_end = chamber_start + chamber_size
            return {
                'x_min': chamber_start + 50,
                'x_max': chamber_end - 50,
                'y_min': chamber_start + 50,
                'y_max': chamber_end - 50
            }

        else:
            # Default: center area
            return {
                'x_min': map_size * 0.3,
                'x_max': map_size * 0.7,
                'y_min': map_size * 0.3,
                'y_max': map_size * 0.7
            }

    def _random_position(self, spawn_area, entity_radius=0):
        """
        Get random position within spawn area, accounting for entity radius.

        Args:
            spawn_area: Dict with x_min, x_max, y_min, y_max
            entity_radius: Radius of the entity to spawn (to avoid wall overlap)

        Returns:
            Tuple of (x, y) coordinates
        """
        # Add margin based on entity radius to prevent spawning in walls
        margin = entity_radius + 5  # Extra 5 pixel safety margin

        x_min = spawn_area['x_min'] + margin
        x_max = spawn_area['x_max'] - margin
        y_min = spawn_area['y_min'] + margin
        y_max = spawn_area['y_max'] - margin

        # Ensure valid range
        if x_min >= x_max:
            x = (spawn_area['x_min'] + spawn_area['x_max']) / 2
        else:
            x = random.uniform(x_min, x_max)

        if y_min >= y_max:
            y = (spawn_area['y_min'] + spawn_area['y_max']) / 2
        else:
            y = random.uniform(y_min, y_max)

        return x, y
