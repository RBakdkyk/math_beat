"""WhatsApp formatter — converts generated session to numbered Hebrew text."""

from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent))

from curriculum import BLOCK_HEADERS, TOPICS

def _format_date(iso_date: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except ValueError:
        return iso_date


def format_session(questions: list, session_date: str) -> str:
    """Format a list of question dicts as WhatsApp-ready Hebrew text.

    Output: numbered list with block headers, plain text only.
    No LaTeX, no markdown, no emoji. Fractions as 1/2, multiplication as ×.
    """
    if not questions:
        return ""

    lines = [f"Daily Practice - {_format_date(session_date)}", ""]

    current_block = None
    for q in questions:
        qtype = q.get("subtopic", q.get("type", ""))
        block_header = BLOCK_HEADERS.get(qtype, TOPICS.get(qtype, {}).get("name", qtype))

        if block_header != current_block:
            if current_block is not None:
                lines.append("")
            lines.append(f"{block_header}:")
            current_block = block_header

        if "description" in q:
            lines.append(f"{q['id']}. {q['description']}")
            if q.get("exercise"):
                lines.append(f"   {q['exercise']}")
        else:
            lines.append(f"{q['id']}. {q.get('he', '')}")

    return "\n".join(lines)
