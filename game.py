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
from pycollision import Collision

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

    def updatePlayer(self):
        # Move player
        speed = math.sqrt(self.hspeed**2 + self.vspeed**2)
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
            print("BRAKING.....")
            self.hspeed  *= brake_power
            self.vspeed  *= brake_power

        # Rotate player
        self.dir += self.rtspd

    def drawPlayer(self):
        a = math.radians(self.dir)
        x = self.x
        y = self.y
        s = player_size
        t = self.thrust
        # Draw player
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


class Rubble(pygame.sprite.Sprite):
    def __init__(self, x, y, room_id):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.room_id = room_id

        # Random size between player_size and 5 * player_size
        self.size = random.uniform(player_size, player_size * 5)

        # Random drift direction and speed
        drift_angle = random.uniform(0, 360)
        drift_speed = random.uniform(0.2, 0.8)
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



def render_room(map_sequence: room_schema.HydratedRoomSequence, n: int):
    room = map_sequence.rooms[n]

    for segment in room.walls:
        walls_sprites.add(Wall(segment))
    # test = Wall(vec(100, 100), vec(200, 150))


FramePerSec = pygame.time.Clock()

pygame.display.set_caption("INFINITE TEMPLE: Movement Test")

def collision_test(player, wall):
    length = math.sqrt((wall.coord_1.x - wall.coord_2.x) ** 2 + (wall.coord_1.y - wall.coord_2.y) ** 2)
    player_seg_0 = math.sqrt((player.x - wall.coord_1.x) ** 2 + (player.y - wall.coord_1.y) ** 2)
    player_seg_1 = math.sqrt((player.x - wall.coord_2.x) ** 2 + (player.y - wall.coord_2.y) ** 2)
    buffer = 1
    if length - buffer <= player_seg_0 + player_seg_1 <= length + buffer:
        return True
    return False


def build_room_sequence(room_file: str):
    active_map = load_map_file(room_file)
    #room_classes
    #getattr(module, member_name)
    hydrated_rooms = []
    for i, room_name in enumerate(active_map.rooms):
        room_class = getattr(room_schema, room_schema.room_classes[room_name])
        hydrated_rooms.append(room_class(i, 1000))
    return HydratedRoomSequence(rooms=hydrated_rooms)


def check_room_transition(player, current_room, map_size=1000):
    """
    Check if player has left the current room boundaries.

    Args:
        player: Player instance with x, y coordinates
        current_room: Room instance with walls defining the playable area
        map_size: Size of the map (default 1000)

    Returns:
        1 if player should move to next room (room_id + 1)
        -1 if player should move to previous room (room_id - 1)
        0 if player is still in current room
    """
    corridor_width = int(map_size * 0.2)
    center = map_size // 2
    corridor_start = center - corridor_width // 2
    corridor_end = center + corridor_width // 2

    # Determine room type by class name
    room_type = current_room.__class__.__name__

    # Check right edge (x > map_size)
    if player.x > map_size and corridor_start <= player.y <= corridor_end:
        # Forward exits (go to next room)
        if room_type in ["HorizontalPassage", "StartRoom", "ElbowTopRight", "ElbowBottomRight"]:
            walls_sprites.empty()
            return 1
        # Backward exits (go to previous room)
        if room_type in ["ElbowLeftTop", "ElbowLeftBottom"]:
            walls_sprites.empty()
            return -1

    # Check left edge (x < 0)
    if player.x < 0 and corridor_start <= player.y <= corridor_end:
        # Forward exits
        if room_type in ["ElbowTopLeft", "ElbowBottomLeft"]:
            walls_sprites.empty()
            return 1
        # Backward exits
        if room_type in ["HorizontalPassage", "ElbowRightTop", "ElbowRightBottom"]:
            walls_sprites.empty()
            return -1

    # Check bottom edge (y > map_size)
    if player.y > map_size and corridor_start <= player.x <= corridor_end:
        # Forward exits
        if room_type in ["VerticalPassage", "ElbowLeftBottom", "ElbowRightBottom"]:
            walls_sprites.empty()
            return 1
        # Backward exits
        if room_type in ["ElbowTopLeft", "ElbowTopRight"]:
            walls_sprites.empty()
            return -1

    # Check top edge (y < 0)
    if player.y < 0 and corridor_start <= player.x <= corridor_end:
        # Forward exits
        if room_type in ["ElbowLeftTop", "ElbowRightTop"]:
            walls_sprites.empty()
            return 1
        # Backward exits
        if room_type in ["VerticalPassage", "ElbowBottomLeft", "ElbowBottomRight"]:
            walls_sprites.empty()
            return -1

    return 0


def transition_player_to_room(player, direction, map_size=1000):
    """
    Move player to the appropriate entry point when transitioning between rooms.

    Args:
        player: Player instance with x, y coordinates
        direction: 1 for next room, -1 for previous room
        map_size: Size of the map (default 1000)
    """
    if direction == 1:  # Moving to next room
        # Determine which edge they exited from
        if player.x > map_size:  # Exited right, enter from left
            player.x = 0
            # y stays the same (maintain corridor position)
        elif player.x < 0:  # Exited left, enter from right
            player.x = map_size
            # y stays the same (maintain corridor position)
        elif player.y > map_size:  # Exited bottom, enter from top
            player.y = 0
            # x stays the same (maintain corridor position)
        elif player.y < 0:  # Exited top, enter from bottom
            player.y = map_size
            # x stays the same (maintain corridor position)

    elif direction == -1:  # Moving to previous room
        # Determine which edge they exited from
        if player.x < 0:  # Exited left, enter from right
            player.x = map_size
            # y stays the same (maintain corridor position)
        elif player.x > map_size:  # Exited right, enter from left
            player.x = 0
            # y stays the same (maintain corridor position)
        elif player.y < 0:  # Exited top, enter from bottom
            player.y = map_size
            # x stays the same (maintain corridor position)
        elif player.y > map_size:  # Exited bottom, enter from top
            player.y = 0
            # x stays the same (maintain corridor position)


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

room_id = 0

while True:
    surface.fill((0, 0, 0))
    P1.updatePlayer()
    P1.drawPlayer()
    print(room_id, " ", room_sequence.rooms[room_id].__class__.__name__)
    transition = check_room_transition(P1, room_sequence.rooms[room_id])
    transition_player_to_room(P1, transition)
    room_id += transition
    render_room(room_sequence, room_id)
    for rubble in rubble_sprites:
        if rubble.room_id == room_id:
            rubble.updateRubble()
            rubble.drawRubble()
            colliding = pygame.sprite.spritecollide(rubble, walls_sprites, False, collision_test)
            if len(colliding) > 0:
                rubble.dir = colliding[0].angle + 90
                rubble.hspeed *= -1
                rubble.vspeed *= -1

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                room_id += 1
                room_id = len(room_sequence.rooms) if room_id > len(room_sequence.rooms) else room_id
                walls_sprites.empty()
            if event.key == pygame.K_w:
                room_id -= 1
                room_id = 0 if room_id < 0 else room_id
                walls_sprites.empty()
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

    colliding = pygame.sprite.spritecollide(P1, walls_sprites, False, collision_test)
    if len(colliding) > 0:
        P1.dir = colliding[0].angle + 90
        P1.hspeed *= -1
        P1.vspeed *= -1
        #colliding[0]
    # for entity in all_sprites:
    #     if hasattr(entity, 'move'):
    #         entity.move()
    #     if hasattr(entity, 'update'):
    #         entity.update()
    #     surface.blit(entity.surf, entity.rect)
    pygame.display.update()
    FramePerSec.tick(30)