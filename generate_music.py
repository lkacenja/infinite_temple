import os
import textwrap
import time

from openai import OpenAI
from dotenv import load_dotenv

from infinite_temple.schema.audio import AmbientMusic


model_name="gpt-5-nano"

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def create_music_generation_prompt(environment_description: str) -> str:
    """
    Creates a prompt for an LLM to generate ambient music with structured output.

    Args:
        environment_description: A sentence describing the game environment

    Returns:
        A formatted prompt string for the LLM
    """

    prompt = textwrap.dedent(f"""
        You are a procedural music composer generating tonal ambient music for a game environment.

        ENVIRONMENT: {environment_description}
        
        Generate an ambient music piece that captures the mood and atmosphere of this environment. The music MUST be at least 15 seconds long and designed to loop seamlessly back to the beginning.
        
        COMPOSITION REQUIREMENTS:
        1. Create 2-4 different melodic voices that work together harmoniously
        2. Use a consistent key signature that matches the environment's mood
        3. Choose appropriate tempo:
           - Slow (60-80 BPM) for calm/mysterious/dark environments
           - Medium (80-100 BPM) for neutral/contemplative environments  
           - Faster (100-120 BPM) for energetic/bright environments
        4. Layer voices with different rhythmic densities (some sparse, some more active)
        5. **CRITICAL**: The piece MUST be at least 15 seconds long
           - Calculate duration: (60 / BPM) × sum_of_note_durations ≥ 15
           - At 60 BPM: quarter note (4) = 1 second, so need 60+ quarter-note beats
           - At 120 BPM: quarter note (4) = 0.5 seconds, so need 120+ quarter-note beats
        6. **CRITICAL**: End harmonically on the tonic or dominant so the loop sounds natural
           - All voices should resolve to notes in the tonic chord at the end
           - Match the harmonic tension of your opening
        
        NOTE FORMAT:
        - Pitch: 'c4', 'd#5', 'eb3', etc. (note + optional accidental + octave)
          - Notes: a, b, c, d, e, f, g
          - Accidentals: # for sharp, b for flat
          - Octaves: 3 (low bass), 4 (mid), 5 (high), 6 (very high)
          - Rest: 'r'
        - Duration: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth
          - Negative for dotted: -4=dotted quarter, -2=dotted half
        
        MUSICAL GUIDELINES BY ENVIRONMENT TYPE:
        - **Dark/ominous**: Minor keys, lower octaves (3-4), sparse notes, slow tempo (60-75 BPM)
        - **Bright/cheerful**: Major keys, higher octaves (4-5), active rhythms, faster tempo (100-120 BPM)
        - **Mysterious/ethereal**: Modal scales (Dorian, Phrygian), sustained notes, medium tempo (70-85 BPM)
        - **Natural/organic**: Pentatonic scales, flowing rhythms, gentle tempo (75-90 BPM)
        - **Tense/urgent**: Dissonant intervals, driving rhythms, faster tempo (100-120 BPM)
        
        VOICE DESIGN:
        - Voice 1 (Melody): Main melodic line, medium-high octaves (4-5), most active
        - Voice 2 (Bass): Root notes and fifths, low octaves (3-4), sparse and sustained
        - Voice 3 (Harmony): Complementary notes, fills gaps, medium density
        - Voice 4 (Texture): Optional atmospheric layer, very sparse or sustained tones
        
        SEAMLESS LOOPING TECHNIQUE:
        - End all voices on notes that belong to the tonic chord
        - Example in C Major: end on C, E, or G notes
        - Example in A Minor: end on A, C, or E notes
        - The final measure should create anticipation for the return to the beginning
        
        EXAMPLE (Misty Forest - G Major, 75 BPM, ~16 seconds):
        
        {{
          "title": "Misty Forest Ambience",
          "key": "G Major",
          "tempo_bpm": 75,
          "mood": "Peaceful and natural with gentle mystery",
          "duration_seconds": 16.0,
          "voices": [
            {{
              "name": "melody",
              "notes": [
                {{"pitch": "g4", "duration": 2}},
                {{"pitch": "b4", "duration": 4}},
                {{"pitch": "d5", "duration": 4}},
                {{"pitch": "b4", "duration": 2}},
                {{"pitch": "a4", "duration": 2}},
                {{"pitch": "g4", "duration": 4}},
                {{"pitch": "e4", "duration": 4}},
                {{"pitch": "g4", "duration": 2}},
                {{"pitch": "d5", "duration": 4}},
                {{"pitch": "b4", "duration": 4}},
                {{"pitch": "a4", "duration": 4}},
                {{"pitch": "g4", "duration": -2}}
              ]
            }},
            {{
              "name": "bass",
              "notes": [
                {{"pitch": "g3", "duration": 1}},
                {{"pitch": "d3", "duration": 2}},
                {{"pitch": "g3", "duration": 2}},
                {{"pitch": "c3", "duration": 2}},
                {{"pitch": "d3", "duration": 2}},
                {{"pitch": "g3", "duration": 1}}
              ]
            }},
            {{
              "name": "harmony",
              "notes": [
                {{"pitch": "b3", "duration": 2}},
                {{"pitch": "r", "duration": 4}},
                {{"pitch": "d4", "duration": 4}},
                {{"pitch": "r", "duration": 4}},
                {{"pitch": "c4", "duration": 2}},
                {{"pitch": "r", "duration": 4}},
                {{"pitch": "b3", "duration": -2}}
              ]
            }}
          ]
        }}
        
        Now generate the ambient music for the given environment. Return your response as valid JSON matching this structure.
""")

    return prompt


def ask_for_music(seed: str):
    prompt = create_music_generation_prompt(seed)
    print("Generating audio...")
    response = client.responses.parse(
        model=model_name,
        input=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=AmbientMusic
    )
    audio_file = f"audio-{time.time()}.json"
    with open(f"maps/{audio_file}", "w") as f:
        f.write(response.output_parsed.model_dump_json())
    return response.output_parsed


if __name__ == "__main__":
    seed = "A dark and dusty labyrinth of stone passages lead someplace that was once holy."
    ask_for_music(seed)