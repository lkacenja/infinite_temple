"""
Room sequence manipulation utilities.

Functions for inserting antechambers and branching paths into generated room sequences.
"""

import random
from typing import List, Optional


def insert_antechambers(room_list: List[str], map_size: int = 1000) -> List[str]:
    """
    Insert antechambers randomly into a room sequence.

    Args:
        room_list: List of room template names
        map_size: Size of the map (default 1000)

    Returns:
        New list with antechambers inserted
    """
    exit_directions = {
        "start": "RIGHT",
        "horizontal": "RIGHT",
        "vertical": "BOTTOM",
        "elbow_top_left": "LEFT",
        "elbow_top_right": "RIGHT",
        "elbow_bottom_left": "LEFT",
        "elbow_bottom_right": "RIGHT",
        "elbow_left_top": "TOP",
        "elbow_left_bottom": "BOTTOM",
        "elbow_right_top": "TOP",
        "elbow_right_bottom": "BOTTOM",
        "antechamber_vertical": "BOTTOM",
        "antechamber_horizontal": "RIGHT"
    }

    target_antechambers = len(room_list) // 10

    if target_antechambers == 0:
        return room_list.copy()

    new_rooms = room_list.copy()
    valid_positions = list(range(1, len(new_rooms)))

    inserted_count = 0
    attempts = 0
    max_attempts = target_antechambers * 10

    while inserted_count < target_antechambers and attempts < max_attempts:
        attempts += 1

        if not valid_positions:
            break

        pos = random.choice(valid_positions)

        if pos > 0 and "antechamber" in new_rooms[pos - 1]:
            valid_positions.remove(pos)
            continue

        if pos < len(new_rooms) and "antechamber" in new_rooms[pos]:
            valid_positions.remove(pos)
            continue

        previous_room = new_rooms[pos - 1]
        exit_dir = exit_directions.get(previous_room)

        if exit_dir in ["TOP", "BOTTOM"]:
            antechamber_type = "antechamber_vertical"
        elif exit_dir in ["LEFT", "RIGHT"]:
            antechamber_type = "antechamber_horizontal"
        else:
            valid_positions.remove(pos)
            continue

        new_rooms.insert(pos, antechamber_type)
        inserted_count += 1

        valid_positions = [p + 1 if p >= pos else p for p in valid_positions]
        valid_positions = [p for p in valid_positions if p not in [pos, pos + 1]]

    return new_rooms


def calculate_corridor_direction(room_list: List[str], room_index: int) -> tuple:
    """
    Determine which direction a corridor is being traversed in the main path.

    Args:
        room_list: List of room template names
        room_index: Index of the corridor to analyze

    Returns:
        Tuple of (entry_dir, exit_dir) as strings like 'north', 'south', 'east', 'west'
    """
    exit_directions = {
        "start": "east",
        "horizontal": None,
        "vertical": None,
        "elbow_top_left": "west",
        "elbow_top_right": "east",
        "elbow_bottom_left": "west",
        "elbow_bottom_right": "east",
        "elbow_left_top": "north",
        "elbow_left_bottom": "south",
        "elbow_right_top": "north",
        "elbow_right_bottom": "south",
        "antechamber_vertical": None,
        "antechamber_horizontal": None,
    }

    opposite = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }

    if room_index == 0:
        entry_dir = None
        exit_dir = "east"
        return (entry_dir, exit_dir)

    prev_entry, prev_exit = calculate_corridor_direction(room_list, room_index - 1) if room_index > 0 else (None, None)

    entry_dir = opposite[prev_exit]

    current_room = room_list[room_index]
    fixed_exit = exit_directions.get(current_room)

    if fixed_exit is not None:
        exit_dir = fixed_exit
    else:
        exit_dir = opposite[entry_dir]

    return (entry_dir, exit_dir)


def generate_branch_sequence(length: int, start_portal: str) -> List[str]:
    """
    Generate a valid room sequence for a branch following the wrapping rule.

    Args:
        length: Number of rooms in the branch
        start_portal: Direction the branch goes from junction (north/south/east/west)

    Returns:
        List of room template names
    """
    opposite = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }

    can_enter_from = {
        "west": ["horizontal", "elbow_left_top", "elbow_left_bottom", "antechamber_horizontal"],
        "east": ["horizontal", "elbow_right_top", "elbow_right_bottom", "antechamber_horizontal"],
        "north": ["vertical", "elbow_top_left", "elbow_top_right", "antechamber_vertical"],
        "south": ["vertical", "elbow_bottom_left", "elbow_bottom_right", "antechamber_vertical"]
    }

    room_exits = {
        "horizontal": None,
        "vertical": None,
        "elbow_top_left": "west",
        "elbow_top_right": "east",
        "elbow_bottom_left": "west",
        "elbow_bottom_right": "east",
        "elbow_left_top": "north",
        "elbow_left_bottom": "south",
        "elbow_right_top": "north",
        "elbow_right_bottom": "south",
        "antechamber_vertical": None,
        "antechamber_horizontal": None,
    }

    current_entrance = opposite[start_portal]
    branch_rooms = []

    for i in range(length):
        available_rooms = can_enter_from[current_entrance]
        next_room = random.choice(available_rooms)
        branch_rooms.append(next_room)

        fixed_exit = room_exits[next_room]
        if fixed_exit is not None:
            exit_dir = fixed_exit
        else:
            exit_dir = opposite[current_entrance]

        current_entrance = opposite[exit_dir]

    return branch_rooms


