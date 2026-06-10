#!/usr/bin/env python3
"""Topic-distribution invariants (stdlib only).

Run: python tests/test_distribution.py

Covers change `broaden-topic-distribution`:
  - priority quirk fix: a wrong-answer topic ranks >= a never-practiced one,
    while never-practiced still outranks a well-practiced high-rate topic
  - zone-scaling helper: (warmup, primary, rotation) sums exactly to count for
    any count >= 1, with no negative/oversized zone
  - zoned adaptive plan: >=5 distinct topics, 3 warmups, 2 on the top topic;
    --count 5 yields exactly 5; bootstrap (cold start) shape is unchanged
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
    w, p, r = S._zone_counts(count)
    check(w + p + r == count, f"_zone_counts({count}) must sum to {count}, got {(w, p, r)}")
    check(w >= 0 and p >= 0 and r >= 0, f"_zone_counts({count}) has a negative zone {(w, p, r)}")
    check(w <= 3, f"_zone_counts({count}) warmup {w} exceeds 3")
    check(p <= 2, f"_zone_counts({count}) primary {p} exceeds 2")

# Spot-check the canonical default
check(S._zone_counts(8) == (3, 2, 3), f"count 8 should be (3,2,3), got {S._zone_counts(8)}")
check(S._zone_counts(10) == (3, 2, 5), f"count 10 should be (3,2,5), got {S._zone_counts(10)}")
check(S._zone_counts(1) == (1, 0, 0), f"count 1 should be (1,0,0), got {S._zone_counts(1)}")
check(S._zone_counts(2) == (2, 0, 0), f"count 2 should be (2,0,0), got {S._zone_counts(2)}")


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
warm = [s for s in plan8 if s["qtype"] == "multiplication-table"]
check(len(warm) == 3, f"default plan must have 3 warmups, got {len(warm)}")
distinct = {s["qtype"] for s in plan8}
check(len(distinct) >= 5, f"default plan must span >=5 distinct topics, got {len(distinct)}: {distinct}")

# 2-deep primary on the top-priority non-warmup topic
nonwarm = [s["qtype"] for s in plan8 if s["qtype"] != "multiplication-table"]
top = S._prioritized_topics(SUMMARY, exclude={"multiplication-table"})[0]
check(nonwarm.count(top) == 2, f"top-priority topic {top!r} must get 2 questions, got {nonwarm.count(top)}")
# subtraction (wrong-answer) ties at the top tier and is surfaced into the spread,
# even though an alphabetical tiebreak among the 0.75-tier may name another topic #1
sub_prio = S._topic_priority("subtraction", SUMMARY["topics"]["subtraction"])
top_prio = S._topic_priority(top, SUMMARY["topics"].get(top, {}))
check(sub_prio >= top_prio - 1e-9,
      f"confirmed-weak subtraction ({sub_prio}) must rank in the top tier ({top_prio})")
check("subtraction" in nonwarm, "the confirmed-weak topic must appear in the spread")

# warmup targets the weakest fact first
check(warm[0].get("target_fact") == "7×8", "warmup must target the weakest fact (7×8) first")

# --count 5 → exactly 5 across scaled zones
plan5 = S.build_session_plan(count=5)
check(len(plan5) == 5, f"--count 5 must yield exactly 5, got {len(plan5)}")
check(sum(1 for s in plan5 if s["qtype"] == "multiplication-table") == S._zone_counts(5)[0],
      "warmup count in --count 5 plan must match the zone helper")

# 3.4: bootstrap (cold start) shape unchanged — 3 warmups + curated 5-topic core
S.read_summary = lambda: {}
boot = S.build_session_plan(count=8)
boot_warm = [s for s in boot if s["qtype"] == "multiplication-table"]
check(len(boot_warm) == 3, f"bootstrap must have 3 warmups, got {len(boot_warm)}")
boot_core = [s["qtype"] for s in boot if s["qtype"] != "multiplication-table"]
check(set(boot_core) == {"addition", "subtraction", "division",
                         "fraction-comparison", "fraction-addition"},
      f"bootstrap core must be the curated 5 fundamentals, got {set(boot_core)}")
check(all(s["difficulty"] == "medium" for s in boot if s["qtype"] != "multiplication-table"),
      "bootstrap non-warmup slots must stay at medium")


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
