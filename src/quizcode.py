"""Result-code contract shared by quiz.html (encoder) and /results (decoder).

The HTML quiz collects the child's typed answers and packs them into a compact,
URL-safe code she sends back over WhatsApp. `/results` decodes that code, then
grades the answers with the skill's usual judgment.

Canonical format
----------------

    AYL~<date>~<b64>~<chk>

  - ``AYL``   fixed prefix (recognizes our codes)
  - ``date``  session date, ``YYYY-MM-DD``
  - ``b64``   base64url (no padding) of a JSON ordered list ``[[id, answer], ...]``
              — all questions, in order, blanks carried as ``""``
  - ``chk``   single checksum char over the canonical payload ``AYL~<date>~<b64>``

The separator ``~`` is a URL-unreserved character that never appears in the
date, the base64url alphabet (``A-Za-z0-9-_``), or the prefix — so splitting is
unambiguous and the whole code passes through a ``wa.me?text=`` URL untouched.
Hebrew text and fractions ("4/5") survive because the answers are UTF-8 JSON
inside base64; only ASCII reaches the URL.

The JavaScript encoder in quiz.html mirrors this exactly; this module is the
authoritative reference encoder + the decoder used by /results.
"""

import base64
import json

PREFIX = "AYL"
SEP = "~"
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"  # base-36, single-char checksum


def _checksum(canonical: str) -> str:
    """Single-char base-36 checksum over the canonical (ASCII) payload."""
    total = sum(ord(c) for c in canonical)
    return _ALPHABET[total % 36]


def _b64encode(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(b64: str):
    pad = "=" * (-len(b64) % 4)
    raw = base64.urlsafe_b64decode(b64 + pad)
    return json.loads(raw.decode("utf-8"))


def encode(answers, date: str) -> str:
    """Build a result code.

    answers: ordered iterable of (id, answer) pairs or {"id", "answer"} dicts.
             Every question in the session SHOULD appear; blanks are "".
    date:    session date string, "YYYY-MM-DD".
    """
    pairs = []
    for a in answers:
        if isinstance(a, dict):
            qid, ans = a["id"], a.get("answer", "")
        else:
            qid, ans = a[0], a[1]
        pairs.append([int(qid), "" if ans is None else str(ans)])

    b64 = _b64encode(pairs)
    canonical = f"{PREFIX}{SEP}{date}{SEP}{b64}"
    return f"{canonical}{SEP}{_checksum(canonical)}"


def decode(code: str) -> dict:
    """Decode and validate a result code.

    Returns {"date": str, "answers": [{"id": int, "answer": str}, ...]}.
    Raises ValueError on malformed code or checksum mismatch.
    """
    if not isinstance(code, str):
        raise ValueError("code must be a string")
    code = code.strip()

    parts = code.split(SEP)
    if len(parts) != 4:
        raise ValueError("malformed code: expected 4 segments")
    prefix, date, b64, chk = parts
    if prefix != PREFIX:
        raise ValueError(f"malformed code: bad prefix {prefix!r}")

    canonical = f"{prefix}{SEP}{date}{SEP}{b64}"
    if _checksum(canonical) != chk:
        raise ValueError("checksum mismatch — code may be corrupted; re-send it")

    try:
        pairs = _b64decode(b64)
    except Exception as e:  # noqa: BLE001 — any decode failure is a bad code
        raise ValueError(f"malformed code: undecodable payload ({e})")

    answers = [{"id": int(qid), "answer": str(ans)} for qid, ans in pairs]
    return {"date": date, "answers": answers}
