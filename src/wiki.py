"""Wiki file helpers — read/write JSON, list sessions, overwrite protection."""

import json
from pathlib import Path
from datetime import date, datetime

WIKI_DIR = Path(__file__).parent.parent / "wiki"
SESSIONS_DIR = WIKI_DIR / "sessions"
PROGRESS_DIR = WIKI_DIR / "progress"
SUMMARY_PATH = PROGRESS_DIR / "summary.json"


def session_dir(session_date: str) -> Path:
    return SESSIONS_DIR / session_date


def generated_path(session_date: str) -> Path:
    return session_dir(session_date) / "generated.json"


def results_path(session_date: str) -> Path:
    return session_dir(session_date) / "results.json"


def quiz_path(session_date: str) -> Path:
    return session_dir(session_date) / "quiz.html"


def today() -> str:
    return date.today().isoformat()


def read_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data, force: bool = False) -> None:
    """Write JSON to path. Raises FileExistsError if file exists and not force."""
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_summary() -> dict:
    """Read summary.json, returning empty structure if missing."""
    data = read_json(SUMMARY_PATH)
    if data is None:
        return {"topics": {}}
    return data


def write_summary(data: dict) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_sessions() -> list:
    """Return sorted list of session date strings (YYYY-MM-DD)."""
    if not SESSIONS_DIR.exists():
        return []
    return sorted(d.name for d in SESSIONS_DIR.iterdir() if d.is_dir())


def recent_sessions(n: int = 10) -> list:
    """Return up to n most recent session dates."""
    return list_sessions()[-n:]


def read_generated(session_date: str) -> list | None:
    return read_json(generated_path(session_date))


def read_results(session_date: str) -> list | None:
    return read_json(results_path(session_date))


def write_generated(questions: list, session_date: str, force: bool = False) -> None:
    write_json(generated_path(session_date), questions, force=force)


def write_results(results: list, session_date: str, force: bool = False) -> None:
    write_json(results_path(session_date), results, force=force)
