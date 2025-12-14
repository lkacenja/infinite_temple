import sys
import time
import math
import json
import random
import os
import tempfile

import pygame
from pygame.locals import *
from tomita.legacy import pysynth_c as synthesizer

from infinite_temple.schema.room import HydratedRoomSequence
from generate_map import ask_for_map
from infinite_temple.schema import room as room_schema
from infinite_temple.schema.audio import AmbientMusic

white = (255, 255, 255)
red = (255, 0, 0)
black = (0, 0, 0)

display_width = 1000
display_height = 1000

player_size = 10
fd_fric = 0.75
bd_fric = 0.1
player_max_speed = 20
player_max_rtspd = 10
bullet_speed = 15

vec = pygame.math.Vector2

pygame.init()

surface = pygame.display.set_mode((display_width, display_height))

class Timer:
    def __init__(self, frequency: int, callback: callable):
        self.start = time.time()
        self.frequency = frequency
        self.callback = callback

    def tick(self):
        now = time.time()
        if now - self.start > self.frequency:
            self.callback()
            self.start = now


class Wall(pygame.sprite.Sprite):
    def __init__(self, segment: room_schema.Segment):
        pygame.sprite.Sprite.__init__(self)

        self.coord_1 = vec(segment.coord_1.x, segment.coord_1.y)
        self.coord_2 = vec(segment.coord_2.x, segment.coord_2.y)
        rads = math.atan2(self.coord_2.y - self.coord_1.y, self.coord_2.x - self.coord_1.x)
        self.angle = rads * (180 / math.pi)
        self.rect = surface.get_rect()

    def drawWall(self):
        pygame.draw.line(surface, white, self.coord_1, self.coord_2, 2)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.hspeed = 0
        self.vspeed = 0
        self.dir = 0
        self.rtspd = 0
        self.thrust = False
        self.braking = False
        self.rect = surface.get_rect()
        self.radius = player_size * 0.85
        self.exploded = False
        self.fragments = []
        self.max_health = 100
        self.current_health = self.max_health

    def blowUp(self):
        """Explode the ship into flying fragments"""
        self.exploded = True
        a = math.radians(self.dir)
        x = self.x
        y = self.y
        s = player_size

        # Define ship line segments as (x1, y1, x2, y2)
        segments = [
            # Left wing
            (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) + a),
             y - (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) + a),
             x + s * math.cos(a),
             y + s * math.sin(a)),

            # Right wing
            (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) - a),
             y + (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) - a),
             x + s * math.cos(a),
             y + s * math.sin(a)),

            # Back connector
            (x - (s * math.sqrt(2) / 2) * math.cos(a + math.pi / 4),
             y - (s * math.sqrt(2) / 2) * math.sin(a + math.pi / 4),
             x - (s * math.sqrt(2) / 2) * math.cos(-a + math.pi / 4),
             y + (s * math.sqrt(2) / 2) * math.sin(-a + math.pi / 4)),
        ]

        # Create fragments - each segment flies in a random direction
        for seg in segments:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4, 10)
            fragment = {
                'x1': seg[0], 'y1': seg[1],
                'x2': seg[2], 'y2': seg[3],
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'rotation': random.uniform(-0.15, 0.15)
            }
            self.fragments.append(fragment)

    def updatePlayer(self):
        if self.current_health <= 0:
            if not self.exploded:
                self.blowUp()
            # Update fragment positions - just move them in their direction
            for frag in self.fragments:
                # Move both endpoints
                frag['x1'] += frag['vx']
                frag['y1'] += frag['vy']
                frag['x2'] += frag['vx']
                frag['y2'] += frag['vy']

                # Optional: rotate the fragment as it flies
                cx = (frag['x1'] + frag['x2']) / 2
                cy = (frag['y1'] + frag['y2']) / 2
                dx1 = frag['x1'] - cx
                dy1 = frag['y1'] - cy
                dx2 = frag['x2'] - cx
                dy2 = frag['y2'] - cy

                cos_r = math.cos(frag['rotation'])
                sin_r = math.sin(frag['rotation'])

                frag['x1'] = cx + dx1 * cos_r - dy1 * sin_r
                frag['y1'] = cy + dx1 * sin_r + dy1 * cos_r
                frag['x2'] = cx + dx2 * cos_r - dy2 * sin_r
                frag['y2'] = cy + dx2 * sin_r + dy2 * cos_r

                # Apply friction
                frag['vx'] *= 0.98
                frag['vy'] *= 0.98
            return

        # Normal movement code
        speed = math.sqrt(self.hspeed ** 2 + self.vspeed ** 2)
        if self.thrust:
            if speed + fd_fric < player_max_speed:
                self.hspeed += fd_fric * math.cos(self.dir * math.pi / 180)
                self.vspeed += fd_fric * math.sin(self.dir * math.pi / 180)
            else:
                self.hspeed = player_max_speed * math.cos(self.dir * math.pi / 180)
                self.vspeed = player_max_speed * math.sin(self.dir * math.pi / 180)
        else:
            if speed - bd_fric > 0:
                change_in_hspeed = (bd_fric * math.cos(self.vspeed / self.hspeed))
                change_in_vspeed = (bd_fric * math.sin(self.vspeed / self.hspeed))
                if self.hspeed != 0:
                    if change_in_hspeed / abs(change_in_hspeed) == self.hspeed / abs(self.hspeed):
                        self.hspeed -= change_in_hspeed
                    else:
                        self.hspeed += change_in_hspeed
                if self.vspeed != 0:
                    if change_in_vspeed / abs(change_in_vspeed) == self.vspeed / abs(self.vspeed):
                        self.vspeed -= change_in_vspeed
                    else:
                        self.vspeed += change_in_vspeed
            else:
                self.hspeed = 0
                self.vspeed = 0
        self.x += self.hspeed
        self.y += self.vspeed

        brake_power = 0.85
        if self.braking and not self.thrust:
            self.hspeed *= brake_power
            self.vspeed *= brake_power

        # Rotate player
        self.dir += self.rtspd

    def drawPlayer(self):
        if self.current_health <= 0:
            # Draw fragments
            for frag in self.fragments:
                pygame.draw.line(surface, white,
                                 (frag['x1'], frag['y1']),
                                 (frag['x2'], frag['y2']))
            return

        # Normal drawing code
        a = math.radians(self.dir)
        x = self.x
        y = self.y
        s = player_size
        t = self.thrust

        pygame.draw.line(surface, white,
                         (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) + a),
                          y - (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) + a)),
                         (x + s * math.cos(a), y + s * math.sin(a)))

        pygame.draw.line(surface, white,
                         (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) - a),
                          y + (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) - a)),
                         (x + s * math.cos(a), y + s * math.sin(a)))

        pygame.draw.line(surface, white,
                         (x - (s * math.sqrt(2) / 2) * math.cos(a + math.pi / 4),
                          y - (s * math.sqrt(2) / 2) * math.sin(a + math.pi / 4)),
                         (x - (s * math.sqrt(2) / 2) * math.cos(-a + math.pi / 4),
                          y + (s * math.sqrt(2) / 2) * math.sin(-a + math.pi / 4)))
        if t:
            pygame.draw.line(surface, white,
                             (x - s * math.cos(a),
                              y - s * math.sin(a)),
                             (x - (s * math.sqrt(5) / 4) * math.cos(a + math.pi / 6),
                              y - (s * math.sqrt(5) / 4) * math.sin(a + math.pi / 6)))
            pygame.draw.line(surface, white,
                             (x - s * math.cos(-a),
                              y + s * math.sin(-a)),
                             (x - (s * math.sqrt(5) / 4) * math.cos(-a + math.pi / 6),
                              y + (s * math.sqrt(5) / 4) * math.sin(-a + math.pi / 6)))


