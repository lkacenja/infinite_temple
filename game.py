import sys
import time
import math
import json
import random
import os
import tempfile

import pygame
from pygame.locals import *
# from tomita.legacy import pysynth_c as synthesizer

from infinite_temple.utility.ui import HealthBar, RoomProgressDisplay
from infinite_temple.utility.room import RoomManager, build_room_sequence, render_room
from infinite_temple.utility.collision import *
from infinite_temple.sprites.player import Player
from infinite_temple.sprites.rubble import Rubble

display_width = 1000
display_height = 1000

player_size = 10

player_max_rtspd = 10

pygame.init()


class GameConfig:
    DISPLAY_WIDTH = 1000
    DISPLAY_HEIGHT = 1000
    PLAYER_SIZE = 10
    SURFACE = pygame.display.set_mode((1000, 1000))
    VEC = pygame.math.Vector2

def add_rubble(room_id, room_type):
    if room_type in ("StartRoom", "AntechamberHorizontal", "AntechamberVertical"):
        for n in range(random.randrange(3, 5)):
            rubble = Rubble(500, 500, room_id, GameConfig)
            rubble_sprites.add(rubble)


P1 = Player(500, 500, GameConfig)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)

walls_sprites = pygame.sprite.Group()

rubble_sprites = pygame.sprite.Group()

FramePerSec = pygame.time.Clock()

pygame.display.set_caption("INFINITE TEMPLE")

room_sequence = build_room_sequence("maps/map-1765062702.200778.json")
room_manager = RoomManager(room_sequence)

# play_music_file("maps/audio-1765141789.983802.json")

room = room_manager.get_current_room()
render_room(room, walls_sprites, GameConfig)

progress_display = RoomProgressDisplay(x=display_width - 30, y=19, font_size=19)

for n, room in enumerate(room_sequence.rooms):
    add_rubble(n, room.__class__.__name__)

health_bar = HealthBar(10, 10, 300, 8)
current_health = 100.0

clock = pygame.time.Clock()

while True:
    dt = clock.tick(60) / 1000.0

    GameConfig.SURFACE.fill((0, 0, 0))
    P1.updatePlayer()
    P1.drawPlayer()

    transition = room_manager.check_transition(P1, 1000)
    if transition:
        walls_sprites.empty()
        room = room_manager.get_current_room()
        render_room(room, walls_sprites, GameConfig)
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
    health_bar.draw(GameConfig.SURFACE)

    progress_display.update(room_manager.current_room_id, dt)
    progress_display.draw(GameConfig.SURFACE)

    pygame.display.update()
    FramePerSec.tick(30)
