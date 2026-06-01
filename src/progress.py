"""Progress tracking — merge session results into summary.json."""

from datetime import date, datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from wiki import (
    read_summary, write_summary, read_generated, read_results,
    list_sessions, SUMMARY_PATH
)


_PRUNE_DAYS = 15


def _today() -> str:
    return date.today().isoformat()


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _is_recent(date_str: str, cutoff: date) -> bool:
    try:
        return _parse_date(date_str) >= cutoff
    except (ValueError, TypeError):
        return True  # keep if unparseable


def update_summary(session_date: str) -> dict:
    """Merge a session's results into summary.json.

    Returns the updated summary dict.
    Raises FileNotFoundError if generated.json or results.json are missing.
    """
    questions = read_generated(session_date)
    if questions is None:
        raise FileNotFoundError(f"No generated.json for {session_date}")
    results = read_results(session_date)
    if results is None:
        raise FileNotFoundError(f"No results.json for {session_date}")

    # Build a lookup: question id → result
    result_map = {r["id"]: r for r in results}

    summary = read_summary()
    topics = summary.setdefault("topics", {})
    cutoff = _parse_date(session_date) - timedelta(days=_PRUNE_DAYS - 1)

    for q in questions:
        qid = q["id"]
        qtype = q.get("subtopic", q.get("type", "unknown"))
        sig = q.get("signature", "")
        result = result_map.get(qid)
        if result is None:
            continue  # skipped question — not counted
        correct = bool(result.get("correct", False))
        difficulty = q.get("difficulty", "medium")

        if qtype == "multiplication-table":
            _update_mult_fact(topics, sig, session_date, correct, difficulty)
        else:
            _update_topic_params(topics, qtype, sig, session_date, correct, difficulty)

    # Prune old used_params (not multiplication facts)
    for qtype, tdata in topics.items():
        if "used_params" in tdata:
            tdata["used_params"] = [
                p for p in tdata["used_params"]
                if _is_recent(p.get("date", ""), cutoff)
            ]
        # Recalculate correct_rate
        _recalculate_rate(tdata)

    # Update top-level topic metadata
    session_qtypes = {q.get("subtopic", q.get("type")) for q in questions}
    for qtype in session_qtypes:
        if qtype in topics:
            topics[qtype]["last_practiced"] = session_date
            topics[qtype]["times_practiced"] = topics[qtype].get("times_practiced", 0) + 1

    write_summary(summary)
    return summary


def _update_mult_fact(topics: dict, sig: str, session_date: str, correct: bool, difficulty: str = "medium") -> None:
    """Increment per-fact correct/wrong counts for multiplication-table."""
    tdata = topics.setdefault("multiplication-table", {
        "correct_rate": 0.0,
        "times_practiced": 0,
        "last_practiced": None,
        "facts": {},
    })
    facts = tdata.setdefault("facts", {})
    fact_key = sig.replace("mult:", "")
    fact = facts.setdefault(fact_key, {"correct": 0, "wrong": 0, "last_seen": None})
    if correct:
        fact["correct"] += 1
    else:
        fact["wrong"] += 1
    fact["last_seen"] = session_date
    by_diff = fact.setdefault("by_difficulty", {})
    entry = by_diff.setdefault(difficulty, {"correct": 0, "wrong": 0})
    if correct:
        entry["correct"] += 1
    else:
        entry["wrong"] += 1


def _update_topic_params(topics: dict, qtype: str, sig: str, session_date: str, correct: bool, difficulty: str = "medium") -> None:
    """Append a used_params entry for a non-multiplication topic."""
    tdata = topics.setdefault(qtype, {
        "correct_rate": 0.0,
        "times_practiced": 0,
        "last_practiced": None,
        "used_params": [],
    })
    tdata.setdefault("used_params", []).append({
        "sig": sig,
        "date": session_date,
        "correct": correct,
        "difficulty": difficulty,
    })


def _recalculate_rate(tdata: dict) -> None:
    """Recalculate correct_rate and difficulty_rates from available data in tdata."""
    if "facts" in tdata:
        total_c = sum(f["correct"] for f in tdata["facts"].values())
        total_w = sum(f["wrong"] for f in tdata["facts"].values())
        total = total_c + total_w
        tdata["correct_rate"] = round(total_c / total, 3) if total > 0 else 0.0
        diff_totals: dict = {}
        for f in tdata["facts"].values():
            for diff, counts in f.get("by_difficulty", {}).items():
                dt = diff_totals.setdefault(diff, {"correct": 0, "wrong": 0})
                dt["correct"] += counts["correct"]
                dt["wrong"] += counts["wrong"]
        tdata["difficulty_rates"] = {
            d: round(v["correct"] / (v["correct"] + v["wrong"]), 3)
            for d, v in diff_totals.items()
            if (v["correct"] + v["wrong"]) > 0
        }
    elif "used_params" in tdata:
        params = tdata["used_params"]
        if params:
            c = sum(1 for p in params if p.get("correct"))
            tdata["correct_rate"] = round(c / len(params), 3)
            diff_groups: dict = {}
            for p in params:
                d = p.get("difficulty", "medium")
                dg = diff_groups.setdefault(d, {"correct": 0, "total": 0})
                dg["total"] += 1
                if p.get("correct"):
                    dg["correct"] += 1
            tdata["difficulty_rates"] = {
                d: round(v["correct"] / v["total"], 3)
                for d, v in diff_groups.items()
                if v["total"] > 0
            }


def rebuild_summary() -> dict:
    """Rebuild summary.json from scratch by replaying all sessions chronologically."""
    # Wipe summary
    summary = {"topics": {}}
    write_summary(summary)

    sessions = list_sessions()
    for session_date in sessions:
        try:
            update_summary(session_date)
        except FileNotFoundError:
            pass  # session without results — skip

    return read_summary()
