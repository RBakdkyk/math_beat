"""Question generation orchestrator — template engine + Claude CLI fallback."""

import json
import random
import re
import subprocess
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from curriculum import make_question, CLAUDE_TOPICS
from wiki import read_summary, read_generated
from session import build_session_plan

_MAX_ATTEMPTS = 10
_PRUNE_DAYS = 15


def _recent_sigs(summary: dict) -> set:
    """Collect all signatures used within the last 15 days."""
    cutoff = date.today() - timedelta(days=_PRUNE_DAYS)
    sigs = set()
    for qtype, tdata in summary.get("topics", {}).items():
        if qtype == "multiplication-table":
            # Mult facts are tracked differently — no sig dedup
            continue
        for p in tdata.get("used_params", []):
            try:
                if date.fromisoformat(p.get("date", "2000-01-01")) >= cutoff:
                    sigs.add(p["sig"])
            except (ValueError, KeyError):
                pass
    return sigs


def _wrong_params(summary: dict, qtype: str) -> list:
    """Return sigs of recently wrong answers for a topic."""
    tdata = summary.get("topics", {}).get(qtype, {})
    return [
        p["sig"] for p in tdata.get("used_params", [])
        if not p.get("correct", True)
    ]


def _generate_template_question(qtype: str, difficulty: str, used_sigs: set) -> dict | None:
    """Try up to _MAX_ATTEMPTS to generate a non-duplicate question."""
    for _ in range(_MAX_ATTEMPTS):
        try:
            q = make_question(qtype, difficulty)
        except (ValueError, Exception):
            continue
        if q["signature"] not in used_sigs:
            return q
    return None


def _call_claude(qtype: str, difficulty: str, session_date: str) -> dict | None:
    """Call claude CLI for creative question types. Returns question dict or None."""
    category = qtype.replace("-", " ")
    prompt = (
        f"Generate one Hebrew math question for a 4th-grade Israeli student. "
        f"Category: {category}. Difficulty: {difficulty}. "
        f"Respond with JSON only, no markdown: "
        f'{{\"description\": \"<Hebrew instruction>\", '
        f'\"exercise\": \"<pure math expression, no Hebrew>\", '
        f'\"answer\": \"<answer>\", '
        f'\"answer_type\": \"numeric or categorical\"}}'
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        # Handle Claude's output-format json wrapper
        if isinstance(data, dict) and "result" in data:
            data = json.loads(data["result"]) if isinstance(data["result"], str) else data["result"]
        sig = f"wordproblem:{qtype}:{difficulty}"
        exercise = data.get("exercise", "")
        if re.search(r'[\u05D0-\u05EA]', exercise):
            import warnings
            warnings.warn(f"Claude returned Hebrew in exercise field: {exercise!r}")
        return {
            "description": data.get("description", ""),
            "exercise": exercise,
            "answer": str(data.get("answer", "")),
            "answer_type": data.get("answer_type", "numeric"),
            "type": qtype,
            "subtopic": qtype,
            "signature": sig,
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, FileNotFoundError):
        return None


def generate_session(
    count: int = 8,
    topics_override: list = None,
    difficulty_override: str = None,
    session_date: str = None,
) -> list:
    """Generate a full session of questions.

    Returns list of question dicts with id field added.
    """
    if session_date is None:
        session_date = date.today().isoformat()

    summary = read_summary()
    used_sigs = _recent_sigs(summary)

    plan = build_session_plan(
        count=count,
        topics_override=topics_override,
        difficulty_override=difficulty_override,
    )

    questions = []
    q_id = 1

    for slot in plan:
        qtype = slot["qtype"]
        difficulty = slot["difficulty"]
        q = None

        if qtype in CLAUDE_TOPICS:
            # Direct Claude call for these types
            q = _call_claude(qtype, difficulty, session_date)
        else:
            # Template engine first
            q = _generate_template_question(qtype, difficulty, used_sigs)
            if q is None:
                # Exhausted template pool — fall back to Claude
                q = _call_claude(qtype, difficulty, session_date)

        if q is None:
            # Last resort: generate without dedup check
            try:
                q = make_question(qtype, difficulty)
            except ValueError:
                continue

        q["id"] = q_id
        q["date"] = session_date
        q["difficulty"] = difficulty
        used_sigs.add(q["signature"])
        questions.append(q)
        q_id += 1

    return questions
