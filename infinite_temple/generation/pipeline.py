"""
Temple generation pipeline.

Orchestrates generation of all temple assets:
1. Narrative from seed words (blocking - required for all other steps)
2. Parallel generation of:
   - Room layout from narrative
   - Ambient music from narrative
   - Title screen SVG from narrative
   - Game over SVG from narrative
"""

import os
import json
import time
import textwrap
import threading
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from tenacity import retry, stop_after_attempt, retry_if_exception_type

from openai import OpenAI
from dotenv import load_dotenv

from infinite_temple.schema.temple import TempleConfiguration, TempleNarrative
from infinite_temple.schema.room import RoomSequence
from infinite_temple.schema.audio import AmbientMusic
from infinite_temple.generation.narrative import generate_narrative
from infinite_temple.generation.svg_generator import generate_title_svg, generate_gameover_svg
from infinite_temple.persistence.temple_repository import TempleRepository


# Default model
DEFAULT_MODEL = "gpt-5"

# Load environment variables
load_dotenv()


class TempleGenerationPipeline:
    """
    Orchestrates temple generation workflow with progress tracking.

    Generates all assets for a playable temple from three seed words:
    - Narrative (title, backstory, atmosphere, visual theme)
    - Room layout (sequence of connected rooms)
    - Ambient music (tonal composition)
    - Title screen SVG (placeholder in Phase 1)
    - Game over screen SVG (placeholder in Phase 1)

    All assets are saved to maps/temples/temple_<id>/ directory.
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        model: str = DEFAULT_MODEL,
        base_dir: str = "maps/temples"
    ):
        """
        Initialize the generation pipeline.

        Args:
            client: Optional OpenAI client (creates one if not provided)
            model: Model to use for generation (default: gpt-5)
            base_dir: Base directory for temple assets (default: maps/temples)
        """
        if client is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            client = OpenAI(api_key=api_key)

        self.client = client
        self.model = model
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _progress(self, percent: int, message: str, progress_callback: Optional[Callable] = None):
        """
        Report progress to callback or print to console.

        Args:
            percent: Progress percentage (0-100)
            message: Status message
            progress_callback: Optional callback function(percent, message)
        """
        if progress_callback:
            progress_callback(percent, message)
        else:
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"[{bar}] {percent}% - {message}")

    def generate_map_from_narrative(
        self,
        narrative: TempleNarrative,
        room_count: int = 100
    ) -> RoomSequence:
        """
        Generate room sequence informed by temple narrative.

        Args:
            narrative: Temple narrative to inform room generation
            room_count: Number of rooms to generate (default: 100)

        Returns:
            RoomSequence with room templates
        """
        # Import here to avoid circular dependency
        from generate_map import insert_antechambers, insert_forks
        from infinite_temple.schema.room import validate_room_sequence

        max_retries = 3
        prompt = textwrap.dedent(f"""
            # Alien Temple Room Sequence Generation

            ## GAME SETTING: INFINITE TEMPLE

            You are generating a sequence of {room_count} connected corridors through an abandoned alien temple on a hostile world. This is a desolate space horror game where you pilot a lone ship through monuments built by extinct civilizations.

            **Temple**: {narrative.title}
            **Backstory**: {narrative.backstory}
            **Atmosphere**: {narrative.atmosphere}
            **Visual Theme**: {narrative.visual_theme}

            Create a room sequence that matches this alien temple's oppressive narrative. The layout should feel:
            - **Alien and disorienting**: Not designed for human navigation
            - **Desolate**: Empty corridors stretching into darkness
            - **Hostile**: The architecture itself feels dangerous
            - **Ancient**: Built by incomprehensible intelligences

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

            ## Requirements

            1. Generate exactly {room_count} rooms (including the starting room)
            2. **ALWAYS start with the "start" room as room #1** - this is mandatory
            3. **NEVER use "start" anywhere except as the first room** - it only has an exit, no entrance
            4. Each subsequent room must connect properly based on the wrapping rule above
            5. The "start" room exits RIGHT, so room #2 must ENTER from LEFT (horizontal, elbow_left_top, or elbow_left_bottom)
            6. Use a variety of room types - avoid long sequences of the same type
            7. Create a path that matches the temple's atmosphere (winding for mysterious, geometric for angular themes, etc.)
            8. Ensure the final room can theoretically connect to additional rooms (don't dead-end impossibly)

            ## Output Format

            Return a JSON object with this structure:

            ```json
            {{
              "rooms": ["start", "horizontal", "elbow_left_bottom", "vertical", ...]
            }}
            ```

            Just a simple array of room template names.

            Generate your {room_count}-room temple sequence now, ensuring all connections are valid and the path creates an interesting exploration experience that matches the temple's narrative.
        """)

        class InvalidRoomSequenceError(Exception):
            pass

        @retry(
            stop=stop_after_attempt(max_retries),
            retry=retry_if_exception_type(InvalidRoomSequenceError),
            reraise=True
        )
        def generate_and_validate():
            response = self.client.responses.parse(
                model=self.model,
                reasoning={"effort": "low"},
                input=[
                    {"role": "system", "content": "You are a level designer creating oppressive, alien temple layouts for a desolate space horror game."},
                    {"role": "user", "content": prompt},
                ],
                text_format=RoomSequence
            )

            room_sequence = response.output_parsed

            is_valid, error_msg = validate_room_sequence(room_sequence.rooms)
            if not is_valid:
                print(f"Room sequence validation failed: {error_msg}")
                raise InvalidRoomSequenceError(error_msg)

            return room_sequence

        room_sequence = generate_and_validate()

        # Insert antechambers (combat rooms)
        room_sequence.rooms = insert_antechambers(room_sequence.rooms)

        # Insert branching paths
        room_sequence.branch_paths = insert_forks(room_sequence.rooms)

        return room_sequence

    def generate_music_from_narrative(self, narrative: TempleNarrative) -> AmbientMusic:
        """
        Generate ambient music informed by temple atmosphere.

        Args:
            narrative: Temple narrative containing atmosphere descriptor

        Returns:
            AmbientMusic with composition data
        """
        # Use the atmosphere from narrative as the environment description
        environment_description = f"{narrative.atmosphere} - {narrative.title}"

        prompt = textwrap.dedent(f"""
            You are a procedural music composer generating oppressive ambient music for a desolate space horror game.

            ## GAME SETTING: INFINITE TEMPLE

            You pilot a lone ship exploring abandoned alien temples on hostile worlds. The music must evoke:
            - Profound isolation and emptiness
            - Unsettling alien presence
            - Cosmic dread and insignificance
            - The haunting silence of extinct civilizations

            TEMPLE: {narrative.title}
            ATMOSPHERE: {environment_description}
            BACKSTORY CONTEXT: {narrative.backstory[:200]}...

            Generate an ambient music piece that captures the oppressive, desolate mood of this alien temple. The music MUST be at least 15 seconds long and designed to loop seamlessly.

            ## COMPOSITION REQUIREMENTS

            1. Create 2-4 voices that work together to create TENSION and UNEASE
            2. Use minor keys, modal scales (Phrygian, Locrian), or atonal elements
            3. **Tempo**: SLOW (50-75 BPM) - time should feel heavy and oppressive
            4. Layer voices with sparse, unsettling rhythms - embrace silence and emptiness
            5. **CRITICAL**: The piece MUST be at least 15 seconds long
            6. **CRITICAL**: End harmonically unresolved or on tonic to loop seamlessly

            ## NOTE FORMAT

            - Pitch: 'c4', 'd#5', 'eb3', etc. (note + optional accidental + octave)
            - Duration: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth
            - Negative for dotted: -4=dotted quarter, -2=dotted half
            - Rest: 'r'

            ## SPACE HORROR MUSIC GUIDELINES

            **Core Principles:**
            - **Sparse texture**: Long sustained notes with gaps of silence
            - **Low frequencies**: Use octaves 2-4 for most voices (deep, oppressive)
            - **Dissonance**: Minor 2nds, tritones, unresolved tensions
            - **Slow tempo**: 50-75 BPM maximum
            - **Minimal melody**: Avoid cheerful or comforting patterns
            - **Alien quality**: Avoid familiar chord progressions

            **Voice Design for Desolate Temples:**
            - **Voice 1 (Drone)**: Very sparse, sustained low notes (octave 2-3), creating oppressive foundation
            - **Voice 2 (Alien pulse)**: Sparse mid-range notes (octave 3-4) with irregular rhythm, unsettling
            - **Voice 3 (Echo)**: Occasional high notes (octave 4-5) that sound distant and cold, like signals from dead stars
            - **Voice 4 (Optional)**: Very sparse textural elements, enhancing emptiness

            **Mood-Specific Guidance:**
            - **Desolate/Empty**: Whole notes, long rests, minor keys, octaves 2-3
            - **Alien/Unsettling**: Tritones, Phrygian mode, irregular rhythms, octaves 3-4
            - **Hostile/Dangerous**: Dissonant intervals, Locrian mode, slow driving pulse, octaves 2-4
            - **Cosmic Horror**: Atonal clusters, very sparse, ultra-slow tempo (50-60 BPM), extreme register contrasts

            **Example Desolate Temple Music** (C Phrygian, 60 BPM):
            ```json
            {{
              "title": "Echoes of the Void",
              "key": "C Phrygian",
              "tempo_bpm": 60,
              "mood": "Desolate alien corridors with profound emptiness",
              "duration_seconds": 16.0,
              "voices": [
                {{
                  "name": "drone",
                  "notes": [
                    {{"pitch": "c2", "duration": 1}},
                    {{"pitch": "r", "duration": 2}},
                    {{"pitch": "db2", "duration": 1}},
                    {{"pitch": "c2", "duration": -1}}
                  ]
                }},
                {{
                  "name": "alien_pulse",
                  "notes": [
                    {{"pitch": "r", "duration": 2}},
                    {{"pitch": "eb3", "duration": 2}},
                    {{"pitch": "r", "duration": 2}},
                    {{"pitch": "f3", "duration": 4}},
                    {{"pitch": "r", "duration": 4}},
                    {{"pitch": "db3", "duration": 2}},
                    {{"pitch": "r", "duration": 2}},
                    {{"pitch": "c3", "duration": 1}}
                  ]
                }},
                {{
                  "name": "distant_echo",
                  "notes": [
                    {{"pitch": "r", "duration": 1}},
                    {{"pitch": "c5", "duration": 4}},
                    {{"pitch": "r", "duration": 1}},
                    {{"pitch": "r", "duration": 1}},
                    {{"pitch": "r", "duration": 1}}
                  ]
                }}
              ]
            }}
            ```

            Generate the ambient music for this alien temple. The music must evoke isolation, cosmic dread, and the desolate beauty of abandoned alien monuments. Return your response as valid JSON.
        """)

        response = self.client.responses.parse(
            model=self.model,
            reasoning={"effort": "medium"},
            input=[
                {"role": "user", "content": prompt},
            ],
            text_format=AmbientMusic
        )

        return response.output_parsed

    def generate_temple(
        self,
        seed_words: list[str],
        room_count: int = 100,
        progress_callback: Optional[Callable] = None
    ) -> TempleConfiguration:
        """
        Generate complete temple from seed words.

        This is the main entry point for temple generation. It orchestrates
        all generation steps and saves all assets. After narrative generation,
        all other steps run in parallel for faster generation.

        Args:
            seed_words: Three seed words to inspire the temple
            room_count: Number of rooms to generate (default: 100)
            progress_callback: Optional callback for progress updates (percent, message, task_statuses)

        Returns:
            TempleConfiguration with all asset paths

        Raises:
            ValueError: If seed_words is not exactly 3 words

        Example:
            >>> pipeline = TempleGenerationPipeline()
            >>> temple = pipeline.generate_temple(["crystal", "shadow", "signal"])
            >>> print(temple.temple_id)
            "temple_1234567890"
        """
        if len(seed_words) != 3:
            raise ValueError(f"Expected exactly 3 seed words, got {len(seed_words)}")

        # Generate temple ID and create directory
        temple_id = f"temple_{int(time.time())}"
        temple_dir = self.base_dir / temple_id
        temple_dir.mkdir(parents=True, exist_ok=True)

        # Shared state for parallel tasks
        task_statuses = {
            "map": {"complete": False, "message": "Waiting...", "result": None, "error": None},
            "music": {"complete": False, "message": "Waiting...", "result": None, "error": None},
            "title_svg": {"complete": False, "message": "Waiting...", "result": None, "error": None},
            "gameover_svg": {"complete": False, "message": "Waiting...", "result": None, "error": None}
        }
        task_lock = threading.Lock()

        def update_overall_progress():
            """Calculate overall progress and send update."""
            with task_lock:
                completed = sum(1 for task in task_statuses.values() if task["complete"])
                # Narrative is 20%, each of 4 parallel tasks is 20% (total 80%), final save is 5%
                overall = 20 + (completed * 20)

                # Build status message
                status_parts = []
                for task_name, status in task_statuses.items():
                    status_parts.append(f"{task_name}: {status['message']}")
                message = " | ".join(status_parts)

                if progress_callback:
                    progress_callback(overall, message, task_statuses.copy())

        self._progress(0, "Starting temple generation...", progress_callback)

        # Stage 1: Generate narrative (blocking) - 20%
        self._progress(10, "Generating temple narrative...", progress_callback)
        narrative = generate_narrative(seed_words, client=self.client, model=self.model)
        narrative_file = temple_dir / "narrative.json"
        with open(narrative_file, "w") as f:
            f.write(narrative.model_dump_json(indent=2))
        self._progress(20, f"✓ Narrative: {narrative.title}", progress_callback)

        # Stage 2: Run parallel tasks (map, music, SVGs) - 80%
        def generate_map_task():
            try:
                with task_lock:
                    task_statuses["map"]["message"] = "Generating..."
                update_overall_progress()

                room_sequence = self.generate_map_from_narrative(narrative, room_count)
                map_file = temple_dir / "map.json"
                with open(map_file, "w") as f:
                    f.write(room_sequence.model_dump_json(indent=2))

                with task_lock:
                    task_statuses["map"]["complete"] = True
                    task_statuses["map"]["message"] = f"✓ {len(room_sequence.rooms)} rooms"
                    task_statuses["map"]["result"] = (room_sequence, map_file)
                update_overall_progress()
            except Exception as e:
                with task_lock:
                    task_statuses["map"]["error"] = e
                    task_statuses["map"]["message"] = f"✗ Error"
                update_overall_progress()

        def generate_music_task():
            try:
                with task_lock:
                    task_statuses["music"]["message"] = "Composing..."
                update_overall_progress()

                music = self.generate_music_from_narrative(narrative)
                audio_file = temple_dir / "audio.json"
                with open(audio_file, "w") as f:
                    f.write(music.model_dump_json(indent=2))

                with task_lock:
                    task_statuses["music"]["complete"] = True
                    task_statuses["music"]["message"] = f"✓ {music.title[:20]}..."
                    task_statuses["music"]["result"] = (music, audio_file)
                update_overall_progress()
            except Exception as e:
                with task_lock:
                    task_statuses["music"]["error"] = e
                    task_statuses["music"]["message"] = f"✗ Error"
                update_overall_progress()

        def generate_title_svg_task():
            try:
                with task_lock:
                    task_statuses["title_svg"]["message"] = "Generating..."
                update_overall_progress()

                title_svg_file = temple_dir / "title.svg"
                title_svg = generate_title_svg(narrative, client=self.client, model=self.model)
                with open(title_svg_file, "w") as f:
                    f.write(title_svg)

                with task_lock:
                    task_statuses["title_svg"]["complete"] = True
                    task_statuses["title_svg"]["message"] = "✓ Complete"
                    task_statuses["title_svg"]["result"] = title_svg_file
                update_overall_progress()
            except Exception as e:
                with task_lock:
                    task_statuses["title_svg"]["error"] = e
                    task_statuses["title_svg"]["message"] = "✗ Error"
                update_overall_progress()

        def generate_gameover_svg_task():
            try:
                with task_lock:
                    task_statuses["gameover_svg"]["message"] = "Generating..."
                update_overall_progress()

                gameover_svg_file = temple_dir / "gameover.svg"
                gameover_svg = generate_gameover_svg(narrative, client=self.client, model=self.model)
                with open(gameover_svg_file, "w") as f:
                    f.write(gameover_svg)

                with task_lock:
                    task_statuses["gameover_svg"]["complete"] = True
                    task_statuses["gameover_svg"]["message"] = "✓ Complete"
                    task_statuses["gameover_svg"]["result"] = gameover_svg_file
                update_overall_progress()
            except Exception as e:
                with task_lock:
                    task_statuses["gameover_svg"]["error"] = e
                    task_statuses["gameover_svg"]["message"] = "✗ Error"
                update_overall_progress()

        # Launch all parallel tasks
        threads = [
            threading.Thread(target=generate_map_task, name="map"),
            threading.Thread(target=generate_music_task, name="music"),
            threading.Thread(target=generate_title_svg_task, name="title_svg"),
            threading.Thread(target=generate_gameover_svg_task, name="gameover_svg")
        ]

        for thread in threads:
            thread.start()

        # Wait for all tasks to complete
        for thread in threads:
            thread.join()

        # Check for errors
        errors = [task for task in task_statuses.values() if task["error"] is not None]
        if errors:
            error_msgs = [f"{name}: {status['error']}" for name, status in task_statuses.items() if status["error"]]
            raise RuntimeError(f"Temple generation failed: {'; '.join(error_msgs)}")

        # Extract results
        room_sequence, map_file = task_statuses["map"]["result"]
        music, audio_file = task_statuses["music"]["result"]
        title_svg_file = task_statuses["title_svg"]["result"]
        gameover_svg_file = task_statuses["gameover_svg"]["result"]

        # Stage 3: Save configuration (100%)
        self._progress(95, "Saving temple configuration...", progress_callback)
        temple_config = TempleConfiguration(
            temple_id=temple_id,
            created_at=datetime.now(),
            seed_words=seed_words,
            narrative=narrative,
            map_file=str(map_file),
            audio_file=str(audio_file),
            title_svg_file=str(title_svg_file),
            gameover_svg_file=str(gameover_svg_file),
            room_count=len(room_sequence.rooms)
        )

        config_file = temple_dir / "config.json"
        with open(config_file, "w") as f:
            f.write(temple_config.model_dump_json(indent=2))

        # Add to catalog
        repo = TempleRepository(base_dir=str(self.base_dir))
        repo.save_temple(temple_config)

        self._progress(100, f"✓ Temple created: {temple_id}", progress_callback)

        return temple_config


if __name__ == "__main__":
    # Test the pipeline
    import sys

    if len(sys.argv) != 4:
        print("Usage: python -m infinite_temple.generation.pipeline <word1> <word2> <word3>")
        print("Example: python -m infinite_temple.generation.pipeline crystal shadow signal")
        sys.exit(1)

    seed_words = sys.argv[1:4]

    pipeline = TempleGenerationPipeline()
    temple = pipeline.generate_temple(seed_words)

    print("\n" + "="*80)
    print("TEMPLE GENERATION COMPLETE")
    print("="*80)
    print(f"\nTemple ID: {temple.temple_id}")
    print(f"Title: {temple.narrative.title}")
    print(f"Rooms: {temple.room_count}")
    print(f"\nAssets saved to: {Path(temple.map_file).parent}")
    print(f"  - Narrative: narrative.json")
    print(f"  - Map: {temple.map_file}")
    print(f"  - Music: {temple.audio_file}")
    print(f"  - Title: {temple.title_svg_file}")
    print(f"  - Game Over: {temple.gameover_svg_file}")
