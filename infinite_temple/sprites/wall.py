import math

import pygame

from infinite_temple.schema.room import Segment

class Wall(pygame.sprite.Sprite):
    def __init__(self, segment: Segment, config):
        pygame.sprite.Sprite.__init__(self)
        vec = config.VEC
        self.surface = config.SURFACE
        self.coord_1 = vec(segment.coord_1.x, segment.coord_1.y)
        self.coord_2 = vec(segment.coord_2.x, segment.coord_2.y)
        rads = math.atan2(self.coord_2.y - self.coord_1.y, self.coord_2.x - self.coord_1.x)
        self.angle = rads * (180 / math.pi)
        self.rect = self.surface.get_rect()

    def drawWall(self):
        pygame.draw.line(self.surface, (255, 255, 255), self.coord_1, self.coord_2, 2)