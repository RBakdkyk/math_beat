"""Session composition — topic selection and session structure builder."""

from datetime import date, datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from wiki import read_summary
from curriculum import TOPICS, TEMPLATE_TOPICS


# Topic alias map — mirrors the /practice skill. Maps a user-facing key
# (an alias or a Hebrew word) to the concrete subtopic qtypes it covers.
# Any direct qtype in TOPICS also resolves to itself (see resolve_topic_alias).
TOPIC_ALIASES = {
    "fractions": ["fraction-addition", "fraction-comparison", "fraction-subtraction"],
    "שברים":      ["fraction-addition", "fraction-comparison", "fraction-subtraction"],
    "multiplication": ["multiplication-table", "multiplication"],
    "כפל":            ["multiplication-table", "multiplication"],
    "division": ["division"],
    "חילוק":     ["division"],
    "arithmetic": ["addition", "subtraction", "multiplication", "division"],
    "חשבון":       ["addition", "subtraction", "multiplication", "division"],
    "geometry": ["geometry"],
    "צורות":     ["geometry"],
    "probability": ["probability"],
    "סיכויים":      ["probability"],
}

VALID_LEVELS = {"easy", "medium", "hard"}


def resolve_topic_alias(key: str) -> list | None:
    """Resolve an override key to the list of qtypes it covers.

    Returns None if the key is neither a known alias nor a direct qtype.
    """
    if key in TOPIC_ALIASES:
        return list(TOPIC_ALIASES[key])
    if key in TOPICS:
        return [key]
    return None


def parse_difficulty_tokens(tokens: list) -> tuple:
    """Parse `--difficulty` tokens into (global_level, {qtype: level}).

    Each token is either a bare level (the global fallback) or `topic=level`.
    Per-topic keys are expanded through the alias map to concrete qtypes.
    Raises ValueError with a clear message on any invalid token.
    """
    global_level = None
    diff_map = {}
    for tok in tokens:
        if "=" in tok:
            key, _, level = tok.partition("=")
            key = key.strip()
            level = level.strip()
            if level not in VALID_LEVELS:
                raise ValueError(
                    f"invalid difficulty level {level!r} in {tok!r}; "
                    f"must be one of easy, medium, hard"
                )
            qtypes = resolve_topic_alias(key)
            if not qtypes:
                raise ValueError(
                    f"unknown topic {key!r} in {tok!r}; "
                    f"use a topic key or alias (e.g. fractions, division)"
                )
            for qt in qtypes:
                diff_map[qt] = level
        else:
            level = tok.strip()
            if level not in VALID_LEVELS:
                raise ValueError(
                    f"invalid difficulty {level!r}; expected a level "
                    f"(easy/medium/hard) or topic=level (e.g. fractions=hard)"
                )
            global_level = level
    return global_level, diff_map


def resolve_difficulty(
    qtype: str,
    difficulty_map: dict = None,
    difficulty_global: str = None,
    summary: dict = None,
) -> str:
    """Resolve a question slot's difficulty.

    Precedence: per-topic override > global `--difficulty` > auto inference.
    """
    if difficulty_map and qtype in difficulty_map:
        return difficulty_map[qtype]
    if difficulty_global:
        return difficulty_global
    return _infer_difficulty(summary or {}, qtype)


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
    difficulty_map: dict = None,
) -> list:
    """Build a session plan: list of {qtype, difficulty} dicts.

    Without overrides, uses progress data to decide structure:
      - 3 warmup (multiplication-table, targeting weak facts)
      - remaining split between weakest and second-weakest topics

    With overrides:
      - topics_override: list of qtypes to use exclusively
      - difficulty_override: global difficulty fallback
      - difficulty_map: {qtype: level} per-topic overrides (expanded from aliases)

    Difficulty precedence per slot: per-topic override > global > auto.
    A per-topic override only sets the tier when its topic is actually selected;
    it does NOT force the topic into the session.

    Returns list of {qtype, difficulty, target_fact?} dicts.
    """
    summary = read_summary()
    has_progress = bool(summary.get("topics"))

    if topics_override:
        # All questions on specified topics
        plan = []
        topic_cycle = topics_override * (count // len(topics_override) + 1)
        for i in range(count):
            qtype = topic_cycle[i]
            plan.append({
                "qtype": qtype,
                "difficulty": resolve_difficulty(
                    qtype, difficulty_map, difficulty_override, summary
                ),
            })
        return plan

    if not has_progress:
        return _bootstrap_plan(count, difficulty_override, difficulty_map, summary)

    return _adaptive_plan(summary, count, difficulty_override, difficulty_map)


def _warmup_difficulty(difficulty_map: dict, difficulty_global: str) -> str:
    """Warmup tier: always hard, unless an explicit per-topic override is set.

    The warmup always pulls from the full 1×1–10×10 fact pool (the "hard" tier)
    so table practice never softens. A global `--difficulty` does NOT drag it
    down; only an explicit `multiplication-table=<level>` override can change it.
    Weak-fact targeting is applied separately and is unaffected by this tier.
    """
    if difficulty_map and "multiplication-table" in difficulty_map:
        return difficulty_map["multiplication-table"]
    return "hard"


def _bootstrap_plan(
    count: int,
    difficulty: str = None,
    difficulty_map: dict = None,
    summary: dict = None,
) -> list:
    """Diagnostic session for first run (no progress data).

    Advanced pitch: non-warmup questions start at `medium` (not `easy`).
    """
    summary = summary or {}
    plan = []
    warmup_diff = _warmup_difficulty(difficulty_map, difficulty)
    # 3 multiplication warmup
    for _ in range(min(3, count)):
        plan.append({"qtype": "multiplication-table", "difficulty": warmup_diff})
    # Remaining: distribute across core topics, starting at medium for an
    # advanced student (auto inference on an empty summary yields medium).
    core = ["addition", "subtraction", "division", "fraction-comparison", "fraction-addition"]
    remaining = count - len(plan)
    for i in range(remaining):
        qtype = core[i % len(core)]
        plan.append({
            "qtype": qtype,
            "difficulty": resolve_difficulty(qtype, difficulty_map, difficulty, summary),
        })
    return plan


def _adaptive_plan(
    summary: dict,
    count: int,
    difficulty: str = None,
    difficulty_map: dict = None,
) -> list:
    """Session plan driven by progress data."""
    plan = []
    warmup_count = min(3, count)
    remaining = count - warmup_count

    # Warmup: multiplication, targeting weak facts (tier is not auto-inferred)
    warmup_diff = _warmup_difficulty(difficulty_map, difficulty)
    weak_facts = _weakest_mult_facts(summary, n=warmup_count)
    for i in range(warmup_count):
        entry = {"qtype": "multiplication-table", "difficulty": warmup_diff}
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

    main_diff = resolve_difficulty(main_topic, difficulty_map, difficulty, summary)
    sec_diff = resolve_difficulty(secondary_topic, difficulty_map, difficulty, summary)

    for _ in range(main_count):
        plan.append({"qtype": main_topic, "difficulty": main_diff})
    for _ in range(secondary_count):
        plan.append({"qtype": secondary_topic, "difficulty": sec_diff})

    return plan


def _infer_difficulty(summary: dict, qtype: str) -> str:
    """Pick difficulty based on correct rate.

    Thresholds skew upward for an advanced student: harder tiers are reached
    sooner than the prior 0.4/0.8 split.
    """
    tdata = summary.get("topics", {}).get(qtype, {})
    rate = tdata.get("correct_rate", 0.5)
    if rate < 0.3:
        return "easy"
    if rate > 0.65:
        return "hard"
    return "medium"
