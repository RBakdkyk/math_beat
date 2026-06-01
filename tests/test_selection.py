#!/usr/bin/env python3
"""Difficulty-selection invariants (stdlib only).

Run: python tests/test_selection.py

Covers change `add-difficulty-selection-controls`:
  - per-topic override > global --difficulty > auto _infer_difficulty
  - override no-ops when its topic isn't selected; honored when forced/--topics
  - advanced pitch: bootstrap non-warmup = medium; _infer thresholds shifted
  - multiplication-table override keeps weak-fact targeting
  - invalid --difficulty tokens raise a clear error (function + CLI)

Separate from tests/test_bands.py (change A's band invariants).
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import session as S  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def raises_valueerror(fn):
    try:
        fn()
        return False
    except ValueError:
        return True


# ── 1. Precedence via resolve_difficulty ────────────────────────────────────
summary_hot = {"topics": {"division": {"correct_rate": 0.9}}}
check(
    S.resolve_difficulty("fraction-addition", {"fraction-addition": "hard"}, "easy", summary_hot) == "hard",
    "per-topic override must beat global",
)
check(
    S.resolve_difficulty("division", {}, "easy", summary_hot) == "easy",
    "global must beat auto when no per-topic override",
)
check(
    S.resolve_difficulty("division", None, None, summary_hot) == "hard",
    "auto inference must apply when neither override is set (0.9 -> hard)",
)
check(
    S.resolve_difficulty("addition", None, None, {}) == "medium",
    "auto inference on unknown topic defaults to medium",
)


# ── 2. Advanced pitch: shifted thresholds ───────────────────────────────────
check(
    S._infer_difficulty({"topics": {"x": {"correct_rate": 0.7}}}, "x") == "hard",
    "_infer_difficulty(0.7) must be hard under shifted thresholds",
)
check(
    S._infer_difficulty({"topics": {"x": {"correct_rate": 0.2}}}, "x") == "easy",
    "_infer_difficulty(0.2) must be easy",
)
check(
    S._infer_difficulty({"topics": {"x": {"correct_rate": 0.5}}}, "x") == "medium",
    "_infer_difficulty(0.5) must be medium",
)
# Old 0.4/0.8 split would have called 0.7 medium and 0.35 easy — guard the skew.
check(
    S._infer_difficulty({"topics": {"x": {"correct_rate": 0.35}}}, "x") == "medium",
    "0.35 must be medium (not easy) under the shifted easy<0.3 threshold",
)


# ── 3. Bootstrap path: medium non-warmup + override honored ──────────────────
S.read_summary = lambda: {}

boot = S._bootstrap_plan(8)
nonwarm = [s for s in boot if s["qtype"] != "multiplication-table"]
check(bool(nonwarm), "bootstrap must produce non-warmup slots")
check(
    all(s["difficulty"] == "medium" for s in nonwarm),
    "bootstrap non-warmup slots must start at medium, not easy",
)

# Override honored on the bootstrap (no --topics) path.
boot_ov = S.build_session_plan(count=8, difficulty_map={"division": "easy"})
boot_div = [s for s in boot_ov if s["qtype"] == "division"]
check(bool(boot_div), "bootstrap core should include division")
check(
    all(s["difficulty"] == "easy" for s in boot_div),
    "per-topic override must be honored on the bootstrap path",
)

# Override honored on the --topics path (Scenario: bootstrap/--topics).
topics_plan = S.build_session_plan(
    count=6, topics_override=["division"], difficulty_map={"division": "easy"}
)
check(
    all(s["qtype"] == "division" and s["difficulty"] == "easy" for s in topics_plan),
    "--topics + per-topic override must yield that topic at the override tier",
)


# ── 4. Adaptive path: precedence, no-op, weak-fact warmup ────────────────────
SUMMARY = {
    "topics": {
        "multiplication-table": {
            "facts": {
                "7×8": {"correct": 1, "wrong": 4},
                "3×4": {"correct": 5, "wrong": 0},
            }
        },
        "fraction-addition": {"correct_rate": 0.9},
    }
}
S.read_summary = lambda: SUMMARY
S._prioritized_topics = lambda summary, exclude=None: ["fraction-addition", "division", "addition"]

# 4a. auto applies where neither override set (main 0.9 -> hard; division -> medium)
auto_plan = S.build_session_plan(count=8)
fa = [s for s in auto_plan if s["qtype"] == "fraction-addition"]
div = [s for s in auto_plan if s["qtype"] == "division"]
check(fa and all(s["difficulty"] == "hard" for s in fa), "auto infer: fraction-addition 0.9 -> hard")
check(div and all(s["difficulty"] == "medium" for s in div), "auto infer: untracked division -> medium")

# 4b. precedence inside a real plan: per-topic > global > auto
mixed = S.build_session_plan(count=8, difficulty_override="easy", difficulty_map={"fraction-addition": "hard"})
mfa = [s for s in mixed if s["qtype"] == "fraction-addition"]
mdiv = [s for s in mixed if s["qtype"] == "division"]
check(mfa and all(s["difficulty"] == "hard" for s in mfa), "per-topic override must win over global easy")
check(mdiv and all(s["difficulty"] == "easy" for s in mdiv), "global must win over auto for non-overridden topic")

# 4c. override no-ops when its topic isn't selected
noop = S.build_session_plan(count=8, difficulty_map={"geometry": "hard"})
check(
    not any(s["qtype"] == "geometry" for s in noop),
    "a per-topic override must NOT force an unselected topic into the session",
)

# 4d. multiplication-table=hard keeps weak-fact targeting (D4 / task 4.3)
warm_plan = S.build_session_plan(count=8, difficulty_map={"multiplication-table": "hard"})
warm = [s for s in warm_plan if s["qtype"] == "multiplication-table"]
check(bool(warm), "warmup slots must exist")
check(all(s["difficulty"] == "hard" for s in warm), "warmup tier must honor multiplication-table override")
check(any("target_fact" in s for s in warm), "warmup must still target weak facts under an override")
check(warm[0].get("target_fact") == "7×8", "warmup must target the weakest fact (7×8) first")


# ── 5. Token parsing + invalid input (task 4.4) ──────────────────────────────
g, m = S.parse_difficulty_tokens(["medium", "fractions=hard"])
check(g == "medium", "bare token must become the global level")
check(
    m == {
        "fraction-addition": "hard",
        "fraction-comparison": "hard",
        "fraction-subtraction": "hard",
    },
    "fractions alias must expand to the three fraction subtopics",
)
g2, m2 = S.parse_difficulty_tokens(["hard"])
check(g2 == "hard" and m2 == {}, "single bare level is global only")

check(raises_valueerror(lambda: S.parse_difficulty_tokens(["fractions=banana"])),
      "invalid level (banana) must raise ValueError")
check(raises_valueerror(lambda: S.parse_difficulty_tokens(["nosuchtopic=hard"])),
      "unknown topic must raise ValueError")
check(raises_valueerror(lambda: S.parse_difficulty_tokens(["banana"])),
      "invalid bare level must raise ValueError")

# CLI-level: generate.py must exit non-zero with a clear error, writing nothing.
cli = subprocess.run(
    [sys.executable, "generate.py", "--difficulty", "fractions=banana", "--date", "2099-12-31"],
    cwd=str(REPO), capture_output=True, text=True,
)
check(cli.returncode != 0, "generate.py must exit non-zero on a bad --difficulty token")
check("banana" in cli.stderr, "CLI error must name the invalid level")
check(not (REPO / "wiki" / "sessions" / "2099-12-31").exists(),
      "no session must be written when --difficulty is invalid")


# ── 6. CLI: alias-expanded --topics + per-topic override (design D1) ─────────
ok = subprocess.run(
    [sys.executable, "generate.py", "--topics", "fractions", "--count", "6",
     "--difficulty", "fractions=hard", "--date", "2099-12-30", "--force"],
    cwd=str(REPO), capture_output=True, text=True,
)
check(ok.returncode == 0, f"--topics fractions --difficulty fractions=hard must succeed: {ok.stderr}")
gen = REPO / "wiki" / "sessions" / "2099-12-30" / "generated.json"
if gen.exists():
    import json
    data = json.loads(gen.read_text())
    qs = data["questions"] if isinstance(data, dict) and "questions" in data else data
    check(bool(qs), "session must contain questions")
    check(
        all(q["type"].startswith("fraction-") for q in qs),
        "--topics fractions must expand to fraction subtopics, not the literal alias",
    )
    check(
        all(q["difficulty"] == "hard" for q in qs),
        "fractions=hard must apply to the alias-expanded --topics fractions slots",
    )
    import shutil
    shutil.rmtree(gen.parent)
else:
    check(False, "generate.py wrote no session for the D1 path")


# ── Report ───────────────────────────────────────────────────────────────────
if _failures:
    print(f"FAIL ({len(_failures)} failures):")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
print("OK — all difficulty-selection invariants hold")
