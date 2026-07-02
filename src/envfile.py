"""Minimal stdlib-only `.env` reader (no third-party dependency).

Used to read `PARENT_WHATSAPP` for the quiz's WhatsApp "Done" link. `.env` is
gitignored so the number never lands in a commit.
"""

from __future__ import annotations

import re
from pathlib import Path

_ENV_PATH = Path(__file__).parent.parent / ".env"


def read_env(path: Path | str | None = None) -> dict:
    """Parse a `.env` file into a dict. Ignores blanks and `#` comments.

    Accepts `KEY=VALUE`; trims whitespace and strips one layer of surrounding
    single/double quotes from the value. Missing file → empty dict.
    """
    p = Path(path) if path is not None else _ENV_PATH
    data: dict = {}
    if not p.exists():
        return data
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key:
            data[key] = val
    return data


def parent_whatsapp(path: Path | str | None = None) -> str | None:
    """Return `PARENT_WHATSAPP` normalized to digits-only `wa.me` form, or None.

    `+972 50-123-4567` → `972501234567`.
    """
    val = read_env(path).get("PARENT_WHATSAPP")
    if not val:
        return None
    digits = re.sub(r"\D", "", val)
    return digits or None
