import os

import json
import textwrap
import time

from openai import OpenAI
from dotenv import load_dotenv

from infinite_temple.schema.room import MapSequence

model_name="gpt-5-nano"

load_dotenv()

def ask_for_map():
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    prompt = textwrap.dedent("""
        You are generating a sequence of connected rectangular rooms for a top-down grid-based game.
        
        ## ROOM PROPERTIES
        - Each room is exactly 1000x1000 units.
        - Coordinates range from (0, 0) in the bottom-left to (1000, 1000) in the top-right.
        - The passage in each room connects one ENTRY EDGE to one EXIT EDGE.
        
        ## EDGE DEFINITIONS
        - "top" edge: y = 1000, x ranges from 0 to 1000
        - "bottom" edge: y = 0, x ranges from 0 to 1000
        - "left" edge: x = 0, y ranges from 0 to 1000
        - "right" edge: x = 1000, y ranges from 0 to 1000
        
        ## CONNECTION RULES
        1. The EXIT EDGE of room N must be the ENTRY EDGE of room N+1.
        2. The EXIT POINT of room N must be EXACTLY the same coordinates as the ENTRY POINT of room N+1 (no vertical or horizontal shift; numbers must match exactly).
        3. Do not alter inherited coordinates — copy them exactly.
        4. Passages must be continuous from room to room.
        
        ## PASSAGE CONSTRUCTION RULES
        - Each passage has a centerline between ENTRY POINT and EXIT POINT.
        - Draw two parallel walls on either side of this centerline to form the passage.
        - Passage width: between 50 and 450 units (varied as desired).
        - Each wall consists of 5–10 connected straight segments.
        - The end point (x_2, y_2) of one segment must be the start point (x_1, y_1) of the next segment in the same wall.
        - Segments must stay within the 0–1000 coordinate range.
        - Vary passage shapes: they may be straight, curved, zig-zag, or angled, but must remain continuous and connect entry_point to exit_point exactly.
        - Avoid repeating the same orientation (vertical/horizontal) for two consecutive rooms.
        - Vary the passage width between rooms (between 50 and 450 units).
        
        ## ADDITIONAL OUTPUT RULES
        - N = 15
        - All coordinates must be integers.
        - Each room must follow the rules above.
        - Do not include any text outside the JSON object.
    """)
    response = client.responses.parse(
        model=model_name,
        input=[
            {"role": "system", "content": "You are a game designer creating levels."},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=MapSequence
    )
    map_file = f"map-{time.time()}.json"
    with open(f"maps/{map_file}", "w") as f:
        f.write(response.output_parsed.model_dump_json())
    return response.output_parsed


if __name__ == "__main__":
    ask_for_map()