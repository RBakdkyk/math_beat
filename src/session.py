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

# Topics omitted from automatic rotation/priority selection. They remain
# generatable on explicit request (`--topics …`), which bypasses this list.
AUTO_EXCLUDED_TOPICS = {"prime-composite", "math-sense"}

# Priority score of a never-practiced topic (correct_rate 0.5, 0 practices,
# infinitely stale): 0.5*0.5 + 1.0*0.3 + 1.0*0.2 = 0.75. A confirmed weakness
# (a practiced topic answered wrong) must rank at least this high — see
# _topic_priority.
NEVER_PRACTICED_BASELINE = 0.75


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

    score = weakness_score * 0.5 + staleness_score * 0.3 + coverage_score * 0.2

    # Weakness must never rank below mere unfamiliarity: a topic that has been
    # practiced and answered wrong is a confirmed weakness and should sit at
    # least at the never-practiced baseline. Floor the score in proportion to
    # how wrong it is — a fully-wrong topic (correct_rate 0.0) reaches the
    # baseline; a partly-wrong one lands proportionally below it. This stays
    # pure weakness rotation (no curriculum-hours weighting).
    if times_practiced > 0:
        score = max(score, weakness_score * NEVER_PRACTICED_BASELINE)

    return score


def _zone_counts(count: int) -> tuple:
    """Map a total question count to (primary, rotation) counts.

    The zones always sum exactly to `count` for any count ≥ 1 (`--count` is
    unclamped). Primary-drill depth is 2 when `count` is ≥ 4, else 1 (or 0 for
    count 0); the rest are 1-each rotation slots.
    """
    count = max(0, count)
    if count <= 0:
        primary = 0
    elif count >= 4:
        primary = 2
    else:
        primary = 1
    rotation = count - primary
    return primary, rotation


def _prioritized_topics(summary: dict, exclude: set = None) -> list:
    """Return all template topics sorted by priority (highest first)."""
    exclude = (exclude or set()) | AUTO_EXCLUDED_TOPICS
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


def build_session_plan(
    count: int = 10,
    topics_override: list = None,
    difficulty_override: str = None,
    difficulty_map: dict = None,
) -> list:
    """Build a session plan: list of {qtype, difficulty} dicts.

    Without overrides, uses progress data to decide structure:
      - 2-deep primary drill on the top-priority topic
      - 1-each rotation across the next distinct topics in priority order

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
    elif not has_progress:
        plan = _bootstrap_plan(count, difficulty_override, difficulty_map, summary)
    else:
        plan = _adaptive_plan(summary, count, difficulty_override, difficulty_map)

    # Constant math-sense slot, appended on top of the normal plan — never
    # competes for a primary/rotation slot (excluded via AUTO_EXCLUDED_TOPICS).
    plan.append({
        "qtype": "math-sense",
        "difficulty": resolve_difficulty(
            "math-sense", difficulty_map, difficulty_override, summary
        ),
    })
    return plan


def _bootstrap_plan(
    count: int,
    difficulty: str = None,
    difficulty_map: dict = None,
    summary: dict = None,
) -> list:
    """Diagnostic session for first run (no progress data).

    Advanced pitch: questions start at `medium` (not `easy`).
    """
    summary = summary or {}
    plan = []
    # Distribute across core topics, starting at medium for an advanced
    # student (auto inference on an empty summary yields medium).
    core = ["addition", "subtraction", "division", "fraction-comparison", "fraction-addition"]
    for i in range(count):
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
    """Session plan driven by progress data.

    Zoned spread: primary depth on the #1-priority topic + 1-each rotation
    across the next distinct topics in priority order. There is no separate
    "coverage" pick — least-touched topics already rank at the top of
    `_topic_priority`, so long-tail breadth falls out of the distinct-topic
    spread (a default 8-question session yields ≥5 distinct topics).
    """
    plan = []
    primary_count, rotation_count = _zone_counts(count)

    sorted_topics = _prioritized_topics(summary)
    if not sorted_topics:
        sorted_topics = ["fraction-addition", "division"]

    # Primary depth on the top-priority topic, then one each across the next
    # distinct topics in priority order. Exhaustion fallback: only once every
    # distinct topic has been used do we cycle back and repeat (not reachable
    # with ~17 template topics, but defined for safety).
    slots = []
    if primary_count > 0:
        slots.extend([sorted_topics[0]] * primary_count)
        rotation_pool = sorted_topics[1:] or sorted_topics
    else:
        rotation_pool = sorted_topics
    for i in range(rotation_count):
        slots.append(rotation_pool[i % len(rotation_pool)])

    for qtype in slots:
        diff = resolve_difficulty(qtype, difficulty_map, difficulty, summary)
        plan.append({"qtype": qtype, "difficulty": diff})

    return plan


def _infer_difficulty(summary: dict, qtype: str) -> str:
    """Pick difficulty based on correct rate.

    Advanced pitch: auto-inference never drops below `medium` — a struggling
    topic stays at medium rather than easing off. `easy` is reachable only by an
    explicit `--difficulty easy` or a per-topic override (see resolve_difficulty).
    """
    tdata = summary.get("topics", {}).get(qtype, {})
    rate = tdata.get("correct_rate", 0.5)
    if rate > 0.65:
        return "hard"
    return "medium"
