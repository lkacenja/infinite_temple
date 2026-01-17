import math
import pygame


class PowerUp(pygame.sprite.Sprite):
    # Power-up types
    HEALTH = "H"
    SHIELD = "S"
    AMMO = "A"

    def __init__(self, x, y, power_type, room_id, config):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.power_type = power_type
        self.room_id = room_id
        self.size = int(config.player_size * 1.2)
        self.surface = config.surface
        self.radius = self.size

        # Animation properties
        self.rotation = 0
        self.rotation_speed = 1.5
        self.pulse_timer = 0
        self.pulse_speed = 0.08

        # For collision detection
        self.rect = pygame.Rect(x - self.size, y - self.size,
                                self.size * 2, self.size * 2)

        # Set up font for letter rendering
        self.font = pygame.font.Font(None, int(self.size * 1.2))

    def updatePowerUp(self):
        """Update animation state"""
        self.rotation += self.rotation_speed
        if self.rotation >= 360:
            self.rotation -= 360

        self.pulse_timer += self.pulse_speed
        if self.pulse_timer >= 2 * math.pi:
            self.pulse_timer -= 2 * math.pi

        # Update rect for collision
        self.rect.center = (self.x, self.y)

    def drawPowerUp(self):
        """Draw the power-up with line art style"""
        # Pulsing effect for size
        pulse = 1 + 0.1 * math.sin(self.pulse_timer)
        current_size = self.size * pulse

        # Draw outer circle using line segments (matching line art style)
        num_segments = 24
        points = []
        for i in range(num_segments):
            angle = math.radians(self.rotation + (360 / num_segments) * i)
            px = self.x + current_size * math.cos(angle)
            py = self.y + current_size * math.sin(angle)
            points.append((px, py))

        # Draw circle outline
        for i in range(num_segments):
            start = points[i]
            end = points[(i + 1) % num_segments]
            pygame.draw.line(self.surface, (255, 255, 255), start, end)

        # Draw inner decorative ring
        inner_size = current_size * 0.7
        inner_points = []
        for i in range(num_segments):
            angle = math.radians(-self.rotation * 0.5 + (360 / num_segments) * i)
            px = self.x + inner_size * math.cos(angle)
            py = self.y + inner_size * math.sin(angle)
            inner_points.append((px, py))

        for i in range(0, num_segments, 2):  # Dashed inner ring
            start = inner_points[i]
            end = inner_points[(i + 1) % num_segments]
            pygame.draw.line(self.surface, (255, 255, 255), start, end)

        # Draw the letter in the center
        letter_surface = self.font.render(self.power_type, True, (255, 255, 255))
        letter_rect = letter_surface.get_rect(center=(self.x, self.y))
        self.surface.blit(letter_surface, letter_rect)

    def collect(self, player):
        """Apply power-up effect to player"""
        if self.power_type == self.HEALTH:
            heal_amount = int(player.max_health * 0.5)
            player.current_health = min(player.current_health + heal_amount,
                                        player.max_health)
        elif self.power_type == self.SHIELD:
            player.shield = 2
        elif self.power_type == self.AMMO:
            player.ammo = 3
