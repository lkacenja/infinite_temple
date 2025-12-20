import math

from infinite_temple.sprites.player import Player


def wall_collision_test(player, wall):
    """
    Check if a circle (player) intersects with a line segment (wall).
    Returns True if collision detected.
    """
    # Get wall endpoints
    x1, y1 = wall.coord_1.x, wall.coord_1.y
    x2, y2 = wall.coord_2.x, wall.coord_2.y

    # Get player position and radius
    cx, cy = player.x, player.y
    r = player.radius

    # Vector from start to end of wall
    dx = x2 - x1
    dy = y2 - y1

    # Vector from wall start to circle center
    fx = cx - x1
    fy = cy - y1

    # Project circle center onto wall line
    wall_length_sq = dx * dx + dy * dy

    if wall_length_sq == 0:
        # Wall has zero length
        dist_sq = fx * fx + fy * fy
        return dist_sq <= r * r

    # Parameter t tells us where on the line the closest point is
    # t=0 means at start, t=1 means at end
    t = (fx * dx + fy * dy) / wall_length_sq
    t = max(0, min(1, t))  # Clamp to line segment

    # Find closest point on line segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Check distance from circle center to closest point
    dist_x = cx - closest_x
    dist_y = cy - closest_y
    dist_sq = dist_x * dist_x + dist_y * dist_y

    return dist_sq <= r * r


def handle_wall_collision(player, wall):
    """
    Resolve collision between player and wall.
    Pushes player out and reflects velocity.
    """
    if isinstance(player, Player):
        top_speed = abs(max(player.vspeed, player.hspeed))
        damage = (top_speed / 20) * 50
        player.current_health -= damage

    # Get wall vector
    dx = wall.coord_2.x - wall.coord_1.x
    dy = wall.coord_2.y - wall.coord_1.y
    wall_length = math.sqrt(dx * dx + dy * dy)

    if wall_length == 0:
        return

    # Normalize wall vector
    wx = dx / wall_length
    wy = dy / wall_length

    # Wall normal (perpendicular)
    nx = -wy
    ny = wx

    # Find closest point on wall to player
    fx = player.x - wall.coord_1.x
    fy = player.y - wall.coord_1.y
    t = max(0, min(1, (fx * wx + fy * wy) / wall_length))

    closest_x = wall.coord_1.x + t * dx
    closest_y = wall.coord_1.y + t * dy

    # Vector from closest point to player
    to_player_x = player.x - closest_x
    to_player_y = player.y - closest_y
    dist = math.sqrt(to_player_x * to_player_x + to_player_y * to_player_y)

    if dist == 0:
        # Player is exactly on the wall, push along normal
        player.x = closest_x + nx * (player.radius + 2)
        player.y = closest_y + ny * (player.radius + 2)
    else:
        # Normalize direction to player
        to_player_x /= dist
        to_player_y /= dist

        # Push player out to be exactly radius + margin from wall
        player.x = closest_x + to_player_x * (player.radius + 2)
        player.y = closest_y + to_player_y * (player.radius + 2)

        # Make sure normal points toward player
        if (nx * to_player_x + ny * to_player_y) < 0:
            nx = -nx
            ny = -ny

    # Reflect velocity off wall
    # v_new = v - 2 * (v · n) * n
    dot = player.hspeed * nx + player.vspeed * ny
    player.hspeed -= 2 * dot * nx
    player.vspeed -= 2 * dot * ny

    # Apply damping to prevent infinite bouncing
    damping = 0.75
    player.hspeed *= damping
    player.vspeed *= damping



def rubble_collision_test(sprite1, sprite2):
    """
    Calculates distance between two sprites using their x/y attributes
    and checks if that distance is less than the sum of their radii.
    """
    # Calculate the difference in positions
    dx = sprite1.x - sprite2.x
    dy = sprite1.y - sprite2.y

    # Calculate the distance squared (optimization to avoid expensive sqrt)
    dist_sq = dx ** 2 + dy ** 2

    # Calculate the sum of radii squared
    radii_sum = sprite1.radius + sprite2.radius
    radii_sq = radii_sum ** 2

    # Check collision
    return dist_sq < radii_sq


def handle_rubble_collision(player, rubble):
    """
    Resolve collision between player and circular rubble.
    Pushes player out and reflects velocity relative to the rubble's movement.
    """
    # 1. Calculate vector between centers (Rubble -> Player)
    dx = player.x - rubble.x
    dy = player.y - rubble.y
    dist = math.sqrt(dx * dx + dy * dy)

    if dist == 0:
        return  # Prevent division by zero if they spawn on exact same pixel

    # Normalize the normal vector (points A->B)
    nx = dx / dist
    ny = dy / dist

    # 2. Calculate Relative Velocity
    # This is crucial because the rubble is also moving.
    # We want the bounce to act as if the rubble were stationary and the player hit it harder/softer.
    rel_vx = player.hspeed - rubble.hspeed
    rel_vy = player.vspeed - rubble.vspeed

    # Calculate impact speed for damage
    impact_speed = math.sqrt(rel_vx ** 2 + rel_vy ** 2)

    # 3. Apply Damage
    if isinstance(player, Player):
        # Using similar scaling to your wall logic
        damage = (impact_speed / 20) * 50
        player.current_health -= damage

    # 4. Positional Correction (Push player out)
    # We want them to be touching, not overlapping
    min_dist = player.radius + rubble.radius + 2  # +2 margin for safety
    overlap = min_dist - dist

    if overlap > 0:
        player.x += nx * overlap
        player.y += ny * overlap
        # Update rect immediately so drawing is smooth
        player.rect.centerx = int(player.x)
        player.rect.centery = int(player.y)

    # 5. Reflect Velocity (Bounce)
    # v_new = v - 2 * (v · n) * n
    # We calculate the dot product of the RELATIVE velocity and the normal
    dot = rel_vx * nx + rel_vy * ny

    # Only bounce if they are moving towards each other (dot < 0)
    if dot < 0:
        # Reflect the relative velocity
        rel_vx -= 2 * dot * nx
        rel_vy -= 2 * dot * ny

        # Apply damping (loss of energy)
        damping = 0.75
        rel_vx *= damping
        rel_vy *= damping

        # Apply the new relative velocity back to the player
        # Player V = Rubble V + New Relative V
        player.hspeed = rubble.hspeed + rel_vx
        player.vspeed = rubble.vspeed + rel_vy

