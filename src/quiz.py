"""Quiz HTML builder — turns a session's questions into a self-contained quiz.html.

The page is a pure collect-and-send form: it renders each question with a
free-text box, and on finish packs the child's answers into a result code
(see quizcode.py for the shared format) and offers a one-tap WhatsApp button
plus a copy fallback. It embeds NO correct answers and does NO grading —
grading happens later in /results.
"""

import html
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from curriculum import BLOCK_HEADERS, TOPICS  # noqa: E402


def _question_text(q: dict) -> tuple[str, str]:
    """Return (instruction, exercise) display strings, with he-only fallback."""
    if "description" in q or "exercise" in q:
        return q.get("description", ""), q.get("exercise", "")
    # Legacy questions carry a single combined Hebrew field.
    return q.get("he", ""), ""


def _block_header(q: dict) -> str:
    qtype = q.get("subtopic", q.get("type", ""))
    return BLOCK_HEADERS.get(qtype, TOPICS.get(qtype, {}).get("name", qtype))


def _render_questions(questions: list) -> str:
    rows = []
    current_block = None
    for q in questions:
        block = _block_header(q)
        if block != current_block:
            rows.append(f'    <h2 class="block">{html.escape(block)}</h2>')
            current_block = block

        qid = q["id"]
        qtype = q.get("subtopic", q.get("type", ""))
        instruction, exercise = _question_text(q)
        parts = [f'    <div class="q">']
        parts.append(f'      <div class="qnum">{qid}.</div>')
        parts.append('      <div class="qbody">')
        if instruction:
            parts.append(f'        <div class="instr">{html.escape(instruction)}</div>')

        if qtype == "fraction-comparison" and "___" in exercise:
            # Comparison answers are the finite set <, =, >. A free-text box in an
            # RTL page mirrors these signs, so we render tappable buttons in a
            # forced-LTR row (left fraction · buttons · right fraction). The tapped
            # sign is stored in a hidden input; /results maps it to the answer.
            left, right = (p.strip() for p in exercise.split("___", 1))
            parts.append('        <div class="cmp-row">')
            parts.append(f'          <span class="cmp-frac">{html.escape(left)}</span>')
            for sign in ("<", "=", ">"):
                parts.append(
                    f'          <button type="button" class="cmp-btn" '
                    f'data-target="q_{qid}" data-sign="{sign}">{sign}</button>'
                )
            parts.append(f'          <span class="cmp-frac">{html.escape(right)}</span>')
            parts.append('        </div>')
            parts.append(f'        <input type="hidden" id="q_{qid}" data-qid="{qid}" value="" />')
        else:
            if exercise:
                parts.append(f'        <div class="ex">{html.escape(exercise)}</div>')
            parts.append(
                f'        <input class="ans" id="q_{qid}" data-qid="{qid}" '
                f'type="text" autocomplete="off" inputmode="text" />'
            )

        parts.append('      </div>')
        parts.append('    </div>')
        rows.append("\n".join(parts))
    return "\n".join(rows)


# JS encoder — MUST mirror quizcode.py (PREFIX, SEP, base-36 checksum, base64url
# of compact JSON [[id, answer], ...]). Kept inline so the page is self-contained.
_JS = """
  const PREFIX = "AYL", SEP = "~";
  const ALPH = "0123456789abcdefghijklmnopqrstuvwxyz";

  function b64url(str) {
    const bytes = new TextEncoder().encode(str);
    let bin = "";
    for (const b of bytes) bin += String.fromCharCode(b);
    return btoa(bin).replace(/\\+/g, "-").replace(/\\//g, "_").replace(/=+$/, "");
  }
  function checksum(s) {
    let t = 0;
    for (let i = 0; i < s.length; i++) t += s.charCodeAt(i);
    return ALPH[t % 36];
  }
  function buildCode(pairs, date) {
    const b64 = b64url(JSON.stringify(pairs));
    const canonical = PREFIX + SEP + date + SEP + b64;
    return canonical + SEP + checksum(canonical);
  }

  function finish() {
    const pairs = QIDS.map(function (id) {
      const el = document.getElementById("q_" + id);
      return [id, el ? el.value.trim() : ""];
    });
    const code = buildCode(pairs, SESSION_DATE);
    document.getElementById("code").textContent = code;
    const wa = "https://wa.me/" + PARENT_NUMBER + "?text=" + encodeURIComponent(code);
    document.getElementById("send").setAttribute("href", wa);
    document.getElementById("result").style.display = "block";
    document.getElementById("result").scrollIntoView({ behavior: "smooth" });
  }

  function copyCode() {
    const code = document.getElementById("code").textContent;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code);
    } else {
      const r = document.createRange();
      r.selectNode(document.getElementById("code"));
      const s = window.getSelection();
      s.removeAllRanges();
      s.addRange(r);
      document.execCommand("copy");
    }
    document.getElementById("copied").style.display = "inline";
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("finishBtn").addEventListener("click", finish);
    document.getElementById("copyBtn").addEventListener("click", copyCode);

    document.querySelectorAll(".cmp-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        const target = b.getAttribute("data-target");
        document.getElementById(target).value = b.getAttribute("data-sign");
        document.querySelectorAll('.cmp-btn[data-target="' + target + '"]')
          .forEach(function (o) { o.classList.remove("selected"); });
        b.classList.add("selected");
      });
    });
  });
"""

