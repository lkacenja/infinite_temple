import math
import random

import pygame


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, config):
        pygame.sprite.Sprite.__init__(self)
        self.player_size = config.player_size
        self.surface = config.surface
        self.x = x
        self.y = y

        self.hspeed = 0
        self.vspeed = 0
        self.dir = 0
        self.rtspd = 0
        self.thrust = False
        self.braking = False
        self.rect = self.surface.get_rect()
        self.radius = self.player_size * 0.85

        self.exploded = False
        self.fragments = []

        self.max_health = 100
        self.current_health = self.max_health
        self.shield = 0
        self.ammo = 0
        self.shield_pulse_timer = 0

        self.player_max_speed = 20
        self.fd_fric = 0.75
        self.bd_fric = 0.1

    def blowUp(self):
        """Explode the ship into flying fragments"""
        self.exploded = True
        a = math.radians(self.dir)
        x = self.x
        y = self.y
        s = self.player_size

        # Define ship line segments as (x1, y1, x2, y2)
        segments = [
            # Left wing
            (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) + a),
             y - (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) + a),
             x + s * math.cos(a),
             y + s * math.sin(a)),

            # Right wing
            (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) - a),
             y + (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) - a),
             x + s * math.cos(a),
             y + s * math.sin(a)),

            # Back connector
            (x - (s * math.sqrt(2) / 2) * math.cos(a + math.pi / 4),
             y - (s * math.sqrt(2) / 2) * math.sin(a + math.pi / 4),
             x - (s * math.sqrt(2) / 2) * math.cos(-a + math.pi / 4),
             y + (s * math.sqrt(2) / 2) * math.sin(-a + math.pi / 4)),
        ]

        # Create fragments - each segment flies in a random direction
        for seg in segments:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4, 10)
            fragment = {
                'x1': seg[0], 'y1': seg[1],
                'x2': seg[2], 'y2': seg[3],
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'rotation': random.uniform(-0.15, 0.15)
            }
            self.fragments.append(fragment)

    def updatePlayer(self):
        if self.current_health <= 0:
            if not self.exploded:
                self.blowUp()
            # Update fragment positions - just move them in their direction
            for frag in self.fragments:
                # Move both endpoints
                frag['x1'] += frag['vx']
                frag['y1'] += frag['vy']
                frag['x2'] += frag['vx']
                frag['y2'] += frag['vy']

                # Optional: rotate the fragment as it flies
                cx = (frag['x1'] + frag['x2']) / 2
                cy = (frag['y1'] + frag['y2']) / 2
                dx1 = frag['x1'] - cx
                dy1 = frag['y1'] - cy
                dx2 = frag['x2'] - cx
                dy2 = frag['y2'] - cy

                cos_r = math.cos(frag['rotation'])
                sin_r = math.sin(frag['rotation'])

                frag['x1'] = cx + dx1 * cos_r - dy1 * sin_r
                frag['y1'] = cy + dx1 * sin_r + dy1 * cos_r
                frag['x2'] = cx + dx2 * cos_r - dy2 * sin_r
                frag['y2'] = cy + dx2 * sin_r + dy2 * cos_r

                # Apply friction
                frag['vx'] *= 0.98
                frag['vy'] *= 0.98
            return

        # Normal movement code
        speed = math.sqrt(self.hspeed ** 2 + self.vspeed ** 2)
        if self.thrust:
            if speed + self.fd_fric < self.player_max_speed:
                self.hspeed += self.fd_fric * math.cos(self.dir * math.pi / 180)
                self.vspeed += self.fd_fric * math.sin(self.dir * math.pi / 180)
            else:
                self.hspeed = self.player_max_speed * math.cos(self.dir * math.pi / 180)
                self.vspeed = self.player_max_speed * math.sin(self.dir * math.pi / 180)
        else:
            if speed - self.bd_fric > 0:
                change_in_hspeed = (self.bd_fric * math.cos(self.vspeed / self.hspeed))
                change_in_vspeed = (self.bd_fric * math.sin(self.vspeed / self.hspeed))
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

        brake_power = 0.85
        if self.braking and not self.thrust:
            self.hspeed *= brake_power
            self.vspeed *= brake_power

        # Rotate player
        self.dir += self.rtspd

        # Update shield pulse animation
        self.shield_pulse_timer += 0.1
        if self.shield_pulse_timer >= 2 * math.pi:
            self.shield_pulse_timer -= 2 * math.pi

    def drawPlayer(self):
        if self.current_health <= 0:
            # Draw fragments
            for frag in self.fragments:
                pygame.draw.line(self.surface, (255, 255, 255),
                                 (frag['x1'], frag['y1']),
                                 (frag['x2'], frag['y2']))
            return

        # Normal drawing code
        a = math.radians(self.dir)
        x = self.x
        y = self.y
        s = self.player_size
        t = self.thrust

        pygame.draw.line(self.surface, (255, 255, 255),
                         (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) + a),
                          y - (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) + a)),
                         (x + s * math.cos(a), y + s * math.sin(a)))

        pygame.draw.line(self.surface, (255, 255, 255),
                         (x - (s * math.sqrt(130) / 12) * math.cos(math.atan(7 / 9) - a),
                          y + (s * math.sqrt(130) / 12) * math.sin(math.atan(7 / 9) - a)),
                         (x + s * math.cos(a), y + s * math.sin(a)))

        pygame.draw.line(self.surface, (255, 255, 255),
                         (x - (s * math.sqrt(2) / 2) * math.cos(a + math.pi / 4),
                          y - (s * math.sqrt(2) / 2) * math.sin(a + math.pi / 4)),
                         (x - (s * math.sqrt(2) / 2) * math.cos(-a + math.pi / 4),
                          y + (s * math.sqrt(2) / 2) * math.sin(-a + math.pi / 4)))
        if t:
            pygame.draw.line(self.surface, (255, 255, 255),
                             (x - s * math.cos(a),
                              y - s * math.sin(a)),
                             (x - (s * math.sqrt(5) / 4) * math.cos(a + math.pi / 6),
                              y - (s * math.sqrt(5) / 4) * math.sin(a + math.pi / 6)))
            pygame.draw.line(self.surface, (255, 255, 255),
                             (x - s * math.cos(-a),
                              y + s * math.sin(-a)),
                             (x - (s * math.sqrt(5) / 4) * math.cos(-a + math.pi / 6),
                              y + (s * math.sqrt(5) / 4) * math.sin(-a + math.pi / 6)))

        # Draw shield if active
        if self.shield > 0:
            self._draw_shield()

    def _draw_shield(self):
        """Draw pulsing concentric rings around player when shield is active."""
        pulse = 1 + 0.15 * math.sin(self.shield_pulse_timer)
        base_radius = self.player_size * 1.5
        num_segments = 16

        for i in range(self.shield):
            ring_radius = base_radius * pulse + (i * 8)
            points = []
            for j in range(num_segments):
                angle = (2 * math.pi / num_segments) * j
                px = self.x + ring_radius * math.cos(angle)
                py = self.y + ring_radius * math.sin(angle)
                points.append((px, py))

            for j in range(num_segments):
                start = points[j]
                end = points[(j + 1) % num_segments]
                pygame.draw.line(self.surface, (255, 255, 255), start, end)

    def fire_bullet(self):
        """
        Attempt to fire a bullet in the direction player is facing.

        Returns:
            Tuple of (target_x, target_y) if ammo available, None otherwise
        """
        if self.ammo <= 0:
            return None

        self.ammo -= 1

        # Calculate target point far in the direction player is facing
        distance = 1000
        target_x = self.x + distance * math.cos(math.radians(self.dir))
        target_y = self.y + distance * math.sin(math.radians(self.dir))

        return (target_x, target_y)