import sys
import time
import math
import json
import random
import os
import tempfile
import argparse
import threading

import pygame
from pygame.locals import *

from infinite_temple.utility.ui import HealthBar, RoomProgressDisplay, AmmoDisplay
from infinite_temple.utility.room import RoomManager, build_room_sequence, render_room
from infinite_temple.utility.music import play_music_file
from infinite_temple.utility.collision import *
from infinite_temple.utility.sfx import load_sound_effects, play_impact_sound, play_collapse_sound, play_priest_sound, play_vision_sound
from infinite_temple.sprites.player import Player
from infinite_temple.sprites.rubble import Rubble
from infinite_temple.utility.svg import draw_centered_surface, SVGLoader, render_text_fallback
from infinite_temple.schema.config import GameConfig
from infinite_temple.persistence.temple_repository import TempleRepository
from infinite_temple.utility.menu import (
    TempleSelector,
    WordPicker,
    EmptyStateMenu,
    GenerationProgressOverlay
)
from infinite_temple.generation.pipeline import TempleGenerationPipeline
from infinite_temple.spawning.enemy_spawner import EnemySpawner
from infinite_temple.spawning.powerup_spawner import PowerUpSpawner
from infinite_temple.sprites.power_up import PowerUp
from infinite_temple.sprites.bullet import Bullet

player_max_rtspd = 10

# Global references
repo = None
config = None
menu = None
temple = None
current_temple_svg = None
generation_overlay = None
generation_thread = None
generation_result = None
generation_error = None
room_sequence = None
room_manager = None
P1 = None
all_sprites = None
walls_sprites = None
rubble_sprites = None
priest_sprites = None
vision_sprites = None
bullet_sprites = None
enemy_spawner = None
powerup_sprites = None
powerup_spawner = None
health_bar = None
progress_display = None
ammo_display = None
start_screen_surface = None
game_over_surface = None


def initialize_game_state():
    """
    Initialize game state and menu.

    Returns tuple of (game_state, menu, current_temple_svg)
    """
    global repo

    repo = TempleRepository(base_dir="maps/temples")
    temples = repo.list_temples(sort_by="created_at")

    if not temples:
        # Empty state - show creation menu only
        menu = EmptyStateMenu(config.surface, handle_create_temple_clicked)
        return "menu", menu, None
    else:
        # Has temples - show selector
        menu = TempleSelector(
            config.surface,
            temples,
            handle_temple_selected,
            update_background_svg
        )
        # Load first temple's SVG as initial background
        first_temple = temples[0]
        svg = SVGLoader().load_svg(first_temple.title_svg_file, width=500, height=500)
        return "menu", menu, svg


pygame.init()

# Load sound effects
load_sound_effects()

config = GameConfig(
    display_width=800,
    display_height=800,
    player_size=10
)


def update_background_svg(temple_id):
    """
    Update background when selector changes.

    Args:
        temple_id: Temple ID for background
    """
    global current_temple_svg

    if temple_id == "CREATE_NEW":
        current_temple_svg = None
        return

    loaded_temple = repo.load_temple(temple_id)
    if loaded_temple:
        current_temple_svg = SVGLoader().load_svg(
            loaded_temple.title_svg_file,
            width=config.display_width,
            height=config.display_height
        )


def handle_back_to_menu():
    """Handle back button from word picker."""
    global menu

    temples = repo.list_temples(sort_by="created_at")
    if temples:
        menu = TempleSelector(
            config.surface,
            temples,
            handle_temple_selected,
            update_background_svg
        )
    else:
        menu = EmptyStateMenu(config.surface, handle_create_temple_clicked)


def handle_temple_selected(selected_id):
    """Handle temple selection from menu."""
    global menu

    if selected_id == "CREATE_NEW":
        # Switch to word picker
        menu = WordPicker(config.surface, handle_generation_started, handle_back_to_menu)
    else:
        # Load and start temple
        load_and_start_temple(selected_id)


def handle_create_temple_clicked():
    """Handle create temple button from empty state."""
    global menu
    menu = WordPicker(config.surface, handle_generation_started, handle_back_to_menu)


