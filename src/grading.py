"""Grading rules for return-code answers (no wiki/curriculum import — pure logic).

Implements the subtleties the three recovered codes exposed:
  * number normalization — strip `,` thousands separators and trailing stray
    punctuation, keep `.` and `/`;
  * unit-stripping from measurement answer keys (`"247 מ\\"ר"` vs typed `247`);
  * fraction equivalence (unreduced ↔ reduced ↔ decimal ↔ Hebrew mixed `1 ו-1/2`);
  * comparison-symbol derivation for `fraction-comparison` (stored answer is the
    larger fraction, or `"שווים"` → `=`).

`grade_payload(questions, payload)` maps decoded `[[id,"answer"], …]` entries to
questions by `id`, omitting blank `""` answers and ids absent from `generated.json`.
"""

from __future__ import annotations

import re
from fractions import Fraction

# Leading number-ish token: digits with optional .,/ and an optional Hebrew mixed
# tail ("1 ו-1/2"); everything after (units like מ"ר, ס"מ) is dropped.
_NUMBER_HEAD = re.compile(r"^\s*(\d[\d.,/]*(?:\s*ו-\s*\d+/\d+)?)")
_MIXED = re.compile(r"^(\d+)\s*ו-\s*(\d+)/(\d+)$")
_COMPARISON = re.compile(r"\s*(.+?)\s*___\s*(.+?)\s*$")
_EQUAL_WORDS = {"שווים", "שווה", "="}


def normalize_number(s: str) -> str:
    """Strip `,` thousands separators and trailing stray punctuation; keep `.`/`/`."""
    s = s.strip().replace(",", "")
    return s.rstrip(" .;")


def strip_units(s: str) -> str:
    """Return the leading numeric/fraction token, dropping a trailing unit suffix."""
    s = s.strip()
    m = _NUMBER_HEAD.match(s)
    return m.group(1).strip() if m else s


def _to_fraction(s: str) -> Fraction:
    """Parse a number/fraction string to a Fraction (raises on non-numeric)."""
    s = s.strip()
    m = _MIXED.match(s)
    if m:
        whole, num, den = (int(x) for x in m.groups())
        return Fraction(whole) + Fraction(num, den)
    if "/" in s:
        num, den = s.split("/", 1)
        return Fraction(int(num), int(den))
    if "." in s:
        return Fraction(s)  # Fraction("52.1") is exact
    return Fraction(int(s))


def _numeric_equal(stored: str, child: str) -> bool:
    try:
        a = _to_fraction(strip_units(normalize_number(stored)))
        b = _to_fraction(strip_units(normalize_number(child)))
    except (ValueError, ZeroDivisionError):
        return False
    return a == b


def _norm_cat(s: str) -> str:
    return s.strip().replace(" ", "").casefold()


def derive_symbol(exercise: str, stored_answer: str) -> str | None:
    """Derive the correct `>`/`<`/`=` for a fraction-comparison question.

    `exercise` looks like `"1/5 ___ 5/8"`; the stored answer is the larger
    fraction (so it equals one operand) or `"שווים"` when equal.
    """
    m = _COMPARISON.match(exercise)
    if not m:
        return None
    left, right = m.group(1).strip(), m.group(2).strip()
    sa = stored_answer.strip()
    if sa in _EQUAL_WORDS:
        return "="
    if sa == left:
        return ">"
    if sa == right:
        return "<"
    try:  # fallback: compute directly
        lf, rf = _to_fraction(left), _to_fraction(right)
    except (ValueError, ZeroDivisionError):
        return None
    return ">" if lf > rf else ("<" if rf > lf else "=")


def grade_question(question: dict, child_answer: str) -> bool:
    """True if the child's raw answer is correct for this question."""
    child = (child_answer or "").strip()
    stored = (question.get("answer") or "").strip()
    qtype = question.get("type")

    if qtype == "fraction-comparison":
        correct = derive_symbol(question.get("exercise", ""), stored)
        tapped = "=" if child in _EQUAL_WORDS else child
        return correct is not None and tapped == correct

    if question.get("widget", "text") == "choice":
        return _norm_cat(child) == _norm_cat(stored)

    # text widget: numeric/fraction equivalence first, then categorical fallback
    if _numeric_equal(stored, child):
        return True
    return _norm_cat(child) == _norm_cat(stored)


def grade_payload(questions: list, payload: list) -> list:
    """Grade decoded `[[id,"answer"], …]` against `generated.json` questions.

    Omits blank `""` answers and ids not present in `questions`. Returns a list
    of per-question dicts with grading + display fields.
    """
    qmap = {q["id"]: q for q in questions}
    graded = []
    for entry in payload:
        qid, ans = entry[0], entry[1]
        if ans == "":
            continue  # rendered-but-unanswered → not counted
        q = qmap.get(qid)
        if q is None:
            continue  # excluded/absent id → not counted
        graded.append({
            "id": qid,
            "type": q.get("type"),
            "description": q.get("description", ""),
            "exercise": q.get("exercise", ""),
            "stored": q.get("answer", ""),
            "child": ans,
            "correct": grade_question(q, ans),
        })
    return graded


def to_results(graded: list) -> list:
    """Project graded entries to the `results.json` shape `[{id,correct,note}]`.

    Records the child's raw decoded answer as the note (with the expected answer
    for wrong ones) since no human is present to describe the mistake.
    """
    results = []
    for g in graded:
        if g["correct"]:
            note = f"answered '{g['child']}'"
        else:
            note = f"answered '{g['child']}' (expected {g['stored']})"
        results.append({"id": g["id"], "correct": g["correct"], "note": note})
    return results
