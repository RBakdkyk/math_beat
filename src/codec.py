"""Return-code envelope codec (stdlib only).

Wire format (recovered from three live codes — authoritative):

    AYL ~ <date> ~ <base64(JSON)> ~ <check>
    check = BASE36[ sum(bytes("AYL~" + date + "~" + b64)) % 36 ]
    BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"

PAYLOAD is JSON ``[[id, "answer"], …]`` carrying only RENDERED questions; an
``""`` answer means rendered-but-unanswered. base64 is STANDARD (not urlsafe);
decode tolerates missing padding. The same checksum is implemented in the quiz
HTML's JavaScript so a browser-built code validates here unchanged.
"""

from __future__ import annotations

import base64
import json
import re

BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"
MARKER = "AYL~"

# Anchors on the marker and matches date + standard-base64 charset + exactly one
# trailing check char, so surrounding text/emoji ("done! AYL~…~j 🎉") don't break it.
_CODE_RE = re.compile(r"AYL~(\d{4}-\d{2}-\d{2})~([A-Za-z0-9+/=]+)~([0-9A-Za-z])")


class CodeError(ValueError):
    """Raised when a code is malformed, fails its checksum, or has no payload."""


def check_char(date: str, b64: str) -> str:
    """check = BASE36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]."""
    material = (MARKER + date + "~" + b64).encode("utf-8")
    return BASE36[sum(material) % 36]


def encode(date: str, answers: list) -> str:
    """Encode ``[[id, "answer"], …]`` → ``AYL~<date>~<base64>~<check>``.

    Uses compact, non-ASCII-preserving JSON to mirror the browser's
    ``JSON.stringify`` so Python- and JS-built codes agree byte-for-byte.
    """
    payload = json.dumps(answers, ensure_ascii=False, separators=(",", ":"))
    # Standard base64 with trailing "=" padding stripped (the recovered format);
    # the check char is computed over this unpadded b64.
    b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{MARKER}{date}~{b64}~{check_char(date, b64)}"


def extract(text: str) -> str | None:
    """Pull a single ``AYL~…`` code out of surrounding text/emoji, or None."""
    m = _CODE_RE.search(text)
    return m.group(0) if m else None


def decode(text: str) -> tuple:
    """Extract, validate, and decode a code.

    Returns ``(date, [[id, "answer"], …])``. Raises :class:`CodeError` if no
    code is found, the checksum mismatches, or the payload is not valid JSON.
    The check char is compared case-insensitively to survive mobile autocorrect.
    """
    code = extract(text)
    if code is None:
        raise CodeError("No AYL~ code found in the pasted text.")
    m = _CODE_RE.search(code)
    date, b64, check = m.group(1), m.group(2), m.group(3)
    if check_char(date, b64) != check.lower():
        raise CodeError("The code looks corrupted (checksum mismatch). Please re-paste it.")
    padded = b64 + "=" * (-len(b64) % 4)
    try:
        payload = json.loads(base64.b64decode(padded))
    except (ValueError, json.JSONDecodeError) as exc:
        raise CodeError(f"The code's payload could not be decoded: {exc}")
    return date, payload
