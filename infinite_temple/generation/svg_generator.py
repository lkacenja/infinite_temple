"""
SVG artwork generation from temple narratives.

This module generates SVG artwork for title and game over screens using
LLM to create visuals that match each temple's unique aesthetic.
"""

import textwrap
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from pydantic import BaseModel

from infinite_temple.schema.temple import TempleNarrative

if TYPE_CHECKING:
    from infinite_temple.generation.llm_client import LLMClient


class SVGArtwork(BaseModel):
    """SVG artwork response schema"""
    svg_content: str


def create_title_svg_prompt(narrative: TempleNarrative) -> str:
    """
    Create prompt for generating title screen SVG.

    Args:
        narrative: Temple narrative containing visual theme and title

    Returns:
        Formatted prompt string for the LLM
    """
    prompt = textwrap.dedent(f"""
        You are an expert SVG designer creating artwork for a desolate space horror game.

        ## GAME: INFINITE TEMPLE

        A roguelike where you pilot a lone ship exploring abandoned alien temples on hostile worlds.
        Visual style: Desolate, alien geometry, cosmic horror, stark minimalism.

        ## TEMPLE DETAILS

        **Title**: {narrative.title}
        **Visual Theme**: {narrative.visual_theme}
        **Atmosphere**: {narrative.atmosphere}
        **Backstory**: {narrative.backstory[:150]}...

        ## TASK: Generate Title Screen Background SVG

        Create an 800x800 SVG background artwork. **DO NOT include any text** - the game UI renders the title and instructions separately.

        ### Visual Requirements
        1. **NO TEXT**: Do not include any text elements, titles, or labels
        2. **Alien Geometry**: Create abstract geometric shapes inspired by "{narrative.visual_theme}"
        3. **Desolate Aesthetic**: Minimal color palette, stark contrasts, empty space
        4. **Composition**: Center-focused with breathing room, leave space for UI text overlay

        ### Color Palette (Desolate Space Horror)
        - **Background**: Deep space black (#000000 or #0a0a0a)
        - **Primary shapes**: Muted grays, deep blues, sickly greens (#2a2a2a, #1a3a4a, #2a3a2a)
        - **Accents**: Dim cyan/red for alien tech (#00cccc, #cc4444) - use sparingly
        - **Avoid**: Bright colors, warm tones, cheerful palettes

        ### Geometric Design Principles
        - **Angular/Sharp themes**: Use polygons, sharp lines, triangular forms
        - **Organic/Flowing themes**: Use smooth curves, ellipses, wavy paths
        - **Crystalline themes**: Use overlapping transparent polygons, faceted shapes
        - **Brutalist themes**: Use thick rectangles, heavy geometric blocks
        - Keep it SIMPLE - 5-10 shapes maximum
        - Use negative space effectively

        ### Technical Requirements
        1. **Valid SVG 1.1 syntax** - must be parseable by standard SVG renderers
        2. **800x800 viewBox**: `<svg viewBox="0 0 800 800" ...>`
        3. **NO TEXT ELEMENTS** - geometry only
        4. **No external resources**: No images, no external fonts, no scripts
        5. **No advanced features**: Avoid filters (except basic opacity), animations, or complex patterns

        ### Example Structure

        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <svg viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
          <!-- Background -->
          <rect width="800" height="800" fill="#0a0a0a"/>

          <!-- Alien geometry (5-10 shapes) -->
          <polygon points="..." fill="#2a2a2a" opacity="0.8"/>
          <circle cx="..." cy="..." r="..." fill="none" stroke="#00cccc" stroke-width="2" opacity="0.6"/>
          <path d="..." fill="none" stroke="#1a3a4a" stroke-width="1"/>
          <!-- More geometric shapes... -->
        </svg>
        ```

        ### Design Guidelines
        - **Alien and unsettling**: Shapes should feel strange and non-human
        - **Desolate**: Embrace emptiness, don't fill every pixel
        - **Mysterious**: Subtle details that hint at ancient purpose
        - **Hostile**: Angular, sharp, or oppressive forms
        - Match the visual theme: "{narrative.visual_theme}"
        - **REMINDER**: No text - pure geometric artwork only

        ## Output Format

        Return ONLY the complete SVG markup as a single string in the `svg_content` field.
        Do not include markdown code blocks or explanations.

        Generate the title screen background SVG now.
    """)

    return prompt


def create_gameover_svg_prompt(narrative: TempleNarrative) -> str:
    """
    Create prompt for generating game over screen SVG.

    Args:
        narrative: Temple narrative containing visual theme

    Returns:
        Formatted prompt string for the LLM
    """
    prompt = textwrap.dedent(f"""
        You are an expert SVG designer creating artwork for a desolate space horror game.

        ## GAME: INFINITE TEMPLE

        A roguelike where you pilot a lone ship exploring abandoned alien temples on hostile worlds.
        Visual style: Desolate, alien geometry, cosmic horror, stark minimalism.

        ## TEMPLE DETAILS

        **Title**: {narrative.title}
        **Visual Theme**: {narrative.visual_theme}
        **Atmosphere**: {narrative.atmosphere}

        ## TASK: Generate Game Over Screen Background SVG

        Create an 800x800 SVG background artwork. **DO NOT include any text** - the game UI renders the "GAME OVER" text and instructions separately.

        ### Visual Requirements
        1. **NO TEXT**: Do not include any text elements, titles, or labels
        2. **Alien Geometry**: Similar to title screen but MORE OPPRESSIVE
        3. **Defeat Aesthetic**: Darker, more claustrophobic, heavier shapes
        4. **Visual Continuity**: Should feel related to the title screen but darker/hostile

        ### Color Palette (Death and Defeat)
        - **Background**: Deeper black (#000000)
        - **Primary shapes**: Darker grays, blood reds, sickly colors (#1a1a1a, #4a1a1a, #1a2a1a)
        - **Accents**: Dull red/amber warning colors (#aa3333, #aa6633) - use sparingly
        - **Overall mood**: DARKER than title screen

        ### Geometric Design Principles (Game Over)
        - **Heavier shapes**: Thicker lines, larger masses, more oppressive
        - **Closer to edges**: Less breathing room, more claustrophobic
        - **Angular/threatening**: Prefer sharp angles over curves
        - **Broken/fractured**: Suggest destruction or defeat
        - Match visual theme: "{narrative.visual_theme}" but make it DARKER

        ### Technical Requirements
        1. **Valid SVG 1.1 syntax** - must be parseable by standard SVG renderers
        2. **800x800 viewBox**: `<svg viewBox="0 0 800 800" ...>`
        3. **NO TEXT ELEMENTS** - geometry only
        4. **No external resources**: No images, no external fonts, no scripts
        5. **No advanced features**: Avoid filters (except basic opacity), animations, or complex patterns

        ### Example Structure

        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <svg viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
          <!-- Background (pure black) -->
          <rect width="800" height="800" fill="#000000"/>

          <!-- Oppressive alien geometry -->
          <polygon points="..." fill="#1a1a1a" opacity="0.9"/>
          <rect x="..." y="..." width="..." height="..." fill="#4a1a1a" opacity="0.7"/>
          <path d="..." fill="none" stroke="#aa3333" stroke-width="2"/>
          <!-- More threatening shapes... -->
        </svg>
        ```

        ### Design Guidelines (Game Over)
        - **Oppressive**: Shapes press in, feel claustrophobic
        - **Defeated**: Suggest the temple's dominance over the player
        - **Darker**: Everything is dimmer, heavier, more ominous than title screen
        - **Continuity**: Use similar geometry to title screen but transformed
        - Visual theme: "{narrative.visual_theme}" but hostile and victorious
        - **REMINDER**: No text - pure geometric artwork only

        ## Output Format

        Return ONLY the complete SVG markup as a single string in the `svg_content` field.
        Do not include markdown code blocks or explanations.

        Generate the game over screen background SVG now.
    """)

    return prompt