class HealthBar:
    def __init__(self, x, y, width, height, border_width=3):
        """
        Create a health bar component.

        Args:
            x: X position of the health bar
            y: Y position of the health bar
            width: Width of the health bar
            height: Height of the health bar
            border_width: Thickness of the border lines
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.border_width = border_width
        self.health_percent = 100.0  # Current health percentage (0-100)

    def set_health(self, percent):
        """Set the health percentage (0-100)"""
        self.health_percent = max(0, min(100, percent))

    def draw(self, surface):
        """Draw the health bar on the given surface"""
        # Draw outer border (WHITE for visibility on black background)
        pygame.draw.rect(
            surface,
            (150, 150, 150),  # WHITE border
            (self.x, self.y, self.width, self.height),
            self.border_width
        )

        # Calculate inner fill area
        inner_x = self.x + self.border_width
        inner_y = self.y + self.border_width
        inner_width = self.width - (self.border_width * 2)
        inner_height = self.height - (self.border_width * 2)

        # Draw black background
        pygame.draw.rect(
            surface,
            (0, 0, 0),  # BLACK background
            (inner_x, inner_y, inner_width, inner_height)
        )

        # Calculate and draw white health fill
        fill_width = int(inner_width * (self.health_percent / 100))
        if fill_width > 0:
            pygame.draw.rect(
                surface,
                (150, 150, 150),  # WHITE fill
                (inner_x, inner_y, fill_width, inner_height)
            )

class Rubble(pygame.sprite.Sprite):
    def __init__(self, x, y, room_id):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.room_id = room_id

        # Random size between player_size and 5 * player_size
        self.size = random.uniform(player_size * 5, player_size * 10)
        self.radius = self.size * 0.5

        # Random drift direction and speed
        drift_angle = random.uniform(0, 360)
        drift_speed = random.uniform(1, 2)
        self.hspeed = drift_speed * math.cos(drift_angle * math.pi / 180)
        self.vspeed = drift_speed * math.sin(drift_angle * math.pi / 180)

        # Generate random squares with different sizes and rotations
        num_squares = random.randint(3, 6)
        self.squares = []
        for _ in range(num_squares):
            square_size = random.uniform(self.size * 0.3, self.size * 0.8)
            rotation = random.uniform(0, 360)
            offset_x = random.uniform(-self.size * 0.2, self.size * 0.2)
            offset_y = random.uniform(-self.size * 0.2, self.size * 0.2)
            self.squares.append({
                'size': square_size,
                'rotation': rotation,
                'offset_x': offset_x,
                'offset_y': offset_y
            })

        # Slow rotation speed for visual interest
        self.rotation_speed = random.uniform(-0.5, 0.5)

        self.rect = pygame.Rect(self.x - self.size, self.y - self.size,
                                self.size * 2, self.size * 2)

    def updateRubble(self):
        # Drift movement
        self.x += self.hspeed
        self.y += self.vspeed

        # Bounce off screen edges
        screen_width = surface.get_width()
        screen_height = surface.get_height()

        # Check horizontal boundaries
        if self.x - self.size < 0:
            self.x = self.size
            self.hspeed = -self.hspeed
        elif self.x + self.size > screen_width:
            self.x = screen_width - self.size
            self.hspeed = -self.hspeed

        # Check vertical boundaries
        if self.y - self.size < 0:
            self.y = self.size
            self.vspeed = -self.vspeed
        elif self.y + self.size > screen_height:
            self.y = screen_height - self.size
            self.vspeed = -self.vspeed

        # Update collision rect position
        self.rect.center = (self.x, self.y)

        # Slowly rotate each square
        for square in self.squares:
            square['rotation'] += self.rotation_speed

    def drawRubble(self):
        # Draw each square
        for square in self.squares:
            size = square['size']
            angle = math.radians(square['rotation'])
            cx = self.x + square['offset_x']
            cy = self.y + square['offset_y']

            # Calculate the four corners of the rotated square
            half_size = size / 2
            corners = []
            for i in range(4):
                corner_angle = angle + (i * math.pi / 2)
                corner_x = cx + half_size * math.sqrt(2) * math.cos(corner_angle + math.pi / 4)
                corner_y = cy + half_size * math.sqrt(2) * math.sin(corner_angle + math.pi / 4)
                corners.append((corner_x, corner_y))

            # Draw the square by connecting the corners
            for i in range(4):
                pygame.draw.line(surface, white, corners[i], corners[(i + 1) % 4])


def add_rubble(room_id, room_type):
    if room_type in ("AntechamberHorizontal", "AntechamberVertical"):
        for n in range(random.randrange(3, 5)):
            rubble = Rubble(500, 500, room_id)
            rubble_sprites.add(rubble)


P1 = Player(500, 500)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)

walls_sprites = pygame.sprite.Group()

rubble_sprites = pygame.sprite.Group()


# print("Generating room....")
# map = ask_for_map()
# print("Generation complete")

def load_map_file(file: str):
    with open(file, "r") as f:
        map_json = json.loads(f.read())
    return room_schema.RoomSequence.model_validate(map_json)



def render_room(room):
    #print(room_manager.current_room_id, " ", room.__class__.__name__)
    for segment in room.walls:
        walls_sprites.add(Wall(segment))
    # test = Wall(vec(100, 100), vec(200, 150))


FramePerSec = pygame.time.Clock()

pygame.display.set_caption("INFINITE TEMPLE")


def wall_collision_test(player, wall):
    """
    Check if a circle (player) intersects with a line segment (wall).
    Returns True if collision detected.
    """
    # Get wall endpoints
    x1, y1 = wall.coord_1.x, wall.coord_1.y
    x2, y2 = wall.coord_2.x, wall.coord_2.y

    # Get player position and radius
    cx, cy = player.x, player.y
    r = player.radius

    # Vector from start to end of wall
    dx = x2 - x1
    dy = y2 - y1

    # Vector from wall start to circle center
    fx = cx - x1
    fy = cy - y1

    # Project circle center onto wall line
    wall_length_sq = dx * dx + dy * dy

    if wall_length_sq == 0:
        # Wall has zero length
        dist_sq = fx * fx + fy * fy
        return dist_sq <= r * r

    # Parameter t tells us where on the line the closest point is
    # t=0 means at start, t=1 means at end
    t = (fx * dx + fy * dy) / wall_length_sq
    t = max(0, min(1, t))  # Clamp to line segment

    # Find closest point on line segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Check distance from circle center to closest point
    dist_x = cx - closest_x
    dist_y = cy - closest_y
    dist_sq = dist_x * dist_x + dist_y * dist_y

    return dist_sq <= r * r


def handle_wall_collision(player, wall):
    """
    Resolve collision between player and wall.
    Pushes player out and reflects velocity.
    """
    if isinstance(player, Player):
        top_speed = abs(max(player.vspeed, player.hspeed))
        damage = (top_speed / 20) * 50
        player.current_health -= damage

    # Get wall vector
    dx = wall.coord_2.x - wall.coord_1.x
    dy = wall.coord_2.y - wall.coord_1.y
    wall_length = math.sqrt(dx * dx + dy * dy)

    if wall_length == 0:
        return

    # Normalize wall vector
    wx = dx / wall_length
    wy = dy / wall_length

    # Wall normal (perpendicular)
    nx = -wy
    ny = wx

    # Find closest point on wall to player
    fx = player.x - wall.coord_1.x
    fy = player.y - wall.coord_1.y
    t = max(0, min(1, (fx * wx + fy * wy) / wall_length))

    closest_x = wall.coord_1.x + t * dx
    closest_y = wall.coord_1.y + t * dy

    # Vector from closest point to player
    to_player_x = player.x - closest_x
    to_player_y = player.y - closest_y
    dist = math.sqrt(to_player_x * to_player_x + to_player_y * to_player_y)

    if dist == 0:
        # Player is exactly on the wall, push along normal
        player.x = closest_x + nx * (player.radius + 2)
        player.y = closest_y + ny * (player.radius + 2)
    else:
        # Normalize direction to player
        to_player_x /= dist
        to_player_y /= dist

        # Push player out to be exactly radius + margin from wall
        player.x = closest_x + to_player_x * (player.radius + 2)
        player.y = closest_y + to_player_y * (player.radius + 2)

        # Make sure normal points toward player
        if (nx * to_player_x + ny * to_player_y) < 0:
            nx = -nx
            ny = -ny

    # Reflect velocity off wall
    # v_new = v - 2 * (v · n) * n
    dot = player.hspeed * nx + player.vspeed * ny
    player.hspeed -= 2 * dot * nx
    player.vspeed -= 2 * dot * ny

    # Apply damping to prevent infinite bouncing
    damping = 0.75
    player.hspeed *= damping
    player.vspeed *= damping



def rubble_collision_test(sprite1, sprite2):
    """
    Calculates distance between two sprites using their x/y attributes
    and checks if that distance is less than the sum of their radii.
    """
    # Calculate the difference in positions
    dx = sprite1.x - sprite2.x
    dy = sprite1.y - sprite2.y

    # Calculate the distance squared (optimization to avoid expensive sqrt)
    dist_sq = dx ** 2 + dy ** 2

    # Calculate the sum of radii squared
    radii_sum = sprite1.radius + sprite2.radius
    radii_sq = radii_sum ** 2

    # Check collision
    return dist_sq < radii_sq


def handle_rubble_collision(player, rubble):
    """
    Resolve collision between player and circular rubble.
    Pushes player out and reflects velocity relative to the rubble's movement.
    """
    # 1. Calculate vector between centers (Rubble -> Player)
    dx = player.x - rubble.x
    dy = player.y - rubble.y
    dist = math.sqrt(dx * dx + dy * dy)

    if dist == 0:
        return  # Prevent division by zero if they spawn on exact same pixel

    # Normalize the normal vector (points A->B)
    nx = dx / dist
    ny = dy / dist

    # 2. Calculate Relative Velocity
    # This is crucial because the rubble is also moving.
    # We want the bounce to act as if the rubble were stationary and the player hit it harder/softer.
    rel_vx = player.hspeed - rubble.hspeed
    rel_vy = player.vspeed - rubble.vspeed

    # Calculate impact speed for damage
    impact_speed = math.sqrt(rel_vx ** 2 + rel_vy ** 2)

    # 3. Apply Damage
    if isinstance(player, Player):
        # Using similar scaling to your wall logic
        damage = (impact_speed / 20) * 50
        player.current_health -= damage

    # 4. Positional Correction (Push player out)
    # We want them to be touching, not overlapping
    min_dist = player.radius + rubble.radius + 2  # +2 margin for safety
    overlap = min_dist - dist

    if overlap > 0:
        player.x += nx * overlap
        player.y += ny * overlap
        # Update rect immediately so drawing is smooth
        player.rect.centerx = int(player.x)
        player.rect.centery = int(player.y)

    # 5. Reflect Velocity (Bounce)
    # v_new = v - 2 * (v · n) * n
    # We calculate the dot product of the RELATIVE velocity and the normal
    dot = rel_vx * nx + rel_vy * ny

    # Only bounce if they are moving towards each other (dot < 0)
    if dot < 0:
        # Reflect the relative velocity
        rel_vx -= 2 * dot * nx
        rel_vy -= 2 * dot * ny

        # Apply damping (loss of energy)
        damping = 0.75
        rel_vx *= damping
        rel_vy *= damping

        # Apply the new relative velocity back to the player
        # Player V = Rubble V + New Relative V
        player.hspeed = rubble.hspeed + rel_vx
        player.vspeed = rubble.vspeed + rel_vy


def build_room_sequence(room_file: str):
    active_map = load_map_file(room_file)
    #room_classes
    #getattr(module, member_name)
    hydrated_rooms = []
    for i, room_name in enumerate(active_map.rooms):
        room_class = getattr(room_schema, room_schema.room_classes[room_name])
        hydrated_rooms.append(room_class(i, 1000))
    return HydratedRoomSequence(rooms=hydrated_rooms)


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


class RoomProgressDisplay:
    """
    Displays the highest room ID achieved with celebratory animation every 5 rooms.
    """

    def __init__(self, x, y, font_size=36):
        """
        Initialize the room progress display.

        Args:
            x: X position for the display
            y: Y position for the display
            font_size: Base font size for the text
        """
        self.x = x
        self.y = y
        self.font_size = font_size
        self.font = pygame.font.Font(None, font_size)
        self.large_font = pygame.font.Font(None, int(font_size * 1.5))

        self.highest_room_id = 0
        self.last_milestone = 0  # Track last milestone for animation

        # Animation state
        self.animating = False
        self.animation_time = 0
        self.animation_duration = 1.0

        # Colors
        self.normal_color = (150, 150, 150)
        self.milestone_color = (255, 225, 225)

    def update(self, current_room_id, dt):
        """
        Update the display with the current room ID.

        Args:
            current_room_id: The current room ID
            dt: Delta time in seconds
        """
        # Update highest room ID
        if current_room_id > self.highest_room_id:
            self.highest_room_id = current_room_id

            # Check if we hit a milestone (every 5 rooms)
            current_milestone = (self.highest_room_id // 5) * 5
            if current_milestone > self.last_milestone and current_milestone > 0:
                self.last_milestone = current_milestone
                self.animating = True
                self.animation_time = 0

        # Update animation
        if self.animating:
            self.animation_time += dt
            if self.animation_time >= self.animation_duration:
                self.animating = False
                self.animation_time = 0

    def draw(self, surface):
        """
        Draw the room progress display.

        Args:
            surface: Pygame surface to draw on
        """
        if self.animating:
            self._draw_animated(surface)
        else:
            self._draw_normal(surface)

    def _draw_normal(self, surface):
        """Draw the normal (non-animated) display."""
        text = f"{self.highest_room_id}"
        text_surface = self.font.render(text, True, self.normal_color)
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        surface.blit(text_surface, text_rect)

    def _draw_animated(self, surface):
        """Draw the animated milestone celebration with pure white text growing and shrinking."""
        progress = self.animation_time / self.animation_duration
        if progress < 0.5:
            scale = 1.0 + (progress * 2) * 0.5  # Grow to 1.5x
        else:
            scale = 1.5 - ((progress - 0.5) * 2) * 0.5  # Shrink back to 1.0x

        text_color = (255, 255, 255)
        scaled_font_size = int(self.font_size * scale)
        scaled_font = pygame.font.Font(None, scaled_font_size)
        text = f"{self.last_milestone}"
        text_surface = scaled_font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        surface.blit(text_surface, text_rect)


def play_music_file(file: str):
    with open(file, "r") as f:
        audio_json = json.loads(f.read())
    audio_model = AmbientMusic.model_validate(audio_json)
    play_music_from_dict(audio_model.model_dump())


class MusicPlayer:
    """Non-blocking music player that can be stopped and managed."""

    def __init__(self):
        self.temp_dir = None
        self.wav_files = []
        self.sounds = []
        self.channels = []
        self.is_playing = False

    def stop(self):
        """Stop all playing music and clean up resources."""
        if self.is_playing:
            pygame.mixer.stop()
            self.is_playing = False

        # Clean up temporary files
        for wav_file in self.wav_files:
            try:
                os.remove(wav_file)
            except:
                pass

        if self.temp_dir:
            try:
                os.rmdir(self.temp_dir)
            except:
                pass

        self.wav_files = []
        self.sounds = []
        self.channels = []
        self.temp_dir = None

    def play(self, music_dict, loop=True):
        """
        Start playing music without blocking.

        Args:
            music_dict: Dictionary with music data or JSON string
            loop: Whether to loop the music indefinitely (default: True)
        """
        # Stop any currently playing music
        self.stop()

        # Handle both dict and JSON string
        if isinstance(music_dict, str):
            music_dict = json.loads(music_dict)

        print(f"Playing: {music_dict['title']}")
        print(f"Key: {music_dict['key']} | Tempo: {music_dict['tempo_bpm']} BPM")
        print(f"Mood: {music_dict['mood']}")
        print(f"Voices: {len(music_dict['voices'])}")

        # Create temporary directory for WAV files
        self.temp_dir = tempfile.mkdtemp()

        # Generate WAV file for each voice using Tomita
        for i, voice in enumerate(music_dict['voices']):
            # Convert to Tomita/PySynth format: list of tuples
            notes = [(note['pitch'], note['duration']) for note in voice['notes']]

            temp_wav = os.path.join(self.temp_dir, f"voice_{i}_{voice['name']}.wav")

            # Generate WAV using Tomita's synthesizer
            synthesizer.make_wav(notes, fn=temp_wav, bpm=music_dict['tempo_bpm'])
            self.wav_files.append(temp_wav)

        # Initialize pygame mixer for playback (if not already initialized)
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        pygame.mixer.set_num_channels(len(self.wav_files))

        # Load and play all voices simultaneously
        for i, wav_file in enumerate(self.wav_files):
            sound = pygame.mixer.Sound(wav_file)
            self.sounds.append(sound)

            channel = pygame.mixer.Channel(i)
            channel.play(sound, loops=-1 if loop else 0)
            self.channels.append(channel)

        self.is_playing = True
        print(f"Music playing in background...")


# Global music player instance
_music_player = MusicPlayer()

def play_music_from_dict(music_dict, loop=True):
    """
    Play ambient music directly from a dictionary (no file needed).
    Non-blocking - returns immediately while music plays in background.

    Args:
        music_dict: Dictionary with music data (from LLM JSON response) or JSON string
        loop: Whether to loop the music indefinitely (default: True)
    """
    _music_player.play(music_dict, loop=loop)


room_sequence = build_room_sequence("maps/map-1765062702.200778.json")
play_music_file("maps/audio-1765141789.983802.json")

room_manager = RoomManager(room_sequence)

room = room_manager.get_current_room()
render_room(room)

progress_display = RoomProgressDisplay(x=display_width - 30, y=19, font_size=19)


for n, room in enumerate(room_sequence.rooms):
    add_rubble(n, room.__class__.__name__)


health_bar = HealthBar(10, 10, 300, 8)
current_health = 100.0

clock = pygame.time.Clock()

while True:
    dt = clock.tick(60) / 1000.0

    surface.fill((0, 0, 0))
    P1.updatePlayer()
    P1.drawPlayer()


    transition =  room_manager.check_transition(P1, 1000)
    if transition:
        walls_sprites.empty()
        room = room_manager.get_current_room()
        render_room(room)
    for rubble in rubble_sprites:
        if rubble.room_id == room_manager.current_room_id:
            rubble.updateRubble()
            rubble.drawRubble()
            colliding = pygame.sprite.spritecollide(rubble, walls_sprites, False, wall_collision_test)
            if len(colliding) > 0:
                rubble.dir = colliding[0].angle + 90
                rubble.hspeed *= -1
                rubble.vspeed *= -1
            colliding = pygame.sprite.spritecollide(P1, [rubble], False, rubble_collision_test)
            if len(colliding) > 0:
                handle_rubble_collision(P1, colliding[0])
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                P1.thrust = True
            if event.key == pygame.K_LEFT:
                P1.rtspd = -player_max_rtspd
            if event.key == pygame.K_RIGHT:
                P1.rtspd = player_max_rtspd
            if event.key == pygame.K_SPACE:
               P1.braking = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                P1.thrust = False
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                P1.rtspd = 0
            if event.key == pygame.K_SPACE:
                P1.braking = False
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    for wall in walls_sprites:
        wall.drawWall()

    colliding = pygame.sprite.spritecollide(P1, walls_sprites, False, wall_collision_test)
    if len(colliding) > 0:
        handle_wall_collision(P1, colliding[0])

    percent_health = (P1.current_health / P1.max_health if P1.current_health > 0 else 0) * 100
    health_bar.set_health(percent_health)
    health_bar.draw(surface)

    progress_display.update(room_manager.current_room_id, dt)
    progress_display.draw(surface)

        #colliding[0]
    # for entity in all_sprites:
    #     if hasattr(entity, 'move'):
    #         entity.move()
    #     if hasattr(entity, 'update'):
    #         entity.update()
    #     surface.blit(entity.surf, entity.rect)
    pygame.display.update()
    FramePerSec.tick(30)