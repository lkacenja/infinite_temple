"""
Narrative generation from seed words.

This module generates temple narratives (title, backstory, atmosphere, visual theme)
from three seed words using OpenAI structured output.
"""

import os
import textwrap
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

from infinite_temple.schema.temple import TempleNarrative


# Default model for narrative generation
DEFAULT_MODEL = "gpt-5-nano"

# Load environment variables
load_dotenv()


def create_narrative_prompt(seed_words: list[str]) -> str:
    """
    Create prompt for generating temple narrative from seed words.

    Args:
        seed_words: Three seed words provided by the user

    Returns:
        Formatted prompt string for the LLM
    """
    words_str = ", ".join(f'"{word}"' for word in seed_words)

    prompt = textwrap.dedent(f"""
        You are a creative writer crafting evocative narratives for a desolate space horror roguelike game.

        ## SETTING: INFINITE TEMPLE

        You pilot a lone ship through the infinite expanse, discovering abandoned alien temples on distant, hostile worlds. Each temple is a monument to civilizations long extinct—structures built by beings incomprehensible to human minds, now empty except for their haunting presence and lethal architecture.

        **Core Theme**: Desolation, cosmic horror, alien geometry, isolation
        **Tone**: Oppressive, mysterious, unsettling, vast emptiness with touches of the unknowable

        SEED WORDS: {words_str}

        Your task is to generate a cohesive alien temple narrative that weaves together these three seed words into a compelling backstory.

        ## Requirements

        ### 1. Temple Title
        - Create an evocative, unsettling temple name
        - Should feel alien, ancient beyond comprehension, abandoned
        - Examples: "The Hollowed Spire of Silent Witnesses", "The Void Cathedral Where Stars Died", "Monument to Absent Gods"
        - Must incorporate themes from the seed words
        - Emphasize the alien and desolate nature

        ### 2. Backstory (100-500 words)
        - Write temple lore explaining its alien origins, purpose, and current desolate state
        - Naturally integrate all three seed words into the narrative
        - Include details about:
          - What alien civilization built it and for what incomprehensible purpose
          - What catastrophic event led to its abandonment
          - What cosmic mysteries or dangers lurk in its passages
          - The profound sense of isolation and emptiness
        - **CRITICAL**: This is on an alien world, not Earth
        - **CRITICAL**: The builders were non-human, their motivations unknowable
        - The backstory should evoke cosmic horror and desolation
        - Be evocative but concise - aim for 200-300 words

        ### 3. Atmosphere Descriptor
        - A SHORT phrase (5-10 words) describing the oppressive mood
        - This will be used to generate ambient music
        - Examples:
          - "empty alien corridors echoing with void-wind"
          - "crystalline darkness humming with dead frequencies"
          - "desolate metal passages under dying starlight"
          - "frozen chambers where gravity distorts unnaturally"
        - Focus on: isolation, alien textures, unnatural sounds, hostile environments
        - **Must feel desolate and unsettling**

        ### 4. Visual Theme
        - A SHORT phrase (5-10 words) describing alien architectural style
        - This will be used to generate SVG artwork
        - Examples:
          - "non-Euclidean geometry with impossible angles"
          - "biomechanical structures fused with crystalline growths"
          - "stark angular monoliths etched with alien glyphs"
          - "fractal patterns that hurt to comprehend"
        - Focus on: alien geometry, unsettling forms, inhuman scale
        - **Must feel otherworldly and strange**

        ## Guidelines

        - **Space Horror**: Emphasize isolation, vastness, incomprehensibility, dread
        - **Alien Nature**: Nothing should feel human or familiar—these are monuments to extinct alien minds
        - **Desolation**: The temples are empty tombs, silent except for the echoes of your ship
        - **Cohesion**: All elements should feel like they belong to the same alien temple
        - Avoid Earth-based references (no "stone," prefer "unknown materials," "alien composites")
        - Avoid familiar religious imagery—make it truly alien
        - The temple should feel hostile and indifferent to human life
        - Don't just list the seed words—weave them naturally into cosmic horror

        ## Example

        **Seed Words**: "crystal", "shadow", "signal"

        **Output**:
        {{
          "title": "The Resonance Vault of Crystalline Silence",
          "backstory": "On a frozen world beneath a dying red dwarf star stands a temple carved from translucent mineral unknown to human science. The beings who built it called across the void with crystalline transmitters, broadcasting signals into the cosmic dark for eons, waiting for an answer that never came. Their civilization expired in the waiting—not destroyed, simply ended, as if they collectively decided existence held no further purpose. The temple remains, its crystalline spires still humming with residual electromagnetic radiation, casting shadows that move independently of any light source. Your ship's instruments malfunction near it, picking up fragments of the ancient signal—not language, not mathematics, but something that makes your mind ache with half-formed comprehension. The corridors refract your helmet lights into kaleidoscopic distortions, and in the shadows between the beams, you sometimes glimpse shapes that vanish when observed directly. This place was built to communicate with something vast and terrible, and though the builders are gone, the signal still echoes, still searches, still waits.",
          "atmosphere": "crystalline alien halls humming with dead signals",
          "visual_theme": "fractured crystal geometry casting impossible shadows"
        }}

        Now generate the alien temple narrative for the given seed words. Ensure all components work together to create a unified vision of desolate space horror.
    """)

    return prompt


def generate_narrative(
    seed_words: list[str],
    client: Optional[OpenAI] = None,
    model: str = DEFAULT_MODEL
) -> TempleNarrative:
    """
    Generate temple narrative from three seed words using OpenAI structured output.

    Args:
        seed_words: Three seed words to inspire the narrative (must be exactly 3)
        client: Optional OpenAI client instance (creates one if not provided)
        model: Model to use for generation (default: gpt-5-nano)

    Returns:
        TempleNarrative with title, backstory, atmosphere, visual_theme

    Raises:
        ValueError: If seed_words is not exactly 3 words

    Example:
        >>> narrative = generate_narrative(["crystal", "shadow", "signal"])
        >>> print(narrative.title)
        "The Resonance Vault of Crystalline Silence"
    """
    # Validate input
    if len(seed_words) != 3:
        raise ValueError(f"Expected exactly 3 seed words, got {len(seed_words)}")

    # Create client if not provided
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        client = OpenAI(api_key=api_key)

    # Generate prompt
    prompt = create_narrative_prompt(seed_words)

    print(f"Generating narrative from seeds: {', '.join(seed_words)}")

    # Call OpenAI with structured output
    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": "You are a creative writer specializing in desolate space horror and cosmic dread narratives."
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=TempleNarrative
    )

    narrative = response.output_parsed

    print(f"✓ Generated narrative: {narrative.title}")
    print(f"  Atmosphere: {narrative.atmosphere}")
    print(f"  Visual theme: {narrative.visual_theme}")

    return narrative


if __name__ == "__main__":
    # Test the narrative generator
    import sys

    if len(sys.argv) != 4:
        print("Usage: python -m infinite_temple.generation.narrative <word1> <word2> <word3>")
        print("Example: python -m infinite_temple.generation.narrative crystal shadow signal")
        sys.exit(1)

    seed_words = sys.argv[1:4]
    narrative = generate_narrative(seed_words)

    print("\n" + "="*80)
    print("GENERATED NARRATIVE")
    print("="*80)
    print(f"\nTitle: {narrative.title}")
    print(f"\nBackstory:\n{narrative.backstory}")
    print(f"\nAtmosphere: {narrative.atmosphere}")
    print(f"Visual Theme: {narrative.visual_theme}")
