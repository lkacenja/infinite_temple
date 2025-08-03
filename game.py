import sys
import time
import math
from typing import List

import pygame
from pygame.locals import *

from main import ask_for_room

white = (255, 255, 255)
red = (255, 0, 0)
black = (0, 0, 0)

display_width = 1000
display_height = 1000

player_size = 10
fd_fric = 0.75
bd_fric = 0.1
player_max_speed = 20
player_max_rtspd = 10
bullet_speed = 15

vec = pygame.math.Vector2

pygame.init()

surface = pygame.display.set_mode((display_width, display_height))

class Timer:
    def __init__(self, frequency: int, callback: callable):
        self.start = time.time()
        self.frequency = frequency
        self.callback = callback

    def tick(self):
        now = time.time()
        if now - self.start > self.frequency:
            self.callback()
            self.start = now


class Wall(pygame.sprite.Sprite):
    def __init__(self, coord_1: vec, coord_2: vec):
        pygame.sprite.Sprite.__init__(self)

        self.coord_1 = coord_1
        self.coord_2 = coord_2
        rads = math.atan2(self.coord_2.y - self.coord_1.y, self.coord_2.x - self.coord_1.x)
        self.angle = rads * (180 / math.pi)



        self.rect = surface.get_rect()

    def drawWall(self):
        pygame.draw.line(surface, white, self.coord_1, self.coord_2, 2)
            


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.hspeed = 0
        self.vspeed = 0
        self.dir = -90
        self.rtspd = 0
        self.thrust = False
        self.rect = surface.get_rect()

    def updatePlayer(self):
        # Move player
        speed = math.sqrt(self.hspeed**2 + self.vspeed**2)
        if self.thrust:
            if speed + fd_fric < player_max_speed:
                self.hspeed += fd_fric * math.cos(self.dir * math.pi / 180)
                self.vspeed += fd_fric * math.sin(self.dir * math.pi / 180)
            else:
                self.hspeed = player_max_speed * math.cos(self.dir * math.pi / 180)
                self.vspeed = player_max_speed * math.sin(self.dir * math.pi / 180)
        else:
            if speed - bd_fric > 0:
                change_in_hspeed = (bd_fric * math.cos(self.vspeed / self.hspeed))
                change_in_vspeed = (bd_fric * math.sin(self.vspeed / self.hspeed))
                if self.hspeed != 0:
                    if change_in_hspeed / abs(change_in_hspeed) == self.hspeed / abs(self.hspeed):
                        self.hspeed -= change_in_hspeed
                    else:
                        self.hspeed += change_in_hspeed
                if self.vspeed != 0:
                    if change_in_vspeed / abs(change_in_vspeed) == self.vspeed / abs(self.vspeed):
                        self.vspeed -= change_in_vspeed
                    else:
                        self.vspeed += change_in_vspeed
            else:
                self.hspeed = 0
                self.vspeed = 0
        self.x += self.hspeed
        self.y += self.vspeed

        # Check for wrapping
        if self.x > display_width:
            self.x = 0
        elif self.x < 0:
            self.x = display_width
        elif self.y > display_height:
            self.y = 0
        elif self.y < 0:
            self.y = display_height

        # Rotate player
        self.dir += self.rtspd

    def drawPlayer(self):
        a = math.radians(self.dir)
        x = self.x
        y = self.y
        s = player_size
        t = self.thrust
        # Draw player
        pygame.draw.line(surface, white,
                         (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) + a),
                          y - (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) + a)),
                         (x + s * math.cos(a), y + s * math.sin(a)))

        pygame.draw.line(surface, white,
                         (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) - a),
                          y + (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) - a)),
                         (x + s * math.cos(a), y + s * math.sin(a)))

        pygame.draw.line(surface, white,
                         (x - (s * math.sqrt(2) / 2) * math.cos(a + math.pi / 4),
                          y - (s * math.sqrt(2) / 2) * math.sin(a + math.pi / 4)),
                         (x - (s * math.sqrt(2) / 2) * math.cos(-a + math.pi / 4),
                          y + (s * math.sqrt(2) / 2) * math.sin(-a + math.pi / 4)))
        if t:
            pygame.draw.line(surface, white,
                             (x - s * math.cos(a),
                              y - s * math.sin(a)),
                             (x - (s * math.sqrt(5) / 4) * math.cos(a + math.pi / 6),
                              y - (s * math.sqrt(5) / 4) * math.sin(a + math.pi / 6)))
            pygame.draw.line(surface, white,
                             (x - s * math.cos(-a),
                              y + s * math.sin(-a)),
                             (x - (s * math.sqrt(5) / 4) * math.cos(-a + math.pi / 6),
                              y + (s * math.sqrt(5) / 4) * math.sin(-a + math.pi / 6)))



P1 = Player(200, 200)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)

walls_sprites = pygame.sprite.Group()

print("Generating room....")
room = ask_for_room()
print("Generation complete")

print(room)

for segment in room.walls:
    walls_sprites.add(Wall(vec(segment.x_1, segment.y_1), vec(segment.x_2, segment.y_2)))
#test = Wall(vec(100, 100), vec(200, 150))





FramePerSec = pygame.time.Clock()

pygame.display.set_caption("INFINITE TEMPLE: Movement Test")

def collision_test(player, wall):
    length = math.sqrt((wall.coord_1.x - wall.coord_2.x) ** 2 + (wall.coord_1.y - wall.coord_2.y) ** 2)
    player_seg_0 = math.sqrt((player.x - wall.coord_1.x) ** 2 + (player.y - wall.coord_1.y) ** 2)
    player_seg_1 = math.sqrt((player.x - wall.coord_2.x) ** 2 + (player.y - wall.coord_2.y) ** 2)
    buffer = 1
    if length - buffer <= player_seg_0 + player_seg_1 <= length + buffer:
        return True
    return False

while True:
    surface.fill((0, 0, 0))
    P1.updatePlayer()
    P1.drawPlayer()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                P1.thrust = True
            if event.key == pygame.K_LEFT:
                P1.rtspd = -player_max_rtspd
            if event.key == pygame.K_RIGHT:
                P1.rtspd = player_max_rtspd
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                P1.thrust = False
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                P1.rtspd = 0
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    for wall in walls_sprites:
        wall.drawWall()

    colliding = pygame.sprite.spritecollide(P1, walls_sprites, False, collision_test)
    if len(colliding) > 0:
        P1.dir = colliding[0].angle + 90
        P1.hspeed *= -1
        P1.vspeed *= -1
        #colliding[0]
    # for entity in all_sprites:
    #     if hasattr(entity, 'move'):
    #         entity.move()
    #     if hasattr(entity, 'update'):
    #         entity.update()
    #     surface.blit(entity.surf, entity.rect)
    pygame.display.update()
    FramePerSec.tick(30)