def get_branch_exit_direction(branch_rooms: List[str], start_portal: str) -> str:
    """
    Compute the exit direction of the last room in a branch sequence.

    Args:
        branch_rooms: List of room template names
        start_portal: Direction the branch goes from junction (north/south/east/west)

    Returns:
        Exit direction of the last room (north/south/east/west)
    """
    opposite = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }

    room_exits = {
        "horizontal": None,
        "vertical": None,
        "elbow_top_left": "west",
        "elbow_top_right": "east",
        "elbow_bottom_left": "west",
        "elbow_bottom_right": "east",
        "elbow_left_top": "north",
        "elbow_left_bottom": "south",
        "elbow_right_top": "north",
        "elbow_right_bottom": "south",
        "antechamber_vertical": None,
        "antechamber_horizontal": None,
    }

    current_entrance = opposite[start_portal]
    exit_dir = None

    for room in branch_rooms:
        fixed_exit = room_exits.get(room)
        if fixed_exit is not None:
            exit_dir = fixed_exit
        else:
            exit_dir = opposite[current_entrance]
        current_entrance = opposite[exit_dir]

    return exit_dir


def insert_forks(room_list: List[str], narrative_context=None) -> list:
    """
    Insert branching paths into a room sequence.

    Modifies room_list in place - replaces corridors with T-junctions at fork points.

    Args:
        room_list: List of room template names (main path) - MODIFIED IN PLACE
        narrative_context: Optional TempleNarrative for density control

    Returns:
        List[BranchPath] objects
    """
    from infinite_temple.schema.room import BranchPath

    if narrative_context:
        atmosphere = narrative_context.atmosphere.lower()
        if any(word in atmosphere for word in ["labyrinth", "maze", "complex", "winding", "twisted"]):
            fork_density = 0.10
        elif any(word in atmosphere for word in ["linear", "straight", "simple", "direct"]):
            fork_density = 0.03
        else:
            fork_density = 0.05
    else:
        fork_density = 0.05

    fork_count = max(2, int(len(room_list) * fork_density))

    valid_room_types = ["horizontal"]
    valid_positions = [
        i for i in range(10, len(room_list) - 10)
        if room_list[i] in valid_room_types
    ]

    fork_positions = []
    for _ in range(fork_count):
        if not valid_positions:
            break

        pos = random.choice(valid_positions)
        fork_positions.append(pos)

        valid_positions = [p for p in valid_positions if abs(p - pos) > 8]

    branch_paths = []

    for fork_pos in sorted(fork_positions):
        entry_dir, exit_dir = calculate_corridor_direction(room_list, fork_pos)

        if entry_dir in ["west", "east"] and exit_dir in ["west", "east"]:
            branch_portal = random.choice(["north", "south"])
        else:
            continue

        if branch_portal == "north":
            room_list[fork_pos] = "tjunction_horizontal_north"
        else:
            room_list[fork_pos] = "tjunction_horizontal_south"

        branch_type = "dead_end" if random.random() < 0.7 else "rejoin"

        if branch_type == "dead_end":
            branch_length = random.randint(3, 5)
        else:
            branch_length = random.randint(5, 15)

        branch_rooms = generate_branch_sequence(branch_length, branch_portal)

        if branch_type == "rejoin":
            min_rejoin = fork_pos + 10
            max_rejoin = min(fork_pos + 25, len(room_list) - 5)

            valid_rejoin_positions = [
                i for i in range(min_rejoin, max_rejoin)
                if room_list[i] in valid_room_types and i not in fork_positions
            ]

            branch_exit = get_branch_exit_direction(branch_rooms, branch_portal)
            opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}

            compatible_rejoin_positions = []
            for rejoin_pos in valid_rejoin_positions:
                rejoin_entry, rejoin_exit = calculate_corridor_direction(room_list, rejoin_pos)

                if rejoin_entry in ["west", "east"] and rejoin_exit in ["west", "east"]:
                    possible_portals = ["north", "south"]
                elif rejoin_entry in ["north", "south"] and rejoin_exit in ["north", "south"]:
                    possible_portals = ["east", "west"]
                else:
                    continue

                for portal in possible_portals:
                    required_exit = opposite[portal]
                    if branch_exit == required_exit:
                        compatible_rejoin_positions.append((rejoin_pos, portal))

            if compatible_rejoin_positions:
                rejoin_pos, rejoin_portal = random.choice(compatible_rejoin_positions)
                branch = BranchPath(
                    fork_main_room_index=fork_pos,
                    fork_portal=branch_portal,
                    branch_rooms=branch_rooms,
                    rejoin_main_room_index=rejoin_pos,
                    rejoin_portal=rejoin_portal
                )
            else:
                branch_type = "dead_end"

        if branch_type == "dead_end":
            branch_rooms.append("dead_end")
            branch = BranchPath(
                fork_main_room_index=fork_pos,
                fork_portal=branch_portal,
                branch_rooms=branch_rooms,
                rejoin_main_room_index=None,
                rejoin_portal=None
            )

        branch_paths.append(branch)

    return branch_paths