def handle_generation_started(word1, word2, word3):
    """Handle temple generation start."""
    global game_state, generation_overlay, generation_thread, generation_result, generation_error

    game_state = "generating"
    generation_overlay = GenerationProgressOverlay(config.surface)
    generation_result = None
    generation_error = None

    def generation_worker():
        """Worker thread for temple generation."""
        global generation_result, generation_error

        pipeline = TempleGenerationPipeline(model="gpt-5-nano")
        try:
            temple_config = pipeline.generate_temple(
                seed_words=[word1, word2, word3],
                room_count=100,
                progress_callback=generation_overlay.update_progress
            )
            generation_result = temple_config
        except Exception as e:
            generation_error = e

    # Start generation in background thread
    generation_thread = threading.Thread(target=generation_worker, daemon=True)
    generation_thread.start()


def handle_generation_complete(temple_config):
    """Handle successful temple generation."""
    load_and_start_temple(temple_config.temple_id)


def handle_generation_error(error):
    """Handle generation failure."""
    global game_state, menu

    print(f"Generation failed: {error}")

    # Return to main menu
    game_state = "menu"
    temples = repo.list_temples(sort_by="created_at")
    if temples:
        menu = TempleSelector(
            config.surface,
            temples,
            handle_temple_selected,
            update_background_svg
        )
    else:
        menu = EmptyStateMenu(config.surface, handle_create_temple_clicked)


def load_and_start_temple(temple_id):
    """
    Load temple assets and initialize gameplay.

    Args:
        temple_id: Temple ID to load
    """
    global game_state, temple, room_sequence, room_manager
    global P1, all_sprites, walls_sprites, rubble_sprites
    global priest_sprites, vision_sprites, bullet_sprites, enemy_spawner
    global powerup_sprites, powerup_spawner
    global health_bar, progress_display, ammo_display
    global start_screen_surface, game_over_surface

    # Load temple
    temple = repo.load_temple(temple_id)
    if not temple:
        print(f"Error loading temple {temple_id}")
        return

    print(f"Loading temple: {temple.narrative.title}")
    print(f"Seed words: {', '.join(temple.seed_words)}")
    print(f"Rooms: {temple.room_count}")

    # Load temple assets
    room_sequence, main_path_length = build_room_sequence(temple.map_file, config)
    room_manager = RoomManager(room_sequence, main_path_length)
    play_music_file(temple.audio_file)

    # Initialize player
    P1 = Player(*config.center, config)
    all_sprites = pygame.sprite.Group()
    all_sprites.add(P1)
    walls_sprites = pygame.sprite.Group()
    rubble_sprites = pygame.sprite.Group()
    priest_sprites = pygame.sprite.Group()
    vision_sprites = pygame.sprite.Group()
    bullet_sprites = pygame.sprite.Group()
    powerup_sprites = pygame.sprite.Group()
    enemy_spawner = EnemySpawner(config)
    powerup_spawner = PowerUpSpawner(config)

    # Initialize UI
    health_bar = HealthBar(10, 10, 300, 8)
    progress_display = RoomProgressDisplay(
        x=config.display_width - 30,
        y=19,
        font_size=19
    )
    ammo_display = AmmoDisplay(x=13, y=30)

    # Load SVGs
    start_screen_surface = SVGLoader().load_svg(temple.title_svg_file, width=config.display_width, height=config.display_height)
    game_over_surface = SVGLoader().load_svg(temple.gameover_svg_file, width=config.display_width, height=config.display_height)

    # Render initial room
    room = room_manager.get_current_room()
    render_room(room, walls_sprites, config)

    # Spawn enemies for starting room
    enemy_spawner.spawn_for_room(
        room_manager.current_room_id,
        room_manager.get_main_path_progress(),
        room,
        priest_sprites,
        vision_sprites,
        rubble_sprites
    )

    # Update caption
    pygame.display.set_caption(f"INFINITE TEMPLE - {temple.narrative.title}")

    # Transition to start screen
    game_state = "start_screen"


def add_rubble(room_id, room_name):
    if room_name in ("antechamber_horizontal", "antechamber_vertical"):
        for n in range(random.randrange(3, 5)):
            rubble = Rubble(500, 500, room_id, config)
            rubble_sprites.add(rubble)


