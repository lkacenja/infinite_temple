import math

import pygame

from infinite_temple.schema.room import Segment

class Wall(pygame.sprite.Sprite):
    def __init__(self, segment: Segment, config):
        pygame.sprite.Sprite.__init__(self)
        vec = config.vec
        self.surface = config.surface
        self.coord_1 = vec(segment.coord_1.x, segment.coord_1.y)
        self.coord_2 = vec(segment.coord_2.x, segment.coord_2.y)
        rads = math.atan2(self.coord_2.y - self.coord_1.y, self.coord_2.x - self.coord_1.x)
        self.angle = rads * (180 / math.pi)
        self.rect = self.surface.get_rect()

    def drawWall(self):
        # Consistent shadow direction (down and to the right, like light from upper-left)
        shadow_offset_x = 4
        shadow_offset_y = 4

        # Shadow coordinates (consistent offset for all walls)
        shadow_coord_1 = (self.coord_1.x + shadow_offset_x,
                         self.coord_1.y + shadow_offset_y)
        shadow_coord_2 = (self.coord_2.x + shadow_offset_x,
                         self.coord_2.y + shadow_offset_y)

        # Draw darker gray outline first (more visible)
        pygame.draw.line(self.surface, (40, 40, 40), shadow_coord_1, shadow_coord_2, 3)

        # Draw white wall on top
        pygame.draw.line(self.surface, (255, 255, 255), self.coord_1, self.coord_2, 2)