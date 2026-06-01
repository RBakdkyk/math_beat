#!/usr/bin/env python3
"""Curriculum-band invariants for the template generators (stdlib only).

Run: python tests/test_bands.py

Calls make_question() DIRECTLY (not through generator._generate_template_question,
which swallows exceptions and would mask a broken band). Asserts the cross-cutting
invariants from the change design over many samples per (topic, tier).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from curriculum import (  # noqa: E402
    make_question, TEMPLATE_TOPICS, _DENOM_PAIRS, _frac_str_raw,
)

N = 400
FAMILIAR = {2, 3, 4, 5, 6, 8, 10}
TENS = {10, 20, 30, 40, 50, 60, 70, 80, 90}
_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def ints(s):
    return [int(x) for x in re.findall(r"\d+", s.replace(",", ""))]


def fracs(s):
    return [(int(n), int(d)) for n, d in re.findall(r"(\d+)\s*/\s*(\d+)", s)]


# ── 0. Smoke: every (topic, tier) generates N times with required keys ──────────
REQUIRED = {"description", "exercise", "answer", "answer_type", "type", "signature"}
for qtype in sorted(TEMPLATE_TOPICS):
    for tier in ("easy", "medium", "hard"):
        for _ in range(N):
            q = make_question(qtype, tier)
            check(REQUIRED <= set(q), f"{qtype}/{tier}: missing keys {REQUIRED - set(q)}")
            check(not re.search(r"[א-ת]", q["exercise"]),
                  f"{qtype}/{tier}: Hebrew in exercise {q['exercise']!r}")


# ── 1. Distinctness: fraction denominator-pair tiers are pairwise disjoint ──────
e, m, h = (set(_DENOM_PAIRS[t]) for t in ("easy", "medium", "hard"))
check(not (e & m) and not (m & h) and not (e & h),
      "_DENOM_PAIRS tiers are not disjoint")


# ── 2. Curriculum bounds, per topic ────────────────────────────────────────────
def sample(qtype, tier):
    return [make_question(qtype, tier) for _ in range(N)]


for tier in ("easy", "medium", "hard"):
    # multiplication: ≤ 2-digit × 3-digit; never 3-digit × 3-digit
    for q in sample("multiplication", tier):
        a, b = ints(q["exercise"])[:2]
        check(min(a, b) <= 99 and max(a, b) <= 999 and not (a >= 100 and b >= 100),
              f"multiplication/{tier}: out-of-range factors {a}×{b}")
    # addition / subtraction: operands ≤ 4-digit
    for qt in ("addition", "subtraction"):
        for q in sample(qt, tier):
            check(all(v <= 9999 for v in ints(q["exercise"])),
                  f"{qt}/{tier}: operand exceeds 4 digits in {q['exercise']!r}")
    # division: divisor ∈ {1..9} ∪ whole-tens
    for q in sample("division", tier):
        divisor = ints(q["exercise"])[1]
        check(1 <= divisor <= 9 or divisor in TENS,
              f"division/{tier}: bad divisor {divisor} in {q['exercise']!r}")
    # multiplication-by-tens: multiplier is whole tens/hundreds, no thousands
    for q in sample("multiplication-by-tens", tier):
        mult = ints(q["exercise"])[1]
        check(mult % 10 == 0 and mult <= 900,
              f"mult-by-tens/{tier}: bad multiplier {mult}")
    # divisibility: divisor ∈ {3,6,9}
    for q in sample("divisibility", tier):
        d = ints(q["exercise"])[1]
        check(d in (3, 6, 9), f"divisibility/{tier}: divisor {d} not in 3/6/9")
    # prime-composite: 2..100
    for q in sample("prime-composite", tier):
        check(2 <= ints(q["exercise"])[0] <= 100, f"prime-composite/{tier}: out of 2..100")
    # natural-numbers: ≤ one million
    for q in sample("natural-numbers", tier):
        check(ints(q["exercise"])[0] <= 1_000_000, f"natural-numbers/{tier}: > one million")
    # fraction comparison: familiar denoms, never unrelated
    for q in sample("fraction-comparison", tier):
        fs = fracs(q["exercise"])
        check(len(fs) == 2, f"fraction-comparison/{tier}: parse {q['exercise']!r}")
        if len(fs) == 2:
            (n1, d1), (n2, d2) = fs
            check(d1 in FAMILIAR and d2 in FAMILIAR,
                  f"fraction-comparison/{tier}: unfamiliar denom {d1},{d2}")
            # intuitive (no algorithm) iff equal denom, equal numerator, or related denom
            intuitive = d1 == d2 or n1 == n2 or d1 % d2 == 0 or d2 % d1 == 0
            check(intuitive,
                  f"fraction-comparison/{tier}: {n1}/{d1} vs {n2}/{d2} needs the algorithm")
    # fraction add/sub: all denominators familiar
    for qt in ("fraction-addition", "fraction-subtraction"):
        for q in sample(qt, tier):
            for _, d in fracs(q["exercise"]) + fracs(q["answer"]):
                check(d in FAMILIAR, f"{qt}/{tier}: unfamiliar denom {d} in {q}")
    # exponents: forward exp ≤ 3; inverse answer is a valid power; commutativity correct
    for q in sample("exponents", tier):
        sig = q["signature"]
        if sig.startswith("exp:"):
            base, exp = ints(q["exercise"])[:2]
            check(exp <= 3, f"exponents/{tier}: forward exp {exp} > 3")
            check(base ** exp == int(q["answer"]), f"exponents/{tier}: wrong value")
        elif sig.startswith("exp-inverse:"):
            n = ints(q["exercise"])[0]
            b, e2 = ints(q["answer"])[:2]
            check(b ** e2 == n and b >= 2 and e2 >= 2, f"exponents inverse: {q['answer']}≠{n}")
        elif sig.startswith("exp-cmp:"):
            a, b = ints(q["exercise"])[:2]
            expected = "כן" if a ** b == b ** a else "לא"
            check(q["answer"] == expected, f"exponents cmp: {q['exercise']} → {q['answer']}")
    # order-of-operations: no ÷ at easy; result is a non-negative integer matching eval
    for q in sample("order-of-operations", tier):
        ex = q["exercise"].rstrip(" =")
        if tier == "easy":
            check("÷" not in ex, f"order-of-ops/easy: ÷ present in {ex!r}")
        val = eval(ex.replace("×", "*").replace("÷", "/"), {"__builtins__": {}})
        check(val == int(q["answer"]) and val >= 0,
              f"order-of-ops/{tier}: {ex} = {val}, answer {q['answer']}")

# distinctness sanity: hard multiplication reaches 3-digit factors, easy never does
easy_max = max(max(ints(q["exercise"])[:2]) for q in sample("multiplication", "easy"))
hard_max = max(max(ints(q["exercise"])[:2]) for q in sample("multiplication", "hard"))
check(easy_max <= 99 < hard_max, f"multiplication tiers not distinct ({easy_max} vs {hard_max})")


# ── 3. Fraction answers are stored UNREDUCED ────────────────────────────────────
check(_frac_str_raw(2, 4) == "2/4", "_frac_str_raw(2,4) should be '2/4' not reduced")
check(_frac_str_raw(5, 6) == "5/6", "_frac_str_raw(5,6) wrong")
check(_frac_str_raw(6, 6) == "1", "_frac_str_raw(6,6) should be '1'")
check(_frac_str_raw(10, 6) == "1 ו-4/6", "_frac_str_raw(10,6) mixed-number wrong")


# ── report ──────────────────────────────────────────────────────────────────────
if _failures:
    print(f"FAIL — {len(_failures)} invariant violation(s):")
    for f in _failures[:40]:
        print("  -", f)
    sys.exit(1)
print(f"OK — all band invariants hold ({N} samples per topic/tier).")
