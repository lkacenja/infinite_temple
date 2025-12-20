import math
import random

import pygame

class Rubble(pygame.sprite.Sprite):
    def __init__(self, x, y, room_id, config):
        pygame.sprite.Sprite.__init__(self)
        self.surface = config.SURFACE

        self.x = x
        self.y = y
        self.room_id = room_id

        # Random size between player_size and 5 * player_size
        self.size = random.uniform(config.PLAYER_SIZE * 5, config.PLAYER_SIZE  * 10)
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
        screen_width = self.surface.get_width()
        screen_height = self.surface.get_height()

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
                pygame.draw.line(self.surface, (255, 255, 255), corners[i], corners[(i + 1) % 4])