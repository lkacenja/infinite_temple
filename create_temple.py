#!/usr/bin/env python3
"""
CLI tool for generating desolate alien temples from seed words.

INFINITE TEMPLE - Desolate Space Horror Edition

Usage:
    python create_temple.py <word1> <word2> <word3>

Example:
    python create_temple.py crystal shadow signal

This will generate:
- Temple narrative (title, backstory, atmosphere, visual theme)
  → LLM generates an alien temple with cosmic horror themes
- Room sequence (100+ connected corridors through hostile architecture)
- Ambient music composition (oppressive, sparse, unsettling)
- Title screen SVG (unique alien geometry artwork)
- Game over screen SVG (oppressive defeat artwork)

All assets are saved to maps/temples/temple_<id>/ directory.

Theme: Pilot a lone ship through abandoned alien temples on distant worlds.
Each temple is a monument to extinct civilizations—desolate, hostile, and incomprehensible.
"""

import sys
import argparse
from pathlib import Path

from infinite_temple.generation.pipeline import TempleGenerationPipeline


def main():
    """Main entry point for temple generation CLI."""
    parser = argparse.ArgumentParser(
        description="Generate a desolate alien temple from three seed words",
        epilog="Example: python create_temple.py crystal shadow signal"
    )

    parser.add_argument(
        "seed_words",
        nargs=3,
        metavar="WORD",
        help="Three seed words to inspire temple generation"
    )

    parser.add_argument(
        "--rooms",
        type=int,
        default=100,
        help="Number of rooms to generate (default: 100)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5-nano",
        help="OpenAI model to use (default: gpt-5-nano)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="maps/temples",
        help="Base directory for temple assets (default: maps/temples)"
    )

    args = parser.parse_args()

    # Print header
    print("="*80)
    print("INFINITE TEMPLE GENERATOR")
    print("Desolate Space Horror Edition")
    print("="*80)
    print(f"\nGenerating alien temple from seeds: {', '.join(args.seed_words)}")
    print(f"Rooms: {args.rooms}")
    print(f"Model: {args.model}")
    print()

    try:
        # Create pipeline and generate temple
        pipeline = TempleGenerationPipeline(
            model=args.model,
            base_dir=args.output_dir
        )

        temple = pipeline.generate_temple(
            seed_words=args.seed_words,
            room_count=args.rooms
        )

        # Print summary
        print("\n" + "="*80)
        print("✓ TEMPLE CREATED SUCCESSFULLY")
        print("="*80)
        print(f"\nID: {temple.temple_id}")
        print(f"Title: {temple.narrative.title}")
        print(f"Rooms: {temple.room_count}")
        print(f"\nBackstory:")
        print(f"{temple.narrative.backstory[:200]}...")
        print(f"\nAtmosphere: {temple.narrative.atmosphere}")
        print(f"Visual Theme: {temple.narrative.visual_theme}")
        print(f"\nAssets saved to: {Path(temple.map_file).parent}/")
        print(f"  - Configuration: config.json")
        print(f"  - Narrative: narrative.json")
        print(f"  - Map: map.json")
        print(f"  - Music: audio.json")
        print(f"  - Title Screen: title.svg")
        print(f"  - Game Over: gameover.svg")
        print("\nTo play this temple, update game.py to load:")
        print(f"  {temple.map_file}")

    except ValueError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
