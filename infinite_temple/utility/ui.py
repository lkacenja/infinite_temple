import pygame

from infinite_temple.utility.difficulty import calculate_difficulty

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
        """Draw the normal (non-animated) display with difficulty triangles."""
        difficulty = calculate_difficulty(self.highest_room_id)
        triangles = "^" * difficulty
        separator = " " if difficulty > 0 else ""
        text = f"{self.highest_room_id}{separator}{triangles}"
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

        difficulty = calculate_difficulty(self.last_milestone)
        triangles = "^" * difficulty
        separator = " " if difficulty > 0 else ""

        text_color = (255, 255, 255)
        scaled_font_size = int(self.font_size * scale)
        scaled_font = pygame.font.Font(None, scaled_font_size)
        text = f"{self.last_milestone}{separator}{triangles}"
        text_surface = scaled_font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        surface.blit(text_surface, text_rect)


class AmmoDisplay:
    """Displays player's remaining ammo as bullet icons."""

    def __init__(self, x, y):
        """
        Initialize the ammo display.

        Args:
            x: X position for the display
            y: Y position for the display
        """
        self.x = x
        self.y = y
        self.ammo_count = 0

    def set_ammo(self, count):
        """Set the ammo count (0-3)."""
        self.ammo_count = max(0, min(3, count))

    def draw(self, surface):
        """Draw the ammo display if player has ammo."""
        if self.ammo_count <= 0:
            return

        bullet_radius = 4
        spacing = 15
        for i in range(self.ammo_count):
            bx = self.x + (i * spacing)
            pygame.draw.circle(surface, (150, 150, 150), (bx, self.y), bullet_radius)
            pygame.draw.circle(surface, (100, 100, 100), (bx, self.y), bullet_radius, 1)
