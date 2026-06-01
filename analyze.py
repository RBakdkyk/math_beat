#!/usr/bin/env python3
"""analyze.py — update progress from a session's results."""

import argparse
import json
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent / "src"))

from progress import update_summary, rebuild_summary
from wiki import read_summary


def _wiki_today():
    return date.today().isoformat()


def _print_summary(summary: dict, session_date: str) -> None:
    topics = summary.get("topics", {})
    print(f"\nProgress Summary — {session_date}")
    print("=" * 40)
    if not topics:
        print("(no data yet)")
        return
    for qtype, tdata in sorted(topics.items(), key=lambda x: x[1].get("correct_rate", 0)):
        rate = int(tdata.get("correct_rate", 0) * 100)
        times = tdata.get("times_practiced", 0)
        name = qtype  # fallback
        try:
            from curriculum import TOPICS
            name = TOPICS.get(qtype, {}).get("name", qtype)
        except Exception:
            pass
        print(f"  {name:30s} {rate:3d}%  ({times} times)")

    # Multiplication weak facts
    mult = topics.get("multiplication-table", {})
    facts = mult.get("facts", {})
    if facts:
        weak = sorted(
            [(f["wrong"] / max(f["correct"] + f["wrong"], 1), k)
             for k, f in facts.items()],
            reverse=True
        )[:3]
        if weak:
            print(f"\n  Weak multiplication facts: {', '.join(k for _, k in weak)}")


def main():
    parser = argparse.ArgumentParser(description="Update progress from session results.")
    parser.add_argument("date", nargs="?", default=None,
                        help="Session date YYYY-MM-DD (default: today)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Rebuild summary.json from all sessions")
    args = parser.parse_args()

    if args.rebuild:
        print("Rebuilding progress from all sessions...")
        summary = rebuild_summary()
        print("Done. summary.json updated.")
        _print_summary(summary, "rebuild")
        return

    session_date = args.date or _wiki_today()
    try:
        summary = update_summary(session_date)
        _print_summary(summary, session_date)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
