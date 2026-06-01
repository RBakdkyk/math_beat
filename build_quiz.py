#!/usr/bin/env python3
"""build_quiz.py — build a self-contained quiz.html from a session's questions."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from quiz import build_quiz
from config import parent_whatsapp_number
from wiki import read_generated, quiz_path, today as wiki_today


def main():
    parser = argparse.ArgumentParser(description="Build an HTML quiz for a session.")
    parser.add_argument("--date", default=None, help="Session date YYYY-MM-DD (default: today)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing quiz.html")
    args = parser.parse_args()

    session_date = args.date or wiki_today()

    questions = read_generated(session_date)
    if not questions:
        print(f"Error: no generated.json for {session_date}. Run generate.py first.", file=sys.stderr)
        sys.exit(1)

    out_path = quiz_path(session_date)
    if out_path.exists() and not args.force:
        print(f"Error: quiz already exists for {session_date}. Use --force to overwrite.")
        sys.exit(1)

    html_doc = build_quiz(questions, session_date, parent_whatsapp_number())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8")

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
