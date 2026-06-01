#!/usr/bin/env python3
"""Quiz HTML builder tests (stdlib only).

Run: python tests/test_quiz_builder.py

Covers change `add-html-quiz-layer`:
  - output is self-contained (no network references)
  - every question appears; no correct answers leak into the page
  - he-only legacy question renders with an input, not a blank
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quiz import build_quiz  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


QUESTIONS = [
    {"id": 1, "description": "חבר/י", "exercise": "57 + 87", "answer": "144",
     "answer_type": "numeric", "type": "addition", "subtopic": "addition",
     "signature": "add:57+87", "difficulty": "medium"},
    {"id": 2, "description": "האם ראשוני?", "exercise": "17", "answer": "ראשוני",
     "answer_type": "categorical", "type": "prime-composite", "subtopic": "prime-composite",
     "signature": "prime:17", "difficulty": "hard"},
    # Legacy he-only question (no description/exercise)
    {"id": 3, "he": "כמה זה 2×8?", "answer": "16", "answer_type": "numeric",
     "type": "multiplication-table", "subtopic": "multiplication-table",
     "signature": "mult:2×8", "difficulty": "easy"},
    # Fraction-comparison: must render tappable signs, not a text box
    {"id": 4, "description": "השווי", "exercise": "1/8 ___ 1/2", "answer": "1/2",
     "answer_type": "categorical", "type": "fraction-comparison",
     "subtopic": "fraction-comparison", "signature": "cmp:1/8|1/2", "difficulty": "medium"},
]

html_doc = build_quiz(QUESTIONS, "2026-06-01", "972500000000")

# ── Self-contained: no network/CDN references ───────────────────────────────
for pat in ("http://", "https://wa.me", "//cdn", "<link", 'src="http'):
    # wa.me appears only as a JS string template ("https://wa.me/" + ...), which
    # is a runtime user action, not a page-load dependency. Assert no load-time
    # external resources: no <link>, no external <script src>, no @import.
    pass
check("<link" not in html_doc, "page references an external <link> stylesheet")
check('src="http' not in html_doc and "src='http" not in html_doc,
      "page loads an external script via src=http")
check("@import" not in html_doc, "CSS uses @import (external dependency)")
check("cdn" not in html_doc.lower(), "page references a CDN")

# ── Every question rendered with an input slot (text box or hidden sign) ─────
for q in QUESTIONS:
    check(f'id="q_{q["id"]}"' in html_doc, f"missing input for q{q['id']}")

# ── Comparison question renders tappable signs, NOT a text box ───────────────
# q4 is fraction-comparison: expect 3 cmp-btn (< = >) targeting q_4, a hidden
# input (no class="ans"), and the two fractions present.
for sign in ("<", "=", ">"):
    check(f'data-target="q_4" data-sign="{sign}"' in html_doc,
          f"comparison q4 missing sign button {sign!r}")
check(html_doc.count('data-target="q_4"') == 3, "comparison q4 should have exactly 3 sign buttons")
check('type="hidden" id="q_4"' in html_doc,
      "comparison q4 should use a hidden input, not a text box")
check('class="ans" id="q_4"' not in html_doc, "comparison q4 must NOT be a free-text box")
# The 3 non-comparison questions each get a text box.
check(html_doc.count('class="ans"') == 3, "expected 3 free-text inputs (non-comparison)")

# ── No correct answers leak into the page ───────────────────────────────────
# A real leak would be the answer embedded as page DATA (in the <script> block),
# NOT the answer happening to appear inside displayed question text (e.g. the
# instruction "האם ראשוני?" legitimately contains the word "ראשוני").
script = html_doc[html_doc.index("<script>"):html_doc.index("</script>")]
for q in QUESTIONS:
    check(q["answer"] not in script,
          f"correct answer {q['answer']!r} leaked into the embedded script data")
# "144" is unique to the answer (not in any question text), so it must be absent entirely.
check("144" not in html_doc, "correct answer '144' leaked into the page")

# ── he-only fallback renders the text, not a blank ──────────────────────────
check("כמה זה 2×8?" in html_doc, "he-only question text not rendered")

# ── Question text IS shown (instruction/exercise present) ────────────────────
check("57 + 87" in html_doc, "exercise not rendered")
check("האם ראשוני?" in html_doc, "instruction not rendered")

if _failures:
    print(f"FAIL ({len(_failures)}):")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("test_quiz_builder: OK")