def generate_title_svg(
    narrative: TempleNarrative,
    llm_client: "LLMClient" = None
) -> str:
    """
    Generate title screen SVG from temple narrative.

    Args:
        narrative: Temple narrative with visual theme and title
        llm_client: LLMClient instance for generation

    Returns:
        SVG markup as string

    Raises:
        ValueError: If no client provided or SVG generation fails

    Example:
        >>> from infinite_temple.generation.llm_client import LLMClient
        >>> client = LLMClient(provider="anthropic")
        >>> svg = generate_title_svg(narrative, client)
        >>> with open("title.svg", "w") as f:
        ...     f.write(svg)
    """
    if llm_client is None:
        raise ValueError("llm_client is required")

    # Generate prompt
    prompt = create_title_svg_prompt(narrative)

    print(f"Generating title screen SVG for: {narrative.title}")

    # Call LLM with structured output
    result = llm_client.generate_with_schema(
        prompt=prompt,
        schema=SVGArtwork,
        system="You are an expert SVG designer specializing in minimalist alien and cosmic horror aesthetics.",
        reasoning_effort="high"
    )

    svg_content = result.svg_content

    # Unescape if needed (LLM may return JSON-escaped strings)
    import json
    if '\\' in svg_content:
        try:
            svg_content = json.loads(f'"{svg_content}"')
        except:
            pass  # If it fails, use as-is

    # Basic validation
    if not svg_content.strip().startswith("<?xml") and not svg_content.strip().startswith("<svg"):
        raise ValueError("Generated content is not valid SVG")

    # Add XML declaration if missing
    if not svg_content.strip().startswith("<?xml"):
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_content

    print(f"✓ Title SVG generated ({len(svg_content)} bytes)")

    return svg_content


def generate_gameover_svg(
    narrative: TempleNarrative,
    llm_client: "LLMClient" = None
) -> str:
    """
    Generate game over screen SVG from temple narrative.

    Args:
        narrative: Temple narrative with visual theme
        llm_client: LLMClient instance for generation

    Returns:
        SVG markup as string

    Raises:
        ValueError: If no client provided or SVG generation fails

    Example:
        >>> from infinite_temple.generation.llm_client import LLMClient
        >>> client = LLMClient(provider="anthropic")
        >>> svg = generate_gameover_svg(narrative, client)
        >>> with open("gameover.svg", "w") as f:
        ...     f.write(svg)
    """
    if llm_client is None:
        raise ValueError("llm_client is required")

    # Generate prompt
    prompt = create_gameover_svg_prompt(narrative)

    print(f"Generating game over screen SVG for: {narrative.title}")

    # Call LLM with structured output
    result = llm_client.generate_with_schema(
        prompt=prompt,
        schema=SVGArtwork,
        system="You are an expert SVG designer specializing in dark, oppressive alien aesthetics for game over screens.",
        reasoning_effort="high"
    )

    svg_content = result.svg_content

    # Unescape if needed (LLM may return JSON-escaped strings)
    import json
    if '\\' in svg_content:
        try:
            svg_content = json.loads(f'"{svg_content}"')
        except:
            pass  # If it fails, use as-is

    # Basic validation
    if not svg_content.strip().startswith("<?xml") and not svg_content.strip().startswith("<svg"):
        raise ValueError("Generated content is not valid SVG")

    # Add XML declaration if missing
    if not svg_content.strip().startswith("<?xml"):
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_content

    print(f"✓ Game over SVG generated ({len(svg_content)} bytes)")

    return svg_content


if __name__ == "__main__":
    # Test SVG generation
    import sys
    from infinite_temple.generation.narrative import generate_narrative
    from infinite_temple.generation.llm_client import LLMClient, DEFAULT_PROVIDER

    if len(sys.argv) < 4:
        print("Usage: python -m infinite_temple.generation.svg_generator <word1> <word2> <word3> [provider]")
        print("Example: python -m infinite_temple.generation.svg_generator crystal shadow signal anthropic")
        sys.exit(1)

    seed_words = sys.argv[1:4]
    provider = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_PROVIDER

    client = LLMClient(provider=provider)

    print("="*80)
    print("SVG ARTWORK GENERATOR TEST")
    print("="*80)
    print()

    # Generate narrative first
    narrative = generate_narrative(seed_words, llm_client=client)

    print()
    print("Generating SVG artwork...")
    print()

    # Generate title SVG
    title_svg = generate_title_svg(narrative, llm_client=client)
    title_path = Path("test_title.svg")
    with open(title_path, "w") as f:
        f.write(title_svg)
    print(f"Title SVG saved to: {title_path}")

    # Generate game over SVG
    gameover_svg = generate_gameover_svg(narrative, llm_client=client)
    gameover_path = Path("test_gameover.svg")
    with open(gameover_path, "w") as f:
        f.write(gameover_svg)
    print(f"Game over SVG saved to: {gameover_path}")

    print()
    print("="*80)
    print("✓ SVG GENERATION COMPLETE")
    print("="*80)
    print(f"\nOpen the SVG files in a browser or SVG viewer to preview.")