DOUBLE_TAP_THRESHOLD = 0.3  # seconds
last_left_press = 0
last_right_press = 0


def snap_to_nearest_90(current_angle, direction):
    """
    Snap to the next 90-degree angle in the specified direction.

    Args:
        current_angle: Current angle in degrees
        direction: 'ccw' for counter-clockwise, 'cw' for clockwise

    Returns:
        The target 90-degree angle
    """
    # Normalize angle to 0-360
    angle = current_angle % 360

    # The four cardinal angles
    cardinal_angles = [0, 90, 180, 270]

    if direction == 'ccw':  # Counter-clockwise (left)
        # Find the next angle counter-clockwise
        for target in sorted(cardinal_angles, reverse=True):
            if target < angle:
                return target
        return 270  # Wrap around to 270 if we're past 0

    else:  # Clockwise (right)
        # Find the next angle clockwise
        for target in sorted(cardinal_angles):
            if target > angle:
                return target
        return 0  # Wrap around to 0 if we're past 270


# Initialize game state
game_state, menu, current_temple_svg = initialize_game_state()

FramePerSec = pygame.time.Clock()
clock = pygame.time.Clock()

death_timer = 0
DEATH_DELAY = 5.0

# Main game loop
while True:
    dt = clock.tick(60) / 1000.0

    # Handle events
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        # Menu state - pass events to menu
        if game_state == "menu":
            menu.handle_event(event)

        # Generating state - no interaction
        elif game_state == "generating":
            pass

        elif event.type == pygame.KEYDOWN:
            # Start screen controls
            if game_state == "start_screen":
                if event.key == pygame.K_SPACE:
                    game_state = "playing"
                    death_timer = 0

            # Game over controls
            elif game_state == "game_over":
                if event.key == pygame.K_SPACE:
                    # Return to menu
                    temples = repo.list_temples(sort_by="created_at")
                    if temples:
                        menu = TempleSelector(
                            config.surface,
                            temples,
                            handle_temple_selected,
                            update_background_svg
                        )
                    else:
                        menu = EmptyStateMenu(config.surface, handle_create_temple_clicked)
                    game_state = "menu"

            # Playing controls
            elif game_state == "playing":
                if P1:
                    if event.key == pygame.K_UP:
                        P1.thrust = True
                    if event.key == pygame.K_LEFT:
                        current_time = time.time()

                        # Check for double-tap
                        if current_time - last_left_press < DOUBLE_TAP_THRESHOLD:
                            # Double-tap detected! Snap counter-clockwise
                            target_angle = snap_to_nearest_90(P1.dir, 'ccw')
                            P1.dir = target_angle
                            P1.rtspd = 0  # Stop rotation
                            last_left_press = 0  # Reset to prevent triple-tap
                        else:
                            # Single tap - normal rotation
                            P1.rtspd = -player_max_rtspd
                            last_left_press = current_time

                    if event.key == pygame.K_RIGHT:
                        current_time = time.time()

                        # Check for double-tap
                        if current_time - last_right_press < DOUBLE_TAP_THRESHOLD:
                            # Double-tap detected! Snap clockwise
                            target_angle = snap_to_nearest_90(P1.dir, 'cw')
                            P1.dir = target_angle
                            P1.rtspd = 0  # Stop rotation
                            last_right_press = 0  # Reset to prevent triple-tap
                        else:
                            # Single tap - normal rotation
                            P1.rtspd = player_max_rtspd
                            last_right_press = current_time
                    if event.key == pygame.K_SPACE:
                        P1.braking = True
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        target = P1.fire_bullet()
                        if target:
                            bullet = Bullet(P1.x, P1.y, target[0], target[1],
                                          room_manager.current_room_id, config, speed=12, size=3)
                            bullet.is_player_bullet = True
                            bullet_sprites.add(bullet)

        if event.type == pygame.KEYUP:
            if game_state == "playing" and P1:
                if event.key == pygame.K_UP:
                    P1.thrust = False
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    P1.rtspd = 0
                if event.key == pygame.K_SPACE:
                    P1.braking = False

    # Check for generation completion
    if game_state == "generating" and generation_thread:
        if not generation_thread.is_alive():
            # Generation finished
            if generation_result:
                handle_generation_complete(generation_result)
            elif generation_error:
                handle_generation_error(generation_error)
            generation_thread = None

    # Clear screen
    config.surface.fill((0, 0, 0))

    # Render based on game state
    if game_state == "menu":
        # Draw temple background SVG
        if current_temple_svg:
            draw_centered_surface(config.surface, current_temple_svg)

        # Draw menu on top
        menu.draw()

    elif game_state == "generating":
        # Draw progress overlay
        if generation_overlay:
            generation_overlay.draw()

    elif game_state == "start_screen":
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
        if not P1 or not room_manager:
            # Safety check - shouldn't happen
            pass
        else:
            # Check for death
            if P1.current_health <= 0:
                death_timer += dt
                if death_timer >= DEATH_DELAY:
                    game_state = "game_over"
                    death_timer = 0
            else:
                death_timer = 0

            # Update player movement
            P1.updatePlayer()

            # Check room transitions FIRST (before collision pushes player back)
            # Portal trigger zones extend beyond room boundaries to catch player before wall collision
            transition = room_manager.check_transition(P1, debug=False)
            if transition:
                walls_sprites.empty()
                room = room_manager.get_current_room()
                render_room(room, walls_sprites, config)

                # Reset rubble entrance sound flags for all rubble
                for rubble in rubble_sprites:
                    rubble.entrance_sound_played = False

                # Spawn enemies for new room
                enemy_spawner.spawn_for_room(
                    room_manager.current_room_id,
                    room_manager.get_main_path_progress(),
                    room,
                    priest_sprites,
                    vision_sprites,
                    rubble_sprites
                )

                # Spawn powerups for new room
                powerup_spawner.spawn_for_room(
                    room_manager.current_room_id,
                    room,
                    room_manager.last_entry_portal,
                    powerup_sprites
                )
            else:
                # Only check collisions if we didn't transition
                # Player-wall collision detection and response (BEFORE drawing to prevent tunneling)
                # Check multiple times per frame if moving fast to prevent tunneling
                speed = math.sqrt(P1.hspeed ** 2 + P1.vspeed ** 2)
                collision_iterations = max(1, int(speed / (P1.radius / 2)))

                for _ in range(collision_iterations):
                    colliding = pygame.sprite.spritecollide(P1, walls_sprites, False, wall_collision_test)
                    if len(colliding) > 0:
                        play_impact_sound(volume=0.25)
                        handle_wall_collision(P1, colliding[0])
                        break

            # Draw player
            P1.drawPlayer()

            # Update rubble
            for rubble in rubble_sprites:
                if rubble.room_id == room_manager.current_room_id:
                    # Play entrance sound once per room entry
                    if not rubble.entrance_sound_played:
                        play_collapse_sound(volume=0.4)
                        rubble.entrance_sound_played = True

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
                        play_impact_sound(volume=0.25)

            # Update priests
            player_is_moving = abs(P1.hspeed) > 0.1 or abs(P1.vspeed) > 0.1
            for priest in priest_sprites:
                if priest.room_id == room_manager.current_room_id:
                    # Store position before movement
                    old_x = priest.x
                    old_y = priest.y

                    priest.updatePriest(P1.x, P1.y, player_is_moving)

                    # Play sound when priest starts charging
                    if priest.just_started_charging:
                        play_priest_sound(volume=0.4)

                    # Check if priest is too close to walls (within 10 pixels)
                    # Temporarily increase radius for wall check
                    original_radius = priest.radius
                    priest.radius = original_radius + 10

                    colliding = pygame.sprite.spritecollide(priest, walls_sprites, False, wall_collision_test)
                    if len(colliding) > 0:
                        # Too close to wall, revert position
                        priest.x = old_x
                        priest.y = old_y
                        priest.hspeed = 0
                        priest.vspeed = 0

                    # Restore original radius
                    priest.radius = original_radius

                    priest.drawPriest()

                    # Priest-player collision
                    if rubble_collision_test(P1, priest):
                        handle_rubble_collision(P1, priest)
                        play_impact_sound(volume=0.25)

                    # Check if priest should fire
                    should_fire, target_x, target_y = priest.should_fire()
                    if should_fire:
                        bullet = Bullet(priest.x, priest.y, target_x, target_y, room_manager.current_room_id, config)
                        bullet_sprites.add(bullet)

            # Update visions
            for vision in vision_sprites:
                if vision.room_id == room_manager.current_room_id:
                    vision.updateVision(dt, P1.x, P1.y)

                    # Play sound when vision explodes
                    if vision.just_exploded:
                        play_vision_sound(volume=0.5)
                        vision.just_exploded = False

                    vision.drawVision()

                    # Vision fragment collisions with player
                    for frag_x, frag_y, frag_radius in vision.getFragmentPositions():
                        dx = P1.x - frag_x
                        dy = P1.y - frag_y
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist < P1.radius + frag_radius:
                            P1.current_health -= 0.5  # Damage per frame

                    # Remove finished visions
                    if vision.isFinished():
                        vision_sprites.remove(vision)

            # Update powerups
            for powerup in list(powerup_sprites):
                if powerup.room_id == room_manager.current_room_id:
                    powerup.updatePowerUp()
                    powerup.drawPowerUp()

                    # Check collision with player
                    dx = P1.x - powerup.x
                    dy = P1.y - powerup.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < P1.radius + powerup.radius:
                        powerup.collect(P1)
                        powerup_sprites.remove(powerup)

            # Update bullets
            for bullet in list(bullet_sprites):
                if bullet.room_id == room_manager.current_room_id:
                    bullet.updateBullet()
                    bullet.drawBullet()

                    # Bullet-player collision
                    dx = P1.x - bullet.x
                    dy = P1.y - bullet.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < P1.radius + bullet.radius:
                        # Skip player's own bullets
                        if getattr(bullet, 'is_player_bullet', False):
                            continue
                        # Shield absorbs priest bullets
                        if P1.shield > 0:
                            P1.shield -= 1
                        else:
                            P1.current_health -= 10
                        bullet_sprites.remove(bullet)
                        continue

                    # Player bullet vs enemies
                    if getattr(bullet, 'is_player_bullet', False):
                        # Check rubble
                        for rubble in list(rubble_sprites):
                            if rubble.room_id == room_manager.current_room_id:
                                dx = rubble.x - bullet.x
                                dy = rubble.y - bullet.y
                                dist = math.sqrt(dx*dx + dy*dy)
                                if dist < rubble.radius + bullet.radius:
                                    rubble_sprites.remove(rubble)
                                    bullet_sprites.remove(bullet)
                                    break
                        else:
                            # Check priests (only if bullet wasn't removed)
                            for priest in list(priest_sprites):
                                if priest.room_id == room_manager.current_room_id:
                                    dx = priest.x - bullet.x
                                    dy = priest.y - bullet.y
                                    dist = math.sqrt(dx*dx + dy*dy)
                                    if dist < priest.radius + bullet.radius:
                                        priest_sprites.remove(priest)
                                        bullet_sprites.remove(bullet)
                                        break
                            else:
                                # Bullet-wall collision (only if not removed)
                                colliding = pygame.sprite.spritecollide(bullet, walls_sprites, False, wall_collision_test)
                                if len(colliding) > 0:
                                    bullet_sprites.remove(bullet)
                                    continue
                        continue

                    # Bullet-wall collision (for priest bullets)
                    colliding = pygame.sprite.spritecollide(bullet, walls_sprites, False, wall_collision_test)
                    if len(colliding) > 0:
                        bullet_sprites.remove(bullet)
                        continue

                    # Remove bullets that go off screen
                    if bullet.is_off_screen(config.display_width):
                        bullet_sprites.remove(bullet)

            # Draw walls
            for wall in walls_sprites:
                wall.drawWall()

            # Draw UI
            percent_health = (P1.current_health / P1.max_health if P1.current_health > 0 else 0) * 100
            health_bar.set_health(percent_health)
            health_bar.draw(config.surface)

            progress_display.update(room_manager.get_unique_rooms_visited(), dt)
            progress_display.draw(config.surface)

            ammo_display.set_ammo(P1.ammo)
            ammo_display.draw(config.surface)

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