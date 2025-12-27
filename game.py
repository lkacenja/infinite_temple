import sys
import time
import math
import json
import random
import os
import tempfile

import pygame
from pygame.locals import *

from infinite_temple.utility.ui import HealthBar, RoomProgressDisplay
from infinite_temple.utility.room import RoomManager, build_room_sequence, render_room
#from infinite_temple.utility.music import play_music_file
from infinite_temple.utility.collision import *
from infinite_temple.sprites.player import Player
from infinite_temple.sprites.rubble import Rubble
from infinite_temple.utility.svg import draw_centered_surface, SVGLoader, render_text_fallback
from infinite_temple.schema.config import GameConfig

player_max_rtspd = 10

pygame.init()

config = GameConfig(
    display_width=1000,
    display_height=1000,
    player_size=10
)

def add_rubble(room_id, room_type):
    if room_type in ("AntechamberHorizontal", "AntechamberVertical"):
        for n in range(random.randrange(3, 5)):
            rubble = Rubble(500, 500, room_id, config)
            rubble_sprites.add(rubble)


P1 = Player(500, 500, config)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)

walls_sprites = pygame.sprite.Group()

rubble_sprites = pygame.sprite.Group()

FramePerSec = pygame.time.Clock()

pygame.display.set_caption("INFINITE TEMPLE")

room_sequence = build_room_sequence("maps/map-1765062702.200778.json")
room_manager = RoomManager(room_sequence)

#play_music_file("maps/audio-1765141789.983802.json")

room = room_manager.get_current_room()
render_room(room, walls_sprites, config)

progress_display = RoomProgressDisplay(x=config.display_width - 30, y=19, font_size=19)

for n, room in enumerate(room_sequence.rooms):
    add_rubble(n, room.__class__.__name__)

health_bar = HealthBar(10, 10, 300, 8)
current_health = 100.0

clock = pygame.time.Clock()

# Game state
game_state = "start_screen"
start_screen_surface = SVGLoader().load_svg("maps/infinite_temple_poster.svg", width=500, height=500)
game_over_surface = SVGLoader().load_svg("maps/game_over_poster.svg", width=500, height=500)

death_timer = 0  # Timer for game over delay
DEATH_DELAY = 5.0  # 5 seconds delay before game over screen

# Main game loop
while True:
    dt = clock.tick(60) / 1000.0

    # Handle events
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            # Start screen controls
            if game_state == "start_screen":
                if event.key == pygame.K_SPACE:
                    game_state = "playing"
                    death_timer = 0

            # Game over controls
            elif game_state == "game_over":
                if event.key == pygame.K_SPACE:
                    # Reset game
                    game_state = "start_screen"
                    death_timer = 0
                    P1.current_health = P1.max_health
                    P1.x = 500
                    P1.y = 500
                    P1.velocity = pygame.math.Vector2(0, 0)

            # Playing controls
            elif game_state == "playing":
                if event.key == pygame.K_UP:
                    P1.thrust = True
                if event.key == pygame.K_LEFT:
                    P1.rtspd = -player_max_rtspd
                if event.key == pygame.K_RIGHT:
                    P1.rtspd = player_max_rtspd
                if event.key == pygame.K_SPACE:
                    P1.braking = True

        if event.type == pygame.KEYUP:
            if game_state == "playing":
                if event.key == pygame.K_UP:
                    P1.thrust = False
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    P1.rtspd = 0
                if event.key == pygame.K_SPACE:
                    P1.braking = False

    # Clear screen
    config.surface.fill((0, 0, 0))

    # Render based on game state
    if game_state == "start_screen":
        # Draw start screen SVG
        if start_screen_surface:
            draw_centered_surface(config.surface, start_screen_surface)
        else:
            # Fallback if SVG doesn't load
            render_text_fallback(config.surface, "INFINITE TEMPLE", 72)
            font = pygame.font.Font(None, 36)
            press_space = font.render("Press SPACE to start", True, (255, 255, 255))
            draw_centered_surface(config.surface, press_space, y_offset=100)

    elif game_state == "playing":
        # Check for death
        if P1.current_health <= 0:
            death_timer += dt
            if death_timer >= DEATH_DELAY:
                game_state = "game_over"
                death_timer = 0
        else:
            death_timer = 0

        # Update player
        P1.updatePlayer()
        P1.drawPlayer()

        # Check room transitions
        transition = room_manager.check_transition(P1, 1000)
        if transition:
            walls_sprites.empty()
            room = room_manager.get_current_room()
            render_room(room, walls_sprites, config)

        # Update rubble
        for rubble in rubble_sprites:
            if rubble.room_id == room_manager.current_room_id:
                rubble.updateRubble()
                rubble.drawRubble()

                # Rubble-wall collisions
                colliding = pygame.sprite.spritecollide(rubble, walls_sprites, False, wall_collision_test)
                if len(colliding) > 0:
                    rubble.dir = colliding[0].angle + 90
                    rubble.hspeed *= -1
                    rubble.vspeed *= -1

                # Rubble-player collisions
                colliding = pygame.sprite.spritecollide(P1, [rubble], False, rubble_collision_test)
                if len(colliding) > 0:
                    handle_rubble_collision(P1, colliding[0])

        # Draw walls
        for wall in walls_sprites:
            wall.drawWall()

        # Player-wall collisions
        colliding = pygame.sprite.spritecollide(P1, walls_sprites, False, wall_collision_test)
        if len(colliding) > 0:
            handle_wall_collision(P1, colliding[0])

        # Draw UI
        percent_health = (P1.current_health / P1.max_health if P1.current_health > 0 else 0) * 100
        health_bar.set_health(percent_health)
        health_bar.draw(config.surface)

        progress_display.update(room_manager.current_room_id, dt)
        progress_display.draw(config.surface)

    elif game_state == "game_over":
        # Draw game over screen SVG
        if game_over_surface:
            draw_centered_surface(config.surface, game_over_surface)
        else:
            # Fallback if SVG doesn't load
            render_text_fallback(config.surface, "GAME OVER", 72)
            font = pygame.font.Font(None, 36)
            press_space = font.render("Press SPACE to continue", True, (255, 255, 255))
            draw_centered_surface(config.surface, press_space, y_offset=100)

    # Update display
    pygame.display.update()
    FramePerSec.tick(30)