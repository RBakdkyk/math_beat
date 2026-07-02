#!/usr/bin/env python3
"""Quiz round-trip codec + grading verification (stdlib only).

Run: python tests/test_quiz_roundtrip.py

Covers the verification section of the quiz-roundtrip change that does not need
the full wiki/analyze pipeline: codec checksum + tolerant extraction, blank-skip,
number normalization, unit-stripping, comparison-symbol derivation, corrupt /
unknown-date rejection, and the percent-encode round-trip for base64 +/.

Imports only `codec` and `grading` (both stdlib-pure) so it runs on Python 3.9+;
the rest of the codebase targets 3.10+.
"""

import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from codec import encode, decode, extract, check_char, CodeError  # noqa: E402
from grading import grade_payload, to_results, derive_symbol, normalize_number  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ── 2.3 / recovered codes: check chars j, 3, 9 ───────────────────────────────
RECOVERED = {
    "2026-06-08": ([[1, "7"], [2, "100"], [3, "25"], [4, "1720"], [5, "24300"],
                    [6, "868"], [7, "256"], [8, "54"]], "j"),
    "2026-06-03": ([[1, "65"], [2, "54"], [3, "35"], [4, ""], [5, ""],
                    [6, "44"], [7, "44"], [8, "1"]], "3"),
    "2026-06-01": ([[1, "70"], [2, "5"], [3, "381,"], [4, "1,038"], [5, "151"],
                    [6, "52.1"], [7, ">"], [8, "40/32"]], "9"),
}
for date, (payload, expected_check) in RECOVERED.items():
    code = encode(date, payload)
    check(code.rsplit("~", 1)[1] == expected_check,
          f"recovered {date}: check char != {expected_check} ({code})")
    d2, p2 = decode(code)
    check(d2 == date and p2 == payload, f"recovered {date}: round-trip mismatch")

# Tolerant extraction inside surrounding text/emoji
emb = "done! " + encode("2026-06-08", RECOVERED["2026-06-08"][0]) + " 🎉"
check(extract(emb) is not None, "extract: failed to anchor on AYL~ in surrounding text")
check(decode(emb)[0] == "2026-06-08", "extract: embedded code did not decode")


# ── 6.5 corrupt + unknown-date rejection ─────────────────────────────────────
good = encode("2026-06-08", RECOVERED["2026-06-08"][0])
corrupt = good[:-1] + ("z" if good[-1] != "z" else "y")  # flip the check char
try:
    decode(corrupt)
    check(False, "corrupt code: decode should have raised")
except CodeError:
    pass
check(extract("no code here at all") is None, "extract: false positive on plain text")
# Unknown date is a pipeline-level concern (no generated.json); the envelope still
# decodes — confirm the date is surfaced for the caller to reject.
unknown = encode("1999-01-01", [[1, "5"]])
check(decode(unknown)[0] == "1999-01-01", "unknown-date code should still decode its date")


# ── 6.7 percent-encode round-trip for base64 +/ ──────────────────────────────
# Find a payload whose base64 contains + or /, then simulate the wa.me text param.
plus_slash = None
for ans in (">", "?>", ">>", "~?", "<?>", "abc?>~"):
    cand = encode("2026-06-09", [[1, ans]])
    if "+" in cand or "/" in cand:
        plus_slash = cand
        break
check(plus_slash is not None, "could not construct a code containing base64 +//")
if plus_slash:
    text_param = urllib.parse.quote(plus_slash)  # encodeURIComponent equivalent
    check("%2B" in text_param or "%2F" in text_param, "percent-encode: +// not escaped")
    received = urllib.parse.unquote(text_param)   # what the pasted text resolves to
    check(decode(received)[0] == "2026-06-09", "percent-encode: code did not round-trip")


# ── 6.4 comparison-symbol derivation ─────────────────────────────────────────
check(derive_symbol("1/5 ___ 5/8", "5/8") == "<", "derive: 1/5 ___ 5/8 (ans 5/8) != <")
check(derive_symbol("5/8 ___ 1/5", "5/8") == ">", "derive: 5/8 ___ 1/5 (ans 5/8) != >")
check(derive_symbol("2/4 ___ 1/2", "שווים") == "=", "derive: equal fractions != =")

cmp_qs = [
    {"id": 1, "type": "fraction-comparison", "exercise": "1/5 ___ 5/8", "answer": "5/8", "widget": "choice"},
    {"id": 2, "type": "fraction-comparison", "exercise": "2/4 ___ 1/2", "answer": "שווים", "widget": "choice"},
]
g = grade_payload(cmp_qs, [[1, ">"], [2, "="]])
check(g[0]["correct"] is False, "comparison: tapped > vs derived < should be wrong")
check(g[1]["correct"] is True, "comparison: tapped = vs derived = should be correct")
g2 = grade_payload([cmp_qs[0]], [[1, "<"]])
check(g2[0]["correct"] is True, "comparison: tapped < vs derived < should be correct")


# ── 6.3 normalization + unit-stripping ───────────────────────────────────────
check(normalize_number("1,038") == "1038", "normalize: thousands separator")
check(normalize_number("381,") == "381", "normalize: trailing comma")
norm_qs = [
    {"id": 1, "type": "measurements-area", "exercise": "19 × 13 =", "answer": '247 מ"ר', "widget": "text"},
    {"id": 2, "type": "addition", "exercise": "x =", "answer": "1038", "widget": "text"},
    {"id": 3, "type": "addition", "exercise": "x =", "answer": "381", "widget": "text"},
]
gn = grade_payload(norm_qs, [[1, "247"], [2, "1,038"], [3, "381,"]])
check(all(e["correct"] for e in gn), f"normalization grading failed: {gn}")


# ── 6.2 blank-skip + absent id ───────────────────────────────────────────────
blank_qs = [{"id": i, "type": "addition", "exercise": "x =", "answer": str(i), "widget": "text"}
            for i in range(1, 9)]
payload = [[1, "1"], [2, "2"], [3, "3"], [4, ""], [5, ""], [6, "6"], [7, "7"], [8, "8"]]
gb = grade_payload(blank_qs, payload)
ids = {e["id"] for e in gb}
check(4 not in ids and 5 not in ids, "blank-skip: ids 4,5 should be omitted")
check(len(gb) == 6 and all(e["correct"] for e in gb), "blank-skip: other six should grade correct")
# absent id (not in generated.json) is dropped, not counted
ga = grade_payload(blank_qs, [[99, "x"], [1, "1"]])
check({e["id"] for e in ga} == {1}, "absent-id: id 99 should be dropped")


# ── 5.5 raw answer recorded as note ──────────────────────────────────────────
wrong_q = [{"id": 1, "type": "multiplication-table", "exercise": "7 × 8 =", "answer": "56", "widget": "text"}]
res = to_results(grade_payload(wrong_q, [[1, "54"]]))
check(res[0]["correct"] is False and "54" in res[0]["note"], "note: wrong raw answer not recorded")


# ── Grade a real session's generated.json (2026-05-27) by its own answer key ──
real_path = Path(__file__).resolve().parent.parent / "wiki" / "sessions" / "2026-05-27" / "generated.json"
if real_path.exists():
    real_qs = json.loads(real_path.read_text(encoding="utf-8"))
    # Build the "perfect" answers as the child would tap/type them.
    perfect = []
    for q in real_qs:
        if q["type"] == "fraction-comparison":
            perfect.append([q["id"], derive_symbol(q["exercise"], q["answer"])])
        elif q["type"].startswith("measurements"):
            perfect.append([q["id"], normalize_number(q["answer"]).split()[0]])  # number only
        else:
            perfect.append([q["id"], q["answer"]])
    gr = grade_payload(real_qs, perfect)
    bad = [e for e in gr if not e["correct"]]
    detail = ", ".join("id{}({} stored={} child={})".format(
        e["id"], e["exercise"], e["stored"], e["child"]) for e in bad)
    check(not bad, "real session 2026-05-27: perfect answers graded wrong: " + detail)
else:
    print("note: wiki/sessions/2026-05-27/generated.json missing — skipped real-session grading")


if _failures:
    print(f"FAIL ({len(_failures)})")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("All quiz round-trip checks passed.")