_CSS = """
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "Segoe UI", Arial, sans-serif;
    direction: rtl; margin: 0; padding: 16px;
    background: #f4f7fb; color: #1c2733; line-height: 1.5;
  }
  .wrap { max-width: 560px; margin: 0 auto; }
  h1 { font-size: 1.4rem; margin: 0 0 4px; }
  .date { color: #5b6b7c; margin: 0 0 20px; }
  h2.block {
    font-size: 1.05rem; margin: 22px 0 8px; color: #2b5fa6;
    border-bottom: 2px solid #d7e3f3; padding-bottom: 4px;
  }
  .q {
    display: flex; gap: 10px; background: #fff; border: 1px solid #e1e8f0;
    border-radius: 12px; padding: 12px 14px; margin: 10px 0;
  }
  .qnum { font-weight: 700; color: #2b5fa6; min-width: 1.6em; }
  .qbody { flex: 1; }
  .instr { font-size: 0.98rem; }
  .ex { font-size: 1.25rem; font-weight: 600; margin: 4px 0 8px; direction: ltr; text-align: right; }
  input.ans {
    width: 100%; font-size: 1.2rem; padding: 10px 12px;
    border: 2px solid #c3d3e6; border-radius: 10px; text-align: center;
  }
  input.ans:focus { outline: none; border-color: #2b5fa6; }
  .cmp-row {
    direction: ltr; display: flex; align-items: center; justify-content: center;
    gap: 10px; margin-top: 6px;
  }
  .cmp-frac { font-size: 1.3rem; font-weight: 600; }
  .cmp-btn {
    width: auto; flex: 0 0 auto; min-width: 52px; margin: 0; padding: 10px 0;
    font-size: 1.4rem; background: #eef2f8; color: #2b5fa6; border: 2px solid #c3d3e6;
  }
  .cmp-btn.selected { background: #2b5fa6; color: #fff; }
  button {
    font-size: 1.15rem; font-weight: 700; padding: 14px 20px; width: 100%;
    border: none; border-radius: 12px; background: #2b5fa6; color: #fff;
    margin-top: 18px; cursor: pointer;
  }
  #result { display: none; background: #fff; border: 1px solid #e1e8f0;
    border-radius: 12px; padding: 16px; margin-top: 18px; text-align: center; }
  #result h3 { margin: 0 0 10px; }
  a.send {
    display: block; text-decoration: none; font-size: 1.2rem; font-weight: 700;
    padding: 14px 20px; border-radius: 12px; background: #25d366; color: #fff; margin: 8px 0;
  }
  .fallback { font-size: 0.85rem; color: #5b6b7c; margin-top: 14px; }
  #code {
    display: block; direction: ltr; word-break: break-all; background: #f0f4f9;
    border: 1px dashed #b7c6d8; border-radius: 8px; padding: 10px; margin: 8px 0;
    font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.8rem;
  }
  button.copy { background: #5b6b7c; }
  #copied { display: none; color: #1a9c52; font-weight: 700; margin-right: 8px; }
"""


def build_quiz(questions: list, session_date: str, parent_number: str) -> str:
    """Return a self-contained quiz.html string for the given questions.

    No correct answers are embedded and no grading is performed in the page.
    """
    qids = [q["id"] for q in questions]
    header = (
        f'  const SESSION_DATE = {json.dumps(session_date)};\n'
        f'  const PARENT_NUMBER = {json.dumps(str(parent_number))};\n'
        f'  const QIDS = {json.dumps(qids)};\n'
    )
    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>תרגול {html.escape(session_date)}</title>
<style>{_CSS}</style>
</head>
<body>
  <div class="wrap">
    <h1>תרגול יומי</h1>
    <p class="date">{html.escape(session_date)}</p>
{_render_questions(questions)}
    <button id="finishBtn">סיימתי ✓</button>

    <div id="result">
      <h3>כל הכבוד! 🎉</h3>
      <p>שלחי את התשובות לאבא:</p>
      <a id="send" class="send" href="#">שלחי לאבא 📩</a>
      <div class="fallback">
        אם הכפתור לא עובד, העתיקי את הקוד ושלחי בוואטסאפ:
        <code id="code"></code>
        <button id="copyBtn" class="copy">העתקת הקוד</button>
        <span id="copied">הועתק ✓</span>
      </div>
    </div>
  </div>
<script>
{header}{_JS}</script>
</body>
</html>
"""
