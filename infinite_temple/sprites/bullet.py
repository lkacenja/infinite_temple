import math
import pygame


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, room_id, config, speed=8, size=4):
        pygame.sprite.Sprite.__init__(self)
        self.surface = config.surface
        self.x = x
        self.y = y
        self.room_id = room_id
        self.size = size
        self.radius = size

        # Calculate direction to target
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx * dx + dy * dy)

        # Normalize and set speed
        if distance > 0:
            self.hspeed = (dx / distance) * speed
            self.vspeed = (dy / distance) * speed
        else:
            self.hspeed = 0
            self.vspeed = 0

        self.rect = self.surface.get_rect()

    def updateBullet(self):
        """Update bullet position"""
        self.x += self.hspeed
        self.y += self.vspeed

    def drawBullet(self):
        """Draw the bullet as a small filled circle"""
        pygame.draw.circle(
            self.surface,
            (255, 255, 255),
            (int(self.x), int(self.y)),
            self.size
        )

    def is_off_screen(self, map_size):
        """Check if bullet is off screen"""
        margin = 100
        return (self.x < -margin or self.x > map_size + margin or
                self.y < -margin or self.y > map_size + margin)
