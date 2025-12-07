import os

import json
import textwrap
import time
import random

from openai import OpenAI
from dotenv import load_dotenv

from infinite_temple.schema.room import RoomSequence

model_name="gpt-5-nano"

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def ask_for_map():
    prompt = textwrap.dedent("""
        # Temple Room Sequence Generation Prompt
        
        You are generating a sequence of 15 connected rooms for an infinitely extending temple exploration game. Each room is a corridor segment that must connect properly to the previous and next rooms.
        
        ## CRITICAL CONNECTION RULE
        
        When a player exits one room, they wrap to the opposite edge and enter the next room from that side.
        
        **Examples:**
        - Room exits RIGHT (x=1000) → Player wraps to x=0 → Next room must ENTER from LEFT
        - Room exits LEFT (x=0) → Player wraps to x=1000 → Next room must ENTER from RIGHT  
        - Room exits BOTTOM (y=1000) → Player wraps to y=0 → Next room must ENTER from TOP
        - Room exits TOP (y=0) → Player wraps to y=1000 → Next room must ENTER from BOTTOM
        
        ## Available Room Types
        
        You have eleven corridor templates to choose from:
        
        1. **start** - Starting room with a 400x400 square in the center and a horizontal corridor exiting RIGHT (ALWAYS use this as the first room)
        2. **horizontal** - Straight corridor entering LEFT, exiting RIGHT (or entering RIGHT, exiting LEFT - it's bidirectional)
        3. **vertical** - Straight corridor entering TOP, exiting BOTTOM (or entering BOTTOM, exiting TOP - it's bidirectional)
        4. **elbow_top_left** - L-shaped corridor entering from TOP, exiting LEFT
        5. **elbow_top_right** - L-shaped corridor entering from TOP, exiting RIGHT
        6. **elbow_bottom_left** - L-shaped corridor entering from BOTTOM, exiting LEFT
        7. **elbow_bottom_right** - L-shaped corridor entering from BOTTOM, exiting RIGHT
        8. **elbow_left_top** - L-shaped corridor entering from LEFT, exiting TOP
        9. **elbow_left_bottom** - L-shaped corridor entering from LEFT, exiting BOTTOM
        10. **elbow_right_top** - L-shaped corridor entering from RIGHT, exiting TOP
        11. **elbow_right_bottom** - L-shaped corridor entering from RIGHT, exiting BOTTOM
        
        ## Connection Rules
        
        **When previous room exits RIGHT → next room must ENTER from LEFT:**
        - Valid next rooms: horizontal, elbow_left_top, elbow_left_bottom
        
        **When previous room exits LEFT → next room must ENTER from RIGHT:**
        - Valid next rooms: horizontal, elbow_right_top, elbow_right_bottom
        
        **When previous room exits BOTTOM → next room must ENTER from TOP:**
        - Valid next rooms: vertical, elbow_top_left, elbow_top_right
        
        **When previous room exits TOP → next room must ENTER from BOTTOM:**
        - Valid next rooms: vertical, elbow_bottom_left, elbow_bottom_right
        
        ## Valid Connections Chart
        
        | Previous Room Exits | Next Room Must Enter From | Valid Next Rooms |
        |---------------------|---------------------------|------------------|
        | RIGHT | LEFT (wraps x=1000→0) | horizontal, elbow_left_top, elbow_left_bottom |
        | LEFT | RIGHT (wraps x=0→1000) | horizontal, elbow_right_top, elbow_right_bottom |
        | BOTTOM | TOP (wraps y=1000→0) | vertical, elbow_top_left, elbow_top_right |
        | TOP | BOTTOM (wraps y=0→1000) | vertical, elbow_bottom_left, elbow_bottom_right |
        
        ## Requirements
        
        1. Generate exactly 25 rooms (including the starting room)
        2. **ALWAYS start with the "start" room as room #1** - this is mandatory
        3. Each subsequent room must connect properly based on the wrapping rule above
        4. The "start" room exits RIGHT, so room #2 must ENTER from LEFT (horizontal, elbow_left_top, or elbow_left_bottom)
        5. Use a variety of room types - avoid long sequences of the same type
        6. Create an interesting, winding path through the temple
        7. Ensure the final room can theoretically connect to additional rooms (don't dead-end impossibly)
        
        **VALIDATION: Before finalizing your sequence, trace through each connection:**
        - For each room, identify which edge it exits from
        - The next room must enter from the OPPOSITE edge (due to wrapping)
        - Check your chart to ensure the next room type is valid
        
        ## Output Format
        
        Return a JSON object with this structure:
        
        ```json
        {
          "rooms": ["horizontal", "elbow_top_right", "vertical", "elbow_bottom_left", ...]
        }
        ```
        
        Just a simple array of room template names. Valid names are:
        - `"start"` (MUST be the first room)
        - `"horizontal"`
        - `"vertical"`
        - `"elbow_top_left"`
        - `"elbow_top_right"`
        - `"elbow_bottom_left"`
        - `"elbow_bottom_right"`
        - `"elbow_left_top"`
        - `"elbow_left_bottom"`
        - `"elbow_right_top"`
        - `"elbow_right_bottom"`
        
        ## Example Valid Sequence (first 5 rooms)
        
        ```json
        {
          "rooms": ["start", "horizontal", "elbow_left_bottom", "vertical", "elbow_top_right"]
        }
        ```
        
        **Explanation of connections:**
        1. `start` exits RIGHT
        2. `horizontal` ENTERS from LEFT (✓ wraps from RIGHT), exits RIGHT
        3. `elbow_left_bottom` ENTERS from LEFT (✓ wraps from RIGHT), exits BOTTOM
        4. `vertical` ENTERS from TOP (✓ wraps from BOTTOM), exits BOTTOM
        5. `elbow_top_right` ENTERS from TOP (✓ wraps from BOTTOM), exits RIGHT
        
        Generate your 15-room temple sequence now, ensuring all connections are valid and the path creates an interesting exploration experience.
    """)
    print("Generating room sequence...")
    response = client.responses.parse(
        model=model_name,
        input=[
            {"role": "system", "content": "You are a game designer creating levels."},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=RoomSequence
    )
    response.output_parsed.rooms = insert_antechambers(response.output_parsed.rooms)
    map_file = f"map-{time.time()}.json"
    with open(f"maps/{map_file}", "w") as f:
        f.write(response.output_parsed.model_dump_json())
    return response.output_parsed


def insert_antechambers(room_list, map_size=1000):
    print(room_list)
    """
    Insert antechambers randomly into a room sequence.

    Args:
        room_list: List of room template names
        map_size: Size of the map (default 1000)

    Returns:
        New list with antechambers inserted
    """
    # Exit directions for each room type
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

    # Calculate how many antechambers to add
    target_antechambers = len(room_list) // 10

    if target_antechambers == 0:
        return room_list.copy()

    # Create a copy to modify
    new_rooms = room_list.copy()

    # Generate valid positions (not position 0, and ensure spacing)
    # Valid positions are 1 to len-1 initially
    valid_positions = list(range(1, len(new_rooms)))

    inserted_count = 0
    attempts = 0
    max_attempts = target_antechambers * 10  # Prevent infinite loop

    while inserted_count < target_antechambers and attempts < max_attempts:
        attempts += 1

        if not valid_positions:
            break

        # Pick a random position
        pos = random.choice(valid_positions)

        # Check if previous room is an antechamber (no back-to-back)
        if pos > 0 and "antechamber" in new_rooms[pos - 1]:
            valid_positions.remove(pos)
            continue

        # Check if next room is an antechamber (no back-to-back)
        if pos < len(new_rooms) and "antechamber" in new_rooms[pos]:
            valid_positions.remove(pos)
            continue

        # Determine which antechamber type based on previous room's exit
        previous_room = new_rooms[pos - 1]
        exit_dir = exit_directions.get(previous_room)

        if exit_dir in ["TOP", "BOTTOM"]:
            antechamber_type = "antechamber_vertical"
        elif exit_dir in ["LEFT", "RIGHT"]:
            antechamber_type = "antechamber_horizontal"
        else:
            # Unknown room type, skip
            valid_positions.remove(pos)
            continue

        # Insert the antechamber
        new_rooms.insert(pos, antechamber_type)
        inserted_count += 1

        # Remove this position and adjacent positions from valid list
        # Adjust positions after insertion (everything shifts right by 1)
        valid_positions = [p + 1 if p >= pos else p for p in valid_positions]
        valid_positions = [p for p in valid_positions if p not in [pos, pos + 1]]

    return new_rooms

if __name__ == "__main__":
    ask_for_map()