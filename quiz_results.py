#!/usr/bin/env python3
"""quiz_results.py — decode a returned AYL~ code and grade it (for /results).

The `/results` skill calls this so grading stays deterministic and testable:

    python quiz_results.py preview "<pasted text or AYL~ code>"
    python quiz_results.py write   "<pasted text or AYL~ code>" [--force]

`preview` prints a JSON object describing the decoded/graded answers (or an
`error`); it writes nothing. `write` (re)writes results.json. The caller decides
whether to run `analyze.py {date}` (first time) or `analyze.py --rebuild`
(re-processing a date that already had results) based on the `exists` flag.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from codec import decode, CodeError
from grading import grade_payload, to_results
from wiki import read_generated, results_path, write_results


def _decode_and_grade(raw: str):
    """Return (date, graded) or raise CodeError / a message-bearing error."""
    date, payload = decode(raw)  # extracts, validates checksum, decodes JSON
    questions = read_generated(date)
    if questions is None:
        raise CodeError(f"No session was generated for {date}; cannot grade this code.")
    return date, payload, grade_payload(questions, payload)


def _preview(raw: str) -> int:
    try:
        date, _payload, graded = _decode_and_grade(raw)
    except CodeError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    correct = sum(1 for g in graded if g["correct"])
    print(json.dumps({
        "date": date,
        "exists": results_path(date).exists(),
        "graded": graded,
        "correct": correct,
        "total": len(graded),
    }, ensure_ascii=False))
    return 0


def _write(raw: str, force: bool) -> int:
    try:
        date, _payload, graded = _decode_and_grade(raw)
    except CodeError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    results = to_results(graded)
    existed = results_path(date).exists()
    write_results(results, date, force=force or existed)
    print(json.dumps({
        "written": str(results_path(date)),
        "date": date,
        "count": len(results),
        "reprocessed": existed,  # caller should run analyze.py --rebuild when True
    }, ensure_ascii=False))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode and grade a returned AYL~ code.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_prev = sub.add_parser("preview", help="Decode and grade; print JSON, write nothing")
    p_prev.add_argument("code", help="Pasted text containing an AYL~ code")
    p_write = sub.add_parser("write", help="Decode, grade, and write results.json")
    p_write.add_argument("code", help="Pasted text containing an AYL~ code")
    p_write.add_argument("--force", action="store_true", help="Force overwrite results.json")
    args = parser.parse_args()

    if args.cmd == "preview":
        sys.exit(_preview(args.code))
    else:
        sys.exit(_write(args.code, args.force))


if __name__ == "__main__":
    main()
