#!/usr/bin/env python3
"""Result-code contract tests (stdlib only).

Run: python tests/test_quizcode.py

Covers change `add-html-quiz-layer`:
  - encode -> decode round-trips numeric, fraction, Hebrew, and blank answers
  - a mutated code is rejected by decode (checksum / structure)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quizcode import encode, decode  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ── 1. Round-trip over representative answers (incl. blanks) ─────────────────

DATE = "2026-06-01"
ANSWERS = [
    (1, "144"),          # numeric
    (2, ""),             # blank
    (3, "12/10"),        # fraction (slash must survive)
    (4, "ראשוני"),       # Hebrew categorical
    (5, "כן"),           # Hebrew yes/no
    (6, "1 2/10"),       # mixed number with space
    (7, "שווים"),        # Hebrew comparison
]

code = encode(ANSWERS, DATE)
got = decode(code)

check(got["date"] == DATE, f"round-trip date: {got['date']!r} != {DATE!r}")
check(len(got["answers"]) == len(ANSWERS),
      f"round-trip count: {len(got['answers'])} != {len(ANSWERS)}")
for (exp_id, exp_ans), a in zip(ANSWERS, got["answers"]):
    check(a["id"] == exp_id, f"id mismatch: {a['id']} != {exp_id}")
    check(a["answer"] == exp_ans,
          f"answer mismatch for q{exp_id}: {a['answer']!r} != {exp_ans!r}")

# Code must be URL-safe (only unreserved chars: A-Za-z0-9-_~ and the date's '-')
import re  # noqa: E402
check(re.fullmatch(r"[A-Za-z0-9\-_~]+", code) is not None,
      f"code has URL-unsafe characters: {code!r}")

# Dict-form answers accepted too
code2 = encode([{"id": 1, "answer": "144"}, {"id": 2, "answer": ""}], DATE)
got2 = decode(code2)
check(got2["answers"][0]["answer"] == "144" and got2["answers"][1]["answer"] == "",
      "dict-form encode round-trip failed")


# ── 2. Corruption is rejected ───────────────────────────────────────────────

def rejects(bad_code, label):
    try:
        decode(bad_code)
    except ValueError:
        return
    _failures.append(f"decode accepted bad code ({label}): {bad_code!r}")


# Flip the checksum char (last char)
rejects(code[:-1] + ("x" if code[-1] != "x" else "y"), "mutated checksum")
# Mutate a payload char (keep length) — should fail checksum
mid = len(code) // 2
rejects(code[:mid] + ("A" if code[mid] != "A" else "B") + code[mid + 1:], "mutated payload")
# Drop a character
rejects(code[:-2] + code[-1:], "dropped character")
# Wrong prefix
rejects("XXX" + code[3:], "bad prefix")
# Wrong segment count
rejects("AYL~2026-06-01", "too few segments")


# ── report ──────────────────────────────────────────────────────────────────

if _failures:
    print(f"FAIL ({len(_failures)}):")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("test_quizcode: OK")
