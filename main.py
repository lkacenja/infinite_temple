import os
import json
import textwrap

import llm

from infinite_temple.schema.room import Room

model_name="qwen2.5:7b"

os.environ['OLLAMA_HOST'] = 'http://localhost:11434'

def ask_for_room():
    model = llm.get_model(model_name)
    prompt = textwrap.dedent("""
        You are creating a flight corridor using line segments that form walls.
        
        Create exactly TWO continuous walls that form a passage:
        - Wall 1: Segments that connect end-to-end to form the left boundary
        - Wall 2: Segments that connect end-to-end to form the right boundary
        
        Rules:
        - Each wall must start at one grid edge and end at another edge
        - Walls must be roughly parallel, creating a corridor at least 50 units wide
        - Each segment's end point (x_2, y_2) must be the start point (x_1, y_1) of the next segment in the same wall
        - Use 10-50 segments per wall (20-100 total)
    """)

    resp = model.prompt(prompt, schema=Room)
    return Room.model_validate(json.loads(resp.text()))


if __name__ == "__main__":
    ask_for_room()