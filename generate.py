#!/usr/bin/env python3
"""generate.py — generate a daily math practice session."""

import argparse
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent / "src"))

from generator import generate_session
from formatter import format_session
from wiki import generated_path, write_generated, today as wiki_today


def main():
    parser = argparse.ArgumentParser(description="Generate a math practice session for Ayala.")
    parser.add_argument("--topics", nargs="+", help="Question types to include (overrides auto-selection)")
    parser.add_argument("--count", type=int, default=8, help="Number of questions (default: 8)")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], help="Force difficulty level")
    parser.add_argument("--date", default=None, help="Session date YYYY-MM-DD (default: today)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing session")
    args = parser.parse_args()

    session_date = args.date or wiki_today()
    out_path = generated_path(session_date)

    if out_path.exists() and not args.force:
        print(f"Error: session already exists for {session_date}. Use --force to overwrite.")
        sys.exit(1)

    questions = generate_session(
        count=args.count,
        topics_override=args.topics,
        difficulty_override=args.difficulty,
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
