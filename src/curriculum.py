"""Curriculum model and deterministic question template engine."""

import random
from fractions import Fraction as Frac

# ─── Topic tree (from kita4 curriculum) ──────────────────────────────────────

TOPICS = {
    "multiplication-table":  {"name": "Multiplication Table",    "hours": 10},
    "addition":               {"name": "Addition",               "hours": 12},
    "subtraction":            {"name": "Subtraction",            "hours": 12},
    "multiplication":         {"name": "Multiplication",         "hours": 12},
    "division":               {"name": "Division",               "hours": 14},
    "order-of-operations":    {"name": "Order of Operations",    "hours":  8},
    "prime-composite":        {"name": "Prime & Composite",      "hours":  5},
    "divisibility":           {"name": "Divisibility Rules",     "hours":  5},
    "fraction-comparison":    {"name": "Fraction Comparison",    "hours":  8},
    "fraction-addition":      {"name": "Fraction Addition",      "hours":  8},
    "fraction-subtraction":   {"name": "Fraction Subtraction",  "hours":  7},
    "measurements-area":      {"name": "Area",                   "hours":  6},
    "measurements-perimeter": {"name": "Perimeter",              "hours":  5},
    "exponents":              {"name": "Exponents",              "hours":  3},
    "natural-numbers":        {"name": "Natural Numbers",        "hours": 10},
    "arithmetic-sequences":   {"name": "Arithmetic Sequences",   "hours":  6},
    "multiplication-by-tens": {"name": "Multiplication by Tens", "hours":  4},
    "equations-unknown":      {"name": "Equations with Unknown", "hours":  6},
    # Claude-only topics:
    "word-problems":          {"name": "Word Problems",          "hours": 12},
    "geometry":               {"name": "Geometry",               "hours": 15},
    "probability":            {"name": "Probability",            "hours":  8},
    "symmetry":               {"name": "Symmetry",               "hours":  4},
}

CLAUDE_TOPICS = {"word-problems", "geometry", "probability", "symmetry"}
TEMPLATE_TOPICS = {k for k in TOPICS if k not in CLAUDE_TOPICS}

# Block headers for WhatsApp output
BLOCK_HEADERS = {
    "multiplication-table":  "Warmup - Multiplication Table",
    "addition":               "Addition",
    "subtraction":            "Subtraction",
    "multiplication":         "Multiplication",
    "division":               "Division",
    "order-of-operations":    "Order of Operations",
    "prime-composite":        "Prime & Composite Numbers",
    "divisibility":           "Divisibility Rules",
    "fraction-comparison":    "Fraction Comparison",
    "fraction-addition":      "Fraction Addition",
    "fraction-subtraction":   "Fraction Subtraction",
    "measurements-area":      "Area",
    "measurements-perimeter": "Perimeter",
    "exponents":              "Exponents",
    "natural-numbers":        "Natural Numbers",
    "arithmetic-sequences":   "Arithmetic Sequences",
    "multiplication-by-tens": "Multiplication by Tens",
    "equations-unknown":      "Equations with Unknown",
    "word-problems":          "Word Problems",
    "geometry":               "Geometry",
    "probability":            "Probability",
    "symmetry":               "Symmetry",
}

# ─── 55 unique multiplication facts (1×1 through 10×10, a ≤ b) ───────────────

MULTIPLICATION_FACTS = [
    (a, b) for a in range(1, 11) for b in range(a, 11)
]  # exactly 55 facts

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _q(desc: str, exercise: str, answer, answer_type: str, qtype: str, sig: str) -> dict:
    return {
        "description": desc,
        "exercise": exercise,
        "answer": str(answer),
        "answer_type": answer_type,
        "type": qtype,
        "subtopic": qtype,
        "signature": sig,
    }


def _frac_str(f: Frac) -> str:
    """Format a Fraction as a Hebrew-friendly string (mixed number if > 1)."""
    if f.denominator == 1:
        return str(f.numerator)
    if f.numerator > f.denominator:
        whole = f.numerator // f.denominator
        rem = f.numerator % f.denominator
        if rem == 0:
            return str(whole)
        return f"{whole} ו-{rem}/{f.denominator}"
    return f"{f.numerator}/{f.denominator}"


def _frac_str_raw(num: int, denom: int) -> str:
    """Format num/denom WITHOUT reducing.

    Grade 4 does not reduce fractions (reduction is a grade-5 skill), so answers
    keep the grade-4-natural denominator: 1/4 + 1/4 → "2/4", not "1/2".
    Exact whole results collapse to the integer (6/6 → "1"); /results accepts
    the equivalent unreduced form.
    """
    if num % denom == 0:
        return str(num // denom)
    if num > denom:
        whole = num // denom
        rem = num % denom
        return f"{whole} ו-{rem}/{denom}"
    return f"{num}/{denom}"


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _prime_factors(n: int) -> list:
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


# ─── Individual question generators ──────────────────────────────────────────

def _mult_table(difficulty: str) -> dict:
    pools = {
        "easy":   [(a, b) for a, b in MULTIPLICATION_FACTS if a <= 5 and b <= 5],
        "medium": [(a, b) for a, b in MULTIPLICATION_FACTS if a <= 8],
        "hard":   MULTIPLICATION_FACTS,
    }
    a, b = random.choice(pools.get(difficulty, pools["medium"]))
    result = a * b
    choice = random.randint(0, 5)
    if choice == 0:
        return _q("מה המספר החסר?", f"{a} × ___ = {result}", b, "numeric", "multiplication-table", f"mult:{a}×{b}")
    if choice == 1:
        return _q("מה המספר החסר?", f"{result} = ___ × {b}", a, "numeric", "multiplication-table", f"mult:{a}×{b}")
    desc = random.choice([
        "כמה זה:",
        "מה המכפלה?",
        "חשב/י:",
        "חשב/י את המכפלה:",
    ])
    return _q(desc, f"{a} × {b} =", result, "numeric", "multiplication-table", f"mult:{a}×{b}")


def _addition(difficulty: str) -> dict:
    if difficulty == "easy":
        a, b = random.randint(10, 99), random.randint(10, 99)
    elif difficulty == "hard":
        a, b = random.randint(1000, 9999), random.randint(1000, 9999)
    else:
        a, b = random.randint(100, 999), random.randint(100, 999)
    desc = random.choice([
        "חשב/י:",
        "מה הסכום?",
        "חבר/י:",
    ])
    return _q(desc, f"{a} + {b} =", a + b, "numeric", "addition", f"add:{a}+{b}")


def _subtraction(difficulty: str) -> dict:
    if difficulty == "easy":
        b = random.randint(10, 90)
        a = random.randint(b + 5, b + 90)
    elif difficulty == "hard":
        b = random.randint(1000, 4999)
        a = random.randint(b + 1000, b + 5000)
    else:
        b = random.randint(100, 499)
        a = random.randint(b + 100, b + 900)
    desc = random.choice([
        "חשב/י:",
        "מה ההפרש?",
    ])
    return _q(desc, f"{a} - {b} =", a - b, "numeric", "subtraction", f"sub:{a}-{b}")


def _multiplication(difficulty: str) -> dict:
    if difficulty == "easy":
        a, b = random.randint(2, 9), random.randint(10, 99)
    elif difficulty == "hard":
        a, b = random.randint(10, 99), random.randint(100, 999)
    else:
        a, b = random.randint(11, 49), random.randint(11, 49)
    desc = random.choice([
        "חשב/י:",
        "מה המכפלה?",
    ])
    return _q(desc, f"{a} × {b} =", a * b, "numeric", "multiplication", f"mult-long:{a}×{b}")


def _division(difficulty: str) -> dict:
    if difficulty == "easy":
        b = random.randint(2, 9)
        result = random.randint(2, 10)
        a = b * result
        desc = random.choice(["חשב/י:", "חלק/י:"])
        return _q(desc, f"{a} ÷ {b} =", result, "numeric", "division", f"div:{a}÷{b}")
    if difficulty == "hard":
        # advanced grade-4 (L255, L286): whole-tens divisor (e.g. 840 ÷ 20),
        # or single-digit divisor with remainder. Dividend kept within grade-4 range.
        if random.random() < 0.5:
            b = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90])
            q = random.randint(3, min(45, 900 // b))
            r = random.randint(0, b - 1)
            a = b * q + r
            if r == 0:
                desc = random.choice(["חשב/י:", "חלק/י:"])
                return _q(desc, f"{a} ÷ {b} =", q, "numeric", "division", f"div:{a}÷{b}")
            return _q("מנה ושארית:", f"{a} ÷ {b} =", f"{q} שארית {r}", "numeric", "division", f"div:{a}÷{b}")
        b = random.randint(2, 9)
        q = random.randint(10, 99)
        r = random.randint(1, b - 1)
        a = b * q + r
        return _q("מנה ושארית:", f"{a} ÷ {b} =", f"{q} שארית {r}", "numeric", "division", f"div:{a}÷{b}")
    # medium: single-digit divisor, larger dividend, ~40% with remainder (L256, L728)
    b = random.randint(2, 9)
    if random.random() < 0.4:
        q = random.randint(10, 55)
        r = random.randint(1, b - 1)
        a = b * q + r
        return _q("מנה ושארית:", f"{a} ÷ {b} =", f"{q} שארית {r}", "numeric", "division", f"div:{a}÷{b}")
    result = random.randint(10, 55)
    a = b * result
    desc = random.choice(["חשב/י:", "חלק/י:"])
    return _q(desc, f"{a} ÷ {b} =", result, "numeric", "division", f"div:{a}÷{b}")


def _order_of_ops(difficulty: str) -> dict:
    # Invariants (all tiers): every ÷ is exactly divisible; result is a
    # non-negative integer (grade 4 has no negatives). ÷ enters at medium (L380).
    if difficulty == "easy":
        # ×-only, two ops, no brackets
        b = random.randint(2, 9)
        c = random.randint(2, 12)
        if random.random() < 0.5:
            a = random.randint(2, 20)
            expr = f"{a} + {b} × {c}"
            result = a + b * c
        else:
            a = random.randint(b * c, b * c + 30)  # a ≥ b×c keeps result ≥ 0
            expr = f"{a} - {b} × {c}"
            result = a - b * c
    elif difficulty == "hard":
        if random.random() < 0.5:
            # (a + b) × c - d ÷ e
            a = random.randint(5, 30); b = random.randint(5, 20); c = random.randint(2, 9)
            e = random.randint(2, 9); q = random.randint(2, 9); d = e * q
            expr = f"({a} + {b}) × {c} - {d} ÷ {e}"
            result = (a + b) * c - q  # (a+b)×c ≥ 20 > q ≤ 9
        else:
            # a × b - c ÷ d
            a = random.randint(5, 20); b = random.randint(3, 9)
            d = random.randint(2, 9); qq = random.randint(2, 9); c = d * qq
            expr = f"{a} × {b} - {c} ÷ {d}"
            result = a * b - qq  # a×b ≥ 15 > qq ≤ 9
    else:
        pick = random.randint(0, 2)
        if pick == 0:
            c = random.randint(2, 12)
            a = random.randint(5, 50)
            b = random.randint(2, a - 1)
            expr = f"({a} - {b}) × {c}"
            result = (a - b) * c
        elif pick == 1:
            a = random.randint(5, 30); b = random.randint(2, 9); c = random.randint(2, 30)
            expr = f"{a} × {b} + {c}"
            result = a * b + c
        else:
            # a + b ÷ c  (÷-before-+, exact)
            c = random.randint(2, 9); q = random.randint(2, 12); b = c * q
            a = random.randint(2, 40)
            expr = f"{a} + {b} ÷ {c}"
            result = a + q
    desc = random.choice([
        "חשב/י לפי סדר הפעולות:",
        "מה תוצאת הביטוי?",
        "פתור/י:",
    ])
    return _q(desc, f"{expr} =", result, "numeric", "order-of-operations", f"orderops:{expr}")


def _prime_composite(difficulty: str) -> dict:
    if difficulty == "easy":
        pool = list(range(2, 21))
    elif difficulty == "hard":
        pool = list(range(2, 101))
    else:
        pool = list(range(2, 51))
    n = random.choice(pool)
    is_p = _is_prime(n)
    if not is_p and random.random() < 0.4:
        factors = _prime_factors(n)
        factor_str = " × ".join(map(str, factors))
        return _q("פרק/י לגורמים ראשוניים:", str(n), factor_str, "categorical", "prime-composite", f"prime:{n}")
    answer = "ראשוני" if is_p else "פריק"
    desc = random.choice([
        "ראשוני או פריק?",
        "בדוק/י: ראשוני או פריק?",
    ])
    return _q(desc, str(n), answer, "categorical", "prime-composite", f"prime:{n}")


def _divisibility(difficulty: str) -> dict:
    # Taught divisibility rules are 3, 6, 9 (L441-443); divisor 2 is prior knowledge.
    d_pools = {
        "easy":   [3],
        "medium": [3, 6, 9],
        "hard":   [3, 6, 9],
    }
    d = random.choice(d_pools.get(difficulty, d_pools["medium"]))
    n_ranges = {"easy": (10, 60), "medium": (20, 200), "hard": (100, 999)}
    lo, hi = n_ranges.get(difficulty, (20, 200))
    n = random.randint(lo, hi)
    answer = "כן" if n % d == 0 else "לא"
    return _q("האם מתחלק? (כן/לא)", f"{n} ÷ {d}", answer, "categorical", "divisibility", f"divides:{d}|{n}")


# Valid denominator pairs for grade 4 fraction operations.
# Tiers are DISJOINT pair sets (provably distinct): easy = equal denominators,
# medium = simple related pairs, hard = larger related pairs. All denominators ∈
# the familiar set {2,3,4,5,6,8,10}; every (d1,d2) has d2 % d1 == 0 so addition/
# subtraction need only intuitive equivalent-name renaming (no grade-5 algorithm).
# Hard is ALSO differentiated by question shape (mixed-number results / missing
# number), handled in the generators below.
_DENOM_PAIRS = {
    "easy":   [(2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (8, 8), (10, 10)],
    "medium": [(2, 4), (2, 6), (3, 6), (4, 8)],
    "hard":   [(2, 8), (2, 10), (5, 10)],
}


def _fraction_comparison(difficulty: str) -> dict:
    # Intuitive strategies only — NO common-denominator / cross-multiply algorithm
    # (grade 5, L64/L132). Familiar denominators only: F = {2,3,4,5,6,8,10}.
    F = [2, 3, 4, 5, 6, 8, 10]
    if difficulty == "easy":
        # equal denominators — compare numerators (L718). Exclude d=2: with only
        # one proper numerator (1) you cannot form two distinct fractions.
        d = random.choice([x for x in F if x >= 3])
        a, b = random.sample(range(1, d), 2)
        d1, d2 = d, d
    elif difficulty == "medium":
        # equal numerators, different denominators — bigger denom = smaller piece (L76)
        d1, d2 = random.sample(F, 2)
        n = random.randint(1, min(d1, d2) - 1)
        a, b = n, n
    else:
        # hard: related denominators (d2 % d1 == 0), renaming required (L57-61);
        # at least one non-unit numerator so it isn't a trivial unit-fraction compare.
        related = [(2, 4), (2, 6), (2, 8), (2, 10), (3, 6), (4, 8), (5, 10)]
        for _ in range(20):
            d1, d2 = random.choice(related)
            a = random.randint(1, d1 - 1)
            b = random.randint(1, d2 - 1)
            if a > 1 or b > 1:
                break

    v1, v2 = Frac(a, d1), Frac(b, d2)
    if v1 > v2:
        answer = f"{a}/{d1}"
    elif v2 > v1:
        answer = f"{b}/{d2}"
    else:
        answer = "שווים"

    desc = random.choice([
        "סמני > או < או =",
        "איזה שבר גדול יותר?",
        "השווי:",
    ])
    return _q(desc, f"{a}/{d1} ___ {b}/{d2}", answer, "categorical", "fraction-comparison",
              f"frac-cmp:{a}/{d1}vs{b}/{d2}")


def _fraction_addition(difficulty: str) -> dict:
    d1, d2 = random.choice(_DENOM_PAIRS.get(difficulty, _DENOM_PAIRS["medium"]))
    k = d2 // d1  # common denominator is d2 (the multiple); keep answers unreduced

    if difficulty == "hard" and random.random() < 0.5:
        # missing-addend (intuitive, L102-105): ___ + b/d2 = total/d2
        total = random.randint(2, d2)
        b = random.randint(1, total - 1)
        blank = total - b
        ans = _frac_str_raw(blank, d2)
        return _q("מה השבר החסר?", f"___ + {b}/{d2} = {_frac_str_raw(total, d2)}",
                  ans, "numeric", "fraction-addition",
                  f"frac-add-missing:?+{b}/{d2}={total}/{d2}")

    a = random.randint(1, d1)
    b = random.randint(1, d2)
    num = a * k + b  # in denominator d2, unreduced (mixed number when > d2)
    ans = _frac_str_raw(num, d2)
    desc = random.choice(["חשב/י:", "מה הסכום?", "חבר/י שברים:"])
    return _q(desc, f"{a}/{d1} + {b}/{d2} =", ans, "numeric", "fraction-addition",
              f"frac-add:{a}/{d1}+{b}/{d2}")


def _fraction_subtraction(difficulty: str) -> dict:
    d1, d2 = random.choice(_DENOM_PAIRS.get(difficulty, _DENOM_PAIRS["medium"]))
    k = d2 // d1

    if difficulty == "hard":
        shape = random.randint(0, 2)
        if shape == 0:
            # whole minus fraction (L121-123): W - b/d2, unreduced
            W = random.randint(1, 2)
            b = random.randint(1, d2 - 1)
            ans = _frac_str_raw(W * d2 - b, d2)
            return _q("חשב/י:", f"{W} - {b}/{d2} =", ans, "numeric", "fraction-subtraction",
                      f"frac-sub:{W}-{b}/{d2}")
        if shape == 1:
            # missing-number: ___ - b/d2 = r/d2  → blank = (r+b)/d2
            r = random.randint(1, d2 - 1)
            b = random.randint(1, d2 - 1)
            blank = r + b
            ans = _frac_str_raw(blank, d2)
            return _q("מה השבר החסר?", f"___ - {b}/{d2} = {_frac_str_raw(r, d2)}",
                      ans, "numeric", "fraction-subtraction",
                      f"frac-sub-missing:?-{b}/{d2}={r}/{d2}")
        # shape 2 falls through to standard (with the harder denominator pairs)

    # standard subtraction, result >= 0, unreduced in denominator d2
    for _ in range(20):
        a = random.randint(1, d1)
        b = random.randint(1, d2)
        if a * k >= b:
            break
    else:
        a, b = d1, 1
    ans = _frac_str_raw(a * k - b, d2)
    desc = random.choice(["חשב/י:", "מה ההפרש?"])
    return _q(desc, f"{a}/{d1} - {b}/{d2} =", ans, "numeric", "fraction-subtraction",
              f"frac-sub:{a}/{d1}-{b}/{d2}")


def _measurements_area(difficulty: str) -> dict:
    if difficulty == "easy":
        l, w = random.randint(2, 9), random.randint(2, 9)
    elif difficulty == "hard":
        l, w = random.randint(10, 50), random.randint(10, 50)
    else:
        l, w = random.randint(5, 20), random.randint(2, 9)
    unit = random.choice(["ס\"מ", "מ'"])
    unit_sq = "סמ\"ר" if unit == "ס\"מ" else "מ\"ר"
    desc = random.choice([
        f"מה שטח המלבן? (אורך {l} {unit}, רוחב {w} {unit})",
        f"חשב/י שטח מלבן: אורך {l} {unit}, רוחב {w} {unit}",
    ])
    return _q(desc, f"{l} × {w} =", f"{l * w} {unit_sq}", "numeric", "measurements-area",
              f"area:{l}×{w}")


def _measurements_perimeter(difficulty: str) -> dict:
    if difficulty == "easy":
        l, w = random.randint(2, 9), random.randint(2, 9)
    elif difficulty == "hard":
        l, w = random.randint(15, 50), random.randint(15, 50)
    else:
        l, w = random.randint(5, 20), random.randint(2, 9)
    unit = random.choice(["ס\"מ", "מ'"])
    desc = random.choice([
        f"מה היקף המלבן? (אורך {l} {unit}, רוחב {w} {unit})",
        f"חשב/י היקף מלבן: אורך {l} {unit}, רוחב {w} {unit}",
    ])
    return _q(desc, f"2 × ({l} + {w}) =", f"{2 * (l + w)} {unit}", "numeric", "measurements-perimeter",
              f"perim:{l}×{w}")


def _exponents(difficulty: str) -> dict:
    # Introductory notation topic (L463); exp ≤ 3. Hard adds conceptual variety
    # (inverse, commutativity-check) per L468/L474, not bigger magnitudes.
    desc_fwd = ["חשב/י:", "מה הערך?"]
    if difficulty == "easy":
        base = random.choice([2, 3]); exp = random.choice([2, 3])
        return _q(random.choice(desc_fwd), f"{base}^{exp} =", base ** exp,
                  "numeric", "exponents", f"exp:{base}^{exp}")
    if difficulty == "medium":
        base = random.choice([2, 3, 4, 5]); exp = random.choice([2, 3])
        return _q(random.choice(desc_fwd), f"{base}^{exp} =", base ** exp,
                  "numeric", "exponents", f"exp:{base}^{exp}")

    # hard: forward (base up to 10) | inverse | commutativity-check
    shape = random.randint(0, 2)
    if shape == 0:
        base = random.choice([2, 3, 4, 5, 10]); exp = random.choice([2, 3])
        return _q(random.choice(desc_fwd), f"{base}^{exp} =", base ** exp,
                  "numeric", "exponents", f"exp:{base}^{exp}")
    if shape == 1:
        # inverse: write N as a power — N constrained to a UNIQUE base≥2/exp≥2 form
        base, exp = random.choice([(2, 3), (3, 3), (5, 2), (5, 3), (7, 2)])
        n = base ** exp
        return _q("כתוב/י כחזקה:", f"{n} =", f"{base}^{exp}",
                  "categorical", "exponents", f"exp-inverse:{n}")
    # commutativity check: is a^b = b^a? include the equality case 2^4=4^2 sometimes
    if random.random() < 0.3:
        a, b = 2, 4
    else:
        a = random.choice([2, 3, 4, 5]); b = random.choice([2, 3, 4, 5])
        while a == b or {a, b} == {2, 4}:
            b = random.choice([2, 3, 4, 5])
    answer = "כן" if a ** b == b ** a else "לא"
    return _q("האם שווה? (כן/לא)", f"{a}^{b} = {b}^{a}", answer,
              "categorical", "exponents", f"exp-cmp:{a}^{b}vs{b}^{a}")


def _equations_unknown(difficulty: str) -> dict:
    """פעולות חשבון עם נעלם אחד — one unknown on either side."""
    op = random.choice(["add", "sub", "mul", "div"])
    if difficulty == "easy":
        if op == "add":
            b = random.randint(1, 20); result = random.randint(b + 1, b + 20)
            a = result - b
            return _q("מה הנעלם?", f"___ + {b} = {result}", a, "numeric", "equations-unknown", f"eq:x+{b}={result}")
        if op == "sub":
            b = random.randint(1, 20); a = random.randint(b + 1, b + 20)
            return _q("מה הנעלם?", f"{a} - ___ = {a - b}", b, "numeric", "equations-unknown", f"eq:{a}-x={a-b}")
        if op == "mul":
            b = random.randint(2, 5); result = b * random.randint(2, 9)
            a = result // b
            return _q("מה הנעלם?", f"___ × {b} = {result}", a, "numeric", "equations-unknown", f"eq:x×{b}={result}")
        b = random.randint(2, 5); a = b * random.randint(2, 9)
        return _q("מה הנעלם?", f"{a} ÷ ___ = {a // b}", b, "numeric", "equations-unknown", f"eq:{a}÷x={a//b}")
    if difficulty == "hard":
        if op == "add":
            b = random.randint(50, 500); result = random.randint(b + 100, b + 500)
            a = result - b
            return _q("מה הנעלם?", f"___ + {b} = {result}", a, "numeric", "equations-unknown", f"eq:x+{b}={result}")
        if op == "sub":
            b = random.randint(100, 500); a = random.randint(b + 100, b + 500)
            return _q("מה הנעלם?", f"{a} - ___ = {a - b}", b, "numeric", "equations-unknown", f"eq:{a}-x={a-b}")
        if op == "mul":
            b = random.randint(6, 9); result = b * random.randint(10, 20)
            a = result // b
            return _q("מה הנעלם?", f"___ × {b} = {result}", a, "numeric", "equations-unknown", f"eq:x×{b}={result}")
        b = random.randint(6, 9); a = b * random.randint(10, 20)
        return _q("מה הנעלם?", f"{a} ÷ ___ = {a // b}", b, "numeric", "equations-unknown", f"eq:{a}÷x={a//b}")
    # medium
    if op == "add":
        b = random.randint(10, 100); result = random.randint(b + 10, b + 200)
        a = result - b
        return _q("מה הנעלם?", f"___ + {b} = {result}", a, "numeric", "equations-unknown", f"eq:x+{b}={result}")
    if op == "sub":
        b = random.randint(10, 100); a = random.randint(b + 10, b + 200)
        return _q("מה הנעלם?", f"{a} - ___ = {a - b}", b, "numeric", "equations-unknown", f"eq:{a}-x={a-b}")
    if op == "mul":
        b = random.randint(3, 9); result = b * random.randint(5, 12)
        a = result // b
        return _q("מה הנעלם?", f"___ × {b} = {result}", a, "numeric", "equations-unknown", f"eq:x×{b}={result}")
    b = random.randint(3, 9); a = b * random.randint(5, 12)
    return _q("מה הנעלם?", f"{a} ÷ ___ = {a // b}", b, "numeric", "equations-unknown", f"eq:{a}÷x={a//b}")


def _multiplication_by_tens(difficulty: str) -> dict:
    """כפל באפסים — multiplying by 10, 100, 1000 or multiples thereof."""
    # Whole tens and whole hundreds only (L223) — no thousands.
    if difficulty == "easy":
        a = random.randint(2, 9)
        b = random.choice([10, 100])
    elif difficulty == "hard":
        a = random.randint(12, 99)
        b = random.choice([100, 200, 300, 400, 500, 600, 700, 800, 900])
    else:
        a = random.randint(2, 99)
        b = random.choice([10, 20, 30, 40, 50, 100, 200, 300])
    desc = random.choice([
        "חשב/י:",
        "מה המכפלה?",
        "כפול/י:",
    ])
    return _q(desc, f"{a} × {b} =", a * b, "numeric", "multiplication-by-tens",
              f"mult-tens:{a}×{b}")


def _arithmetic_sequences(difficulty: str) -> dict:
    # Number-sense / skip-counting enrichment. Not a named kita4 topic, but grounded
    # in the first-class number-sense strand ד.4 (L323-332, L763): steps are
    # constrained to 2-10 so every sequence rehearses a multiplication-table fact
    # (counting by 7s drills the 7× facts), directly serving the app's core mission.
    if difficulty == "easy":
        start = random.randint(1, 20)
        step = random.randint(2, 10)
        length = 5
    elif difficulty == "hard":
        start = random.randint(10, 100)
        step = random.randint(2, 10)
        length = 6
    else:
        start = random.randint(1, 50)
        step = random.randint(2, 10)
        length = 5

    seq = [start + step * i for i in range(length)]
    question_type = random.randint(0, 2)

    if question_type == 0:
        # Find the next term
        shown = seq[:-1]
        answer = seq[-1]
        exercise = ", ".join(str(x) for x in shown) + ", ___"
        desc = "מה המספר הבא בסדרה?"
    elif question_type == 1:
        # Fill in a missing middle term
        missing_idx = random.randint(1, length - 2)
        shown = seq[:]
        answer = shown[missing_idx]
        shown[missing_idx] = "___"
        exercise = ", ".join(str(x) for x in shown)
        desc = "מה המספר החסר בסדרה?"
    else:
        # Find the rule (common difference)
        shown = seq[:4]
        answer = seq[4] if length > 4 else seq[-1]
        exercise = ", ".join(str(x) for x in shown) + ", ___"
        desc = f"מה הכלל? (+{step}) — מה המספר הבא?"

    sig = f"seq:{start}+{step}x{length}-q{question_type}"
    return _q(desc, exercise, answer, "numeric", "arithmetic-sequences", sig)


def _natural_numbers(difficulty: str) -> dict:
    if difficulty == "easy":
        n = random.randint(1001, 9999)
    elif difficulty == "hard":
        n = random.randint(100001, 999999)
    else:
        n = random.randint(10001, 99999)
    # Ask about place value of a specific digit
    digits = [("האחדות", 0), ("העשרות", 1), ("המאות", 2), ("האלפים", 3),
              ("עשרות האלפים", 4), ("מאות האלפים", 5)]
    max_pos = len(str(n)) - 1
    pos_name, pos = random.choice(digits[:max_pos + 1])
    digit_val = (n // (10 ** pos)) % 10
    desc = random.choice([
        f"מהי ספרת {pos_name}?",
        f"מה ערך ספרת {pos_name}?",
    ])
    return _q(desc, f"{n:,}", digit_val, "numeric", "natural-numbers",
              f"natnum:{n}-pos{pos}")


# ─── Public API ──────────────────────────────────────────────────────────────

_GENERATORS = {
    "multiplication-table":  _mult_table,
    "addition":               _addition,
    "subtraction":            _subtraction,
    "multiplication":         _multiplication,
    "division":               _division,
    "order-of-operations":    _order_of_ops,
    "prime-composite":        _prime_composite,
    "divisibility":           _divisibility,
    "fraction-comparison":    _fraction_comparison,
    "fraction-addition":      _fraction_addition,
    "fraction-subtraction":   _fraction_subtraction,
    "measurements-area":      _measurements_area,
    "measurements-perimeter": _measurements_perimeter,
    "exponents":              _exponents,
    "natural-numbers":        _natural_numbers,
    "arithmetic-sequences":   _arithmetic_sequences,
    "multiplication-by-tens": _multiplication_by_tens,
    "equations-unknown":      _equations_unknown,
}


def make_question(qtype: str, difficulty: str = "medium") -> dict:
    """Generate one question for the given type and difficulty.

    Returns dict: {description, exercise, answer, answer_type, type, subtopic, signature}
    Raises ValueError for unknown types or Claude-only types.
    """
    if qtype in CLAUDE_TOPICS:
        raise ValueError(f"{qtype!r} requires Claude — use generator.py fallback")
    if qtype not in _GENERATORS:
        raise ValueError(f"Unknown question type: {qtype!r}")
    return _GENERATORS[qtype](difficulty)
