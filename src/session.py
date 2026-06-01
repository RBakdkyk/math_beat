"""Session composition — topic selection and session structure builder."""

from datetime import date, datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from wiki import read_summary
from curriculum import TOPICS, TEMPLATE_TOPICS


def _staleness_days(last_practiced: str | None) -> int:
    if last_practiced is None:
        return 999  # Never practiced — very stale
    try:
        d = date.fromisoformat(last_practiced)
        return (date.today() - d).days
    except ValueError:
        return 999


def _topic_priority(qtype: str, tdata: dict) -> float:
    """Higher score = higher priority. Based on weakness + staleness + coverage."""
    correct_rate = tdata.get("correct_rate", 0.5)
    times_practiced = tdata.get("times_practiced", 0)
    stale_days = _staleness_days(tdata.get("last_practiced"))

    # Weakness: lower correct_rate → higher priority
    weakness_score = 1.0 - correct_rate

    # Staleness: longer since practiced → higher priority (caps at 14 days)
    staleness_score = min(stale_days / 14.0, 1.0)

    # Coverage: fewer times → higher priority (caps at 10 sessions)
    coverage_score = max(0.0, 1.0 - times_practiced / 10.0)

    return weakness_score * 0.5 + staleness_score * 0.3 + coverage_score * 0.2


def _prioritized_topics(summary: dict, exclude: set = None) -> list:
    """Return all template topics sorted by priority (highest first)."""
    exclude = exclude or set()
    topics_data = summary.get("topics", {})
    scored = []
    for qtype in TEMPLATE_TOPICS:
        if qtype in exclude:
            continue
        tdata = topics_data.get(qtype, {})
        score = _topic_priority(qtype, tdata)
        scored.append((score, qtype))
    scored.sort(reverse=True)
    return [qtype for _, qtype in scored]


def _weakest_mult_facts(summary: dict, n: int = 3) -> list:
    """Return the n weakest multiplication fact keys (lowest correct/wrong ratio)."""
    facts = summary.get("topics", {}).get("multiplication-table", {}).get("facts", {})
    if not facts:
        return []
    # Score by wrong / (correct + wrong) ratio
    scored = []
    for fact_key, fdata in facts.items():
        c = fdata.get("correct", 0)
        w = fdata.get("wrong", 0)
        total = c + w
        ratio = w / total if total > 0 else 0.5
        scored.append((ratio, fact_key))
    scored.sort(reverse=True)
    return [key for _, key in scored[:n]]


def build_session_plan(
    count: int = 8,
    topics_override: list = None,
    difficulty_override: str = None,
) -> list:
    """Build a session plan: list of {qtype, difficulty} dicts.

    Without overrides, uses progress data to decide structure:
      - 3 warmup (multiplication-table, targeting weak facts)
      - remaining split between weakest and second-weakest topics

    With overrides:
      - topics_override: list of qtypes to use exclusively
      - difficulty_override: force a specific difficulty

    Returns list of {qtype, difficulty, weak_facts?} dicts.
    """
    summary = read_summary()
    has_progress = bool(summary.get("topics"))

    if topics_override:
        # All questions on specified topics
        plan = []
        topic_cycle = topics_override * (count // len(topics_override) + 1)
        for i in range(count):
            plan.append({
                "qtype": topic_cycle[i],
                "difficulty": difficulty_override or "medium",
            })
        return plan

    if not has_progress:
        return _bootstrap_plan(count, difficulty_override)

    return _adaptive_plan(summary, count, difficulty_override)


def _bootstrap_plan(count: int, difficulty: str = None) -> list:
    """Diagnostic session for first run (no progress data)."""
    plan = []
    # 3 multiplication warmup
    for _ in range(min(3, count)):
        plan.append({"qtype": "multiplication-table", "difficulty": difficulty or "medium"})
    # Remaining: distribute across core topics
    core = ["addition", "subtraction", "division", "fraction-comparison", "fraction-addition"]
    remaining = count - len(plan)
    for i in range(remaining):
        plan.append({
            "qtype": core[i % len(core)],
            "difficulty": difficulty or "easy",
        })
    return plan


def _adaptive_plan(summary: dict, count: int, difficulty: str = None) -> list:
    """Session plan driven by progress data."""
    plan = []
    warmup_count = min(3, count)
    remaining = count - warmup_count

    # Warmup: multiplication, targeting weak facts
    weak_facts = _weakest_mult_facts(summary, n=warmup_count)
    for i in range(warmup_count):
        entry = {"qtype": "multiplication-table", "difficulty": difficulty or "medium"}
        if i < len(weak_facts):
            entry["target_fact"] = weak_facts[i]
        plan.append(entry)

    # Get priority-sorted topics (excluding warmup)
    sorted_topics = _prioritized_topics(summary, exclude={"multiplication-table"})
    if not sorted_topics:
        sorted_topics = ["fraction-addition", "division"]

    main_topic = sorted_topics[0]
    secondary_topic = sorted_topics[1] if len(sorted_topics) > 1 else sorted_topics[0]

    # Allocate: 60-70% to main, 30-40% to secondary
    main_count = max(1, int(remaining * 0.65))
    secondary_count = remaining - main_count

    main_diff = difficulty or _infer_difficulty(summary, main_topic)
    sec_diff = difficulty or _infer_difficulty(summary, secondary_topic)

    for _ in range(main_count):
        plan.append({"qtype": main_topic, "difficulty": main_diff})
    for _ in range(secondary_count):
        plan.append({"qtype": secondary_topic, "difficulty": sec_diff})

    return plan


def _infer_difficulty(summary: dict, qtype: str) -> str:
    """Pick difficulty based on correct rate."""
    tdata = summary.get("topics", {}).get(qtype, {})
    rate = tdata.get("correct_rate", 0.5)
    if rate < 0.4:
        return "easy"
    if rate > 0.8:
        return "hard"
    return "medium"
