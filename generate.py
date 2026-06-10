#!/usr/bin/env python3
"""generate.py — generate a daily math practice session."""

import argparse
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent / "src"))

from generator import generate_session
from formatter import format_session
from session import parse_difficulty_tokens, resolve_topic_alias
from wiki import generated_path, write_generated, today as wiki_today


def main():
    parser = argparse.ArgumentParser(description="Generate a math practice session for Ayala.")
    parser.add_argument("--topics", nargs="+", help="Question types to include (overrides auto-selection)")
    parser.add_argument("--count", type=int, default=10, help="Number of questions (default: 10)")
    parser.add_argument(
        "--difficulty",
        nargs="+",
        help="A single global level (easy/medium/hard) and/or per-topic "
             "assignments (e.g. fractions=hard division=easy)",
    )
    parser.add_argument("--date", default=None, help="Session date YYYY-MM-DD (default: today)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing session")
    args = parser.parse_args()

    difficulty_global = None
    difficulty_map = None
    if args.difficulty:
        try:
            difficulty_global, difficulty_map = parse_difficulty_tokens(args.difficulty)
        except ValueError as e:
            parser.error(f"--difficulty: {e}")

    # Expand --topics tokens through the same alias map (e.g. fractions ->
    # the three fraction subtopics) so they line up with per-topic difficulty
    # keys and resolve to real template generators. Unknown tokens pass through.
    topics_override = None
    if args.topics:
        topics_override = []
        for tok in args.topics:
            resolved = resolve_topic_alias(tok)
            topics_override.extend(resolved if resolved else [tok])

    session_date = args.date or wiki_today()
    out_path = generated_path(session_date)

    if out_path.exists() and not args.force:
        print(f"Error: session already exists for {session_date}. Use --force to overwrite.")
        sys.exit(1)

    questions = generate_session(
        count=args.count,
        topics_override=topics_override,
        difficulty_override=difficulty_global,
        difficulty_map=difficulty_map,
        session_date=session_date,
    )

    if not questions:
        print("Error: failed to generate questions.", file=sys.stderr)
        sys.exit(1)

    write_generated(questions, session_date, force=args.force)

    formatted = format_session(questions, session_date)
    print(formatted)


if __name__ == "__main__":
    main()
