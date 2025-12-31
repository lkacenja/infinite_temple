import math
import pygame


class Priest(pygame.sprite.Sprite):
    def __init__(self, x, y, config):
        pygame.sprite.Sprite.__init__(self)
        self.priest_size = config.player_size  # Default size if not in config
        self.surface = config.surface
        self.x = x
        self.y = y

        self.hspeed = 0
        self.vspeed = 0
        self.dir = 0  # Direction in degrees
        self.rect = self.surface.get_rect()
        self.radius = self.priest_size * 0.85

        self.max_health = 50
        self.current_health = self.max_health

    def updatePriest(self):
        """Update priest position"""
        self.x += self.hspeed
        self.y += self.vspeed

        # Optional: slowly rotate the priest
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
        pygame.draw.circle(self.surface, (255, 255, 255), (int(x), int(y)), circle_radius, 1)