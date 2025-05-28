import os
import json

import llm

from infinite_temple.schema.base import GridDrawing

model_name="deepseek-r1"

os.environ['OLLAMA_HOST'] = 'http://localhost:11434'

def ask_for_point():
    model = llm.get_model(model_name)
    resp = model.prompt("You are a game asset generator. Given a 10x10 grid, generate a drawing of a space ship using BETWEEN 10 AND 50 POINTS. Each point has an x and y coordinate. Each point may also be an engine ('e'), weapon ('w') or hull ('h'). A ship may have no more than two engines and no more than one weapon.", schema=GridDrawing)
    p = GridDrawing.model_validate(json.loads(resp.text()))
    print(p)


if __name__ == "__main__":
    ask_for_point()