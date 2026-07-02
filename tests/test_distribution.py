#!/usr/bin/env python3
"""Topic-distribution invariants (stdlib only).

Run: python tests/test_distribution.py

Covers change `broaden-topic-distribution`:
  - priority quirk fix: a wrong-answer topic ranks >= a never-practiced one,
    while never-practiced still outranks a well-practiced high-rate topic
  - zone-scaling helper: (primary, rotation) sums exactly to count for
    any count >= 1, with no negative/oversized zone
  - zoned adaptive plan: >=5 distinct topics, 2 on the top topic;
    --count 5 yields exactly 5; bootstrap (cold start) shape is unchanged
  - multiplication-table no longer forced as warmup — it competes in the
    normal priority rotation like any other topic
  - new template topic volume-surface-area: gradeable volume/surface variants
    across all three tiers, and quiz-renderable
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import session as S  # noqa: E402
from curriculum import (  # noqa: E402
    make_question, TEMPLATE_TOPICS, is_quiz_renderable, NEEDS_VISUAL_TOPICS,
)

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


# ── 1. Priority quirk fix (tasks 1.1, 1.3) ───────────────────────────────────
unseen = S._topic_priority("x", {})
check(abs(unseen - S.NEVER_PRACTICED_BASELINE) < 1e-9,
      f"never-practiced baseline should be {S.NEVER_PRACTICED_BASELINE}, got {unseen}")

# 1.1: wrong-answer topic (practiced once, 0% correct, recent) >= unseen baseline
today = S.date.today().isoformat()
wrong = S._topic_priority(
    "subtraction",
    {"correct_rate": 0.0, "times_practiced": 1, "last_practiced": today},
)
check(wrong >= unseen,
      f"wrong-answer topic ({wrong}) must rank >= never-practiced ({unseen})")

# 1.3: never-practiced still outranks a well-practiced, high-correct-rate topic
well = S._topic_priority(
    "fraction-addition",
    {"correct_rate": 0.95, "times_practiced": 6, "last_practiced": today},
)
check(unseen > well,
      f"never-practiced ({unseen}) must outrank well-practiced high-rate ({well})")
check(wrong > well,
      "a confirmed weakness must also outrank a well-practiced high-rate topic")


# ── 2. Zone-scaling helper (task 2.2) ────────────────────────────────────────
for count in (1, 2, 5, 8, 12, 20):
    p, r = S._zone_counts(count)
    check(p + r == count, f"_zone_counts({count}) must sum to {count}, got {(p, r)}")
    check(p >= 0 and r >= 0, f"_zone_counts({count}) has a negative zone {(p, r)}")
    check(p <= 2, f"_zone_counts({count}) primary {p} exceeds 2")

# Spot-check the canonical default
check(S._zone_counts(8) == (2, 6), f"count 8 should be (2,6), got {S._zone_counts(8)}")
check(S._zone_counts(10) == (2, 8), f"count 10 should be (2,8), got {S._zone_counts(10)}")
check(S._zone_counts(1) == (1, 0), f"count 1 should be (1,0), got {S._zone_counts(1)}")
check(S._zone_counts(2) == (1, 1), f"count 2 should be (1,1), got {S._zone_counts(2)}")


# ── 3. Zoned adaptive plan (tasks 3.4, 3.6) ──────────────────────────────────
SUMMARY = {
    "topics": {
        "multiplication-table": {
            "facts": {
                "7×8": {"correct": 1, "wrong": 4},
                "6×7": {"correct": 2, "wrong": 3},
                "3×4": {"correct": 5, "wrong": 0},
            }
        },
        "subtraction": {"correct_rate": 0.0, "times_practiced": 1, "last_practiced": today},
        "division": {"correct_rate": 0.5, "times_practiced": 2, "last_practiced": today},
    }
}
S.read_summary = lambda: SUMMARY

# default count is 10 (no count arg)
plan_default = S.build_session_plan()
check(len(plan_default) == 10, f"default plan (no --count) must have 10 slots, got {len(plan_default)}")
check(len({s['qtype'] for s in plan_default}) >= 5,
      "default 10-question plan must span >=5 distinct topics")

plan8 = S.build_session_plan(count=8)
check(len(plan8) == 8, f"explicit --count 8 must have 8 slots, got {len(plan8)}")
distinct = {s["qtype"] for s in plan8}
check(len(distinct) >= 5, f"default plan must span >=5 distinct topics, got {len(distinct)}: {distinct}")

# multiplication-table is no longer a forced warmup — it competes in the
# normal priority rotation and gets no target_fact
check(not any(s.get("target_fact") for s in plan8),
      "multiplication-table must no longer be weak-fact-targeted")

# 2-deep primary on the top-priority topic
topics_in_plan = [s["qtype"] for s in plan8]
top = S._prioritized_topics(SUMMARY)[0]
check(topics_in_plan.count(top) == 2, f"top-priority topic {top!r} must get 2 questions, got {topics_in_plan.count(top)}")
# subtraction (wrong-answer) ties at the top tier and is surfaced into the spread,
# even though an alphabetical tiebreak among the 0.75-tier may name another topic #1
sub_prio = S._topic_priority("subtraction", SUMMARY["topics"]["subtraction"])
top_prio = S._topic_priority(top, SUMMARY["topics"].get(top, {}))
check(sub_prio >= top_prio - 1e-9,
      f"confirmed-weak subtraction ({sub_prio}) must rank in the top tier ({top_prio})")
check("subtraction" in topics_in_plan, "the confirmed-weak topic must appear in the spread")

# --count 5 → exactly 5
plan5 = S.build_session_plan(count=5)
check(len(plan5) == 5, f"--count 5 must yield exactly 5, got {len(plan5)}")

# 3.4: bootstrap (cold start) shape — curated 5-topic core
S.read_summary = lambda: {}
boot = S.build_session_plan(count=8)
boot_topics = [s["qtype"] for s in boot]
check(set(boot_topics) == {"addition", "subtraction", "division",
                            "fraction-comparison", "fraction-addition"},
      f"bootstrap core must be the curated 5 fundamentals, got {set(boot_topics)}")
check(all(s["difficulty"] == "medium" for s in boot),
      "bootstrap slots must stay at medium")


# ── 4. New topic volume-surface-area (tasks 4.3, 4.4) ────────────────────────
check("volume-surface-area" in TEMPLATE_TOPICS, "volume-surface-area must be a template topic")
check(is_quiz_renderable("volume-surface-area"),
      "volume-surface-area must be quiz-renderable")
check("volume-surface-area" not in NEEDS_VISUAL_TOPICS,
      "volume-surface-area must NOT be in NEEDS_VISUAL_TOPICS")

seen_sigs = set()
for tier in ("easy", "medium", "hard"):
    for _ in range(300):
        q = make_question("volume-surface-area", tier)
        check(q["answer_type"] == "numeric", f"vol/surf {tier}: answer_type must be numeric")
        sig = q["signature"]
        seen_sigs.add(sig.split(":")[0])
        # answer value must equal the computed volume / surface from the dims
        _, dims = sig.split(":")
        a, b, c = (int(x) for x in dims.split("×"))
        ans_num = int(q["answer"].split()[0])
        if sig.startswith("volume:"):
            check(ans_num == a * b * c, f"volume {tier}: {a}×{b}×{c} answer {ans_num}")
        elif sig.startswith("surface:"):
            check(ans_num == 2 * (a * b + b * c + a * c),
                  f"surface {tier}: {a}×{b}×{c} answer {ans_num}")
        else:
            check(False, f"unexpected signature {sig!r}")
check({"volume", "surface"} <= seen_sigs,
      f"both volume and surface variants must be produced, saw {seen_sigs}")


# ── report ───────────────────────────────────────────────────────────────────
if _failures:
    print(f"FAIL — {len(_failures)} invariant violation(s):")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("OK — all topic-distribution invariants hold")
