import math
import random
import pygame


class Vision(pygame.sprite.Sprite):
    def __init__(self, x, y, config):
        pygame.sprite.Sprite.__init__(self)
        self.vision_size = config.player_size * 5
        self.surface = config.surface
        self.x = x
        self.y = y

        self.rect = self.surface.get_rect()

        # Pulsating properties
        self.base_radius = self.vision_size
        self.current_radius = self.base_radius
        self.pulse_time = 0
        self.pulse_speed = 0.1  # Speed of pulsation
        self.pulse_amplitude = 8  # How much the radius changes

        # Explosion timing
        self.lifetime = random.uniform(3.0, 5.0)  # Random 3-5 seconds
        self.age = 0
        self.exploded = False
        self.arc_fragments = []

    def explode(self):
        """Explode the vision into fewer, larger arc segments"""
        self.exploded = True

        # Create 4-6 larger arc fragments
        num_fragments = random.randint(4, 6)

        for i in range(num_fragments):
            # Random starting angle for the arc
            start_angle = random.uniform(0, 2 * math.pi)
            # Larger arcs spanning 60-120 degrees
            arc_length = random.uniform(math.pi / 3, 2 * math.pi / 3)

            # Random velocity direction (outward from center)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4, 9)

            # Larger radius for arc segments (70-100% of base size)
            arc_radius = random.uniform(self.base_radius * 0.7, self.base_radius)

            fragment = {
                'x': self.x,
                'y': self.y,
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'radius': arc_radius,
                'start_angle': start_angle,
                'arc_length': arc_length,
                'rotation_speed': random.uniform(-0.08, 0.08),
                'alpha': 255,  # For fade effect
                'collision_radius': arc_radius  # For collision detection
            }
            self.arc_fragments.append(fragment)

    def updateVision(self, dt=1):
        """Update the vision state

        Args:
            dt: Delta time (usually 1 for frame-based, or actual delta time)
        """
        if not self.exploded:
            # Update age
            self.age += dt * 0.016  # Assuming ~60 FPS, 0.016 seconds per frame

            # Pulsate the circle
            self.pulse_time += self.pulse_speed
            self.current_radius = self.base_radius + math.sin(self.pulse_time) * self.pulse_amplitude

            # Check if it's time to explode
            if self.age >= self.lifetime:
                self.explode()
        else:
            # Update arc fragments
            for frag in self.arc_fragments:
                frag['x'] += frag['vx']
                frag['y'] += frag['vy']

                # Rotate the arc
                frag['start_angle'] += frag['rotation_speed']

                # Apply friction
                frag['vx'] *= 0.98
                frag['vy'] *= 0.98

                # Fade out more slowly since there are fewer pieces
                frag['alpha'] = max(0, frag['alpha'] - 2)

    def drawVision(self):
        """Draw the vision or its fragments"""
        if not self.exploded:
            # Draw pulsating circle
            radius = int(self.current_radius)
            if radius > 0:
                pygame.draw.circle(self.surface, (255, 255, 255),
                                   (int(self.x), int(self.y)), radius, 2)  # Thicker line
        else:
            # Draw arc fragments
            for frag in self.arc_fragments:
                if frag['alpha'] > 0:
                    # Draw arc as connected line segments
                    num_points = 15  # More points for smoother, larger arcs
                    points = []
                    for i in range(num_points + 1):
                        angle = frag['start_angle'] + (frag['arc_length'] * i / num_points)
                        px = frag['x'] + frag['radius'] * math.cos(angle)
                        py = frag['y'] + frag['radius'] * math.sin(angle)
                        points.append((px, py))

                    # Draw connected line segments to form the arc
                    if len(points) > 1:
                        # Calculate color with alpha (fade effect)
                        alpha_ratio = frag['alpha'] / 255
                        color_value = int(255 * alpha_ratio)
                        pygame.draw.lines(self.surface, (color_value, color_value, color_value),
                                          False, points, 2)  # Thicker line width

    def getFragmentPositions(self):
        """Get positions and collision radii of all active fragments

        Returns:
            List of tuples: [(x, y, radius), ...]
        """
        if not self.exploded:
            return [(self.x, self.y, self.current_radius)]

        return [(frag['x'], frag['y'], frag['collision_radius'])
                for frag in self.arc_fragments if frag['alpha'] > 0]

    def isFinished(self):
        """Check if the vision has exploded and all fragments have faded"""
        if not self.exploded:
            return False
        return all(frag['alpha'] <= 0 for frag in self.arc_fragments)