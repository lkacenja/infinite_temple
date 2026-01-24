import math
import random
import pygame


class Priest(pygame.sprite.Sprite):
    def __init__(self, x, y, room_id, config):
        pygame.sprite.Sprite.__init__(self)
        self.priest_size = config.player_size
        self.surface = config.surface
        self.x = x
        self.y = y
        self.room_id = room_id

        self.hspeed = 0
        self.vspeed = 0
        self.dir = 0  # Direction in degrees
        self.rect = self.surface.get_rect()
        self.radius = self.priest_size * 0.85

        self.max_health = 50
        self.current_health = self.max_health

        # AI state machine
        self.state = "moving"  # moving, charging, firing
        self.move_speed = 1.5  # Slow movement
        self.state_timer = 0
        self.move_duration = random.uniform(0.5, 1.0)  # Random 0.5-1 seconds
        self.charge_duration = 0.5  # 0.5 seconds to charge

        # Target tracking
        self.target_x = 0
        self.target_y = 0

        # Track state changes
        self.just_started_charging = False

    def updatePriest(self, player_x, player_y, player_is_moving):
        """Update priest AI and position

        Args:
            player_x: Player's current x position
            player_y: Player's current y position
            player_is_moving: Whether the player is currently moving
        """
        # Reset state change flag
        self.just_started_charging = False

        if self.state == "moving":
            # Timer always advances
            self.state_timer += 1/60  # Assuming 60 FPS

            # Only physically move when player is moving
            if player_is_moving:
                # Move away from player only if player is within 50 pixels
                dx = self.x - player_x
                dy = self.y - player_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0 and distance <= 50:
                    # Normalize and apply move speed
                    self.hspeed = (dx / distance) * self.move_speed
                    self.vspeed = (dy / distance) * self.move_speed

                    # Update position
                    self.x += self.hspeed
                    self.y += self.vspeed
                else:
                    # Player is too far, don't move
                    self.hspeed = 0
                    self.vspeed = 0

            # Check if it's time to start charging (independent of player movement)
            if self.state_timer >= self.move_duration:
                self.state = "charging"
                self.state_timer = 0
                self.just_started_charging = True
                # Store player position at start of charge
                self.target_x = player_x
                self.target_y = player_y
                # Stop moving
                self.hspeed = 0
                self.vspeed = 0

        elif self.state == "charging":
            # Charging happens independently of player movement
            self.state_timer += 1/60  # Assuming 60 FPS
            # Track player through 80% of charge, then lock final position
            if self.state_timer < self.charge_duration * 0.8:
                self.target_x = player_x
                self.target_y = player_y
            if self.state_timer >= self.charge_duration:
                self.state = "firing"
                self.state_timer = 0

        elif self.state == "firing":
            # Transition back to moving immediately after firing
            self.state = "moving"
            self.state_timer = 0
            self.move_duration = random.uniform(0.5, 1.0)  # New random duration

        # Slowly rotate the priest
        self.dir += 0.5

    def drawPriest(self):
        """Draw the diamond-shaped priest with a circle in the center"""
        if self.current_health <= 0:
            return

        x = self.x
        y = self.y
        s = self.priest_size
        a = math.radians(self.dir)

        # Calculate diamond vertices (top, right, bottom, left)
        # Rotating the diamond by the current direction
        top = (
            x + s * math.cos(a),
            y + s * math.sin(a)
        )
        right = (
            x + s * math.cos(a + math.pi / 2),
            y + s * math.sin(a + math.pi / 2)
        )
        bottom = (
            x + s * math.cos(a + math.pi),
            y + s * math.sin(a + math.pi)
        )
        left = (
            x + s * math.cos(a + 3 * math.pi / 2),
            y + s * math.sin(a + 3 * math.pi / 2)
        )

        # Draw the diamond (4 lines connecting the vertices)
        pygame.draw.line(self.surface, (255, 255, 255), top, right)
        pygame.draw.line(self.surface, (255, 255, 255), right, bottom)
        pygame.draw.line(self.surface, (255, 255, 255), bottom, left)
        pygame.draw.line(self.surface, (255, 255, 255), left, top)

        # Draw the circle in the center
        circle_radius = int(s * 0.4)  # Circle is 40% of the priest size

        if self.state == "charging":
            # Fill the circle while charging
            pygame.draw.circle(self.surface, (255, 255, 255), (int(x), int(y)), circle_radius)
        else:
            # Draw outline circle when not charging
            pygame.draw.circle(self.surface, (255, 255, 255), (int(x), int(y)), circle_radius, 1)

    def should_fire(self):
        """Check if priest should fire this frame

        Returns:
            Tuple of (should_fire: bool, target_x, target_y) or (False, 0, 0)
        """
        if self.state == "firing":
            return (True, self.target_x, self.target_y)
        return (False, 0, 0)