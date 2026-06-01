"""Local configuration values for ayala_math.

PARENT_WHATSAPP_NUMBER is baked into each generated quiz.html so the child's
"שלחי לאבא" button opens a pre-filled WhatsApp message to the parent.

Format: international, digits only, NO leading "+" and no spaces/dashes
(this is what wa.me expects). Example for an Israeli number 050-123-4567:
"972501234567".

The number is read from `.env` (gitignored) or the AYALA_PARENT_WHATSAPP
environment variable — it is NOT committed to the repo. See `.env.example`.
"""

import os
from pathlib import Path

_ENV_PATH = Path(__file__).parent.parent / ".env"
_PLACEHOLDER = "972500000000"


def _load_dotenv(path: Path) -> None:
    """Minimal stdlib .env loader: KEY=VALUE per line, '#' comments.

    Does not override variables already present in the real environment.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parent_whatsapp_number() -> str:
    """Resolve the parent WhatsApp number: real env var / .env, else placeholder."""
    _load_dotenv(_ENV_PATH)
    return os.environ.get("AYALA_PARENT_WHATSAPP", _PLACEHOLDER)
