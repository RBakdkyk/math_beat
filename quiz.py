#!/usr/bin/env python3
"""quiz.py — wrap a session's generated.json into a self-contained quiz.html.

The HTML carries questions only (no answer key); the child solves on her phone
and the "Done" button returns her answers as a single `AYL~…` code over WhatsApp,
which the parent pastes into `/results`. Needs-visual topics (geometry, symmetry)
are excluded with a warning. See openspec/changes/quiz-roundtrip.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from wiki import read_generated, session_dir
from curriculum import is_quiz_renderable
from envfile import parent_whatsapp

CANONICAL_COMPARISON_PROMPT = "סמני > או < או ="


def _render_data(questions: list) -> tuple:
    """Project questions to answer-free render dicts; return (rendered, excluded).

    Strips the `answer` key entirely. Applies the fraction-comparison render
    override (canonical prompt + `>`/`<`/`=` buttons) regardless of stored
    description. Excludes needs-visual topics.
    """
    rendered, excluded = [], []
    for q in questions:
        qtype = q.get("type", "")
        if not is_quiz_renderable(qtype):
            excluded.append(q)
            continue
        if qtype == "fraction-comparison":
            widget, options = "choice", [">", "<", "="]
            prompt = CANONICAL_COMPARISON_PROMPT
        else:
            widget = q.get("widget", "text")
            options = q.get("options") if widget == "choice" else None
            prompt = q.get("description", "")
        item = {
            "id": q["id"],
            "prompt": prompt,
            "exercise": q.get("exercise", ""),
            "widget": widget,
        }
        if options is not None:
            item["options"] = options
        rendered.append(item)
    return rendered, excluded


def build_html(date: str, wa_number: str, rendered: list) -> str:
    questions_json = json.dumps(rendered, ensure_ascii=False)
    return _HTML_TEMPLATE.format(
        date=date,
        wa=wa_number,
        questions=questions_json,
    )


class QuizError(Exception):
    """A user-facing failure while wrapping a session into quiz.html."""


def write_quiz(date: str, questions: list, force: bool = False, warn=None) -> tuple:
    """Render `questions` to <session>/quiz.html for `date`.

    Returns (out_path, n_rendered, excluded). Raises QuizError with a
    user-facing message on any failure (missing WhatsApp number, nothing
    renderable, or an existing file without `force`). `warn`, if given, is
    called once per excluded needs-visual question with a formatted message.
    """
    wa_number = parent_whatsapp()
    if not wa_number:
        raise QuizError("PARENT_WHATSAPP must be set in .env (e.g. PARENT_WHATSAPP=+972 50-123-4567).")

    rendered, excluded = _render_data(questions)
    if warn:
        for q in excluded:
            warn(f"Warning: excluding needs-visual question id={q['id']} "
                 f"({q.get('type')}): {q.get('description','')} {q.get('exercise','')}".rstrip())

    if not rendered:
        raise QuizError(f"No quiz-renderable questions for {date}; nothing written.")

    out_path = session_dir(date) / "quiz.html"
    if out_path.exists() and not force:
        raise QuizError(f"{out_path} already exists. Pass --force to overwrite.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_html(date, wa_number, rendered), encoding="utf-8")
    return out_path, len(rendered), excluded


def main():
    parser = argparse.ArgumentParser(description="Wrap a session into a self-contained HTML quiz.")
    parser.add_argument("date", help="Session date YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing quiz.html")
    args = parser.parse_args()

    questions = read_generated(args.date)
    if questions is None:
        print(f"No session found for {args.date}. Generate one first with: python generate.py --date {args.date}",
              file=sys.stderr)
        sys.exit(1)

    try:
        out_path, n_rendered, excluded = write_quiz(
            args.date, questions, force=args.force,
            warn=lambda m: print(m, file=sys.stderr),
        )
    except QuizError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {out_path} ({n_rendered} questions"
          + (f", {len(excluded)} excluded" if excluded else "") + ").")


# ─── Self-contained HTML (inline CSS/JS, no external assets) ──────────────────
# {date}, {wa}, {questions} are filled by str.format; literal CSS/JS braces are
# doubled. The JS checksum/base64 mirror src/codec.py so a browser-built code
# validates unchanged in the /results decode branch.

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>תרגול - {date}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 0;
          background: #f4f6fb; color: #1a2233; direction: rtl; }}
  header {{ background: #3b5bdb; color: #fff; padding: 18px 16px; }}
  header h1 {{ margin: 0; font-size: 20px; }}
  header .date {{ opacity: .85; font-size: 14px; margin-top: 4px; }}
  main {{ padding: 12px 14px 110px; max-width: 640px; margin: 0 auto; }}
  .q {{ background: #fff; border-radius: 12px; padding: 14px 16px; margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .q .num {{ color: #3b5bdb; font-weight: 700; font-size: 14px; }}
  .q .prompt {{ font-size: 17px; margin: 4px 0 8px; }}
  .q .exercise {{ direction: ltr; text-align: left; unicode-bidi: isolate;
        font-size: 22px; font-weight: 600; letter-spacing: .5px; margin: 6px 0 12px;
        font-family: "SF Mono", Menlo, Consolas, monospace; }}
  .q input[type=text] {{ width: 100%; font-size: 22px; padding: 10px 12px;
        border: 2px solid #cdd6ea; border-radius: 10px; direction: ltr; text-align: left; }}
  .choices {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .choices button {{ flex: 1 1 auto; min-width: 64px; font-size: 20px; padding: 12px;
        border: 2px solid #cdd6ea; border-radius: 10px; background: #fff; cursor: pointer; }}
  .choices button.sel {{ background: #3b5bdb; color: #fff; border-color: #3b5bdb; }}
  footer {{ position: fixed; bottom: 0; left: 0; right: 0; background: #fff;
        padding: 12px 14px; box-shadow: 0 -1px 6px rgba(0,0,0,.1); }}
  #done {{ width: 100%; font-size: 19px; font-weight: 700; padding: 14px;
        background: #2f9e44; color: #fff; border: none; border-radius: 12px; cursor: pointer; }}
  #code {{ margin-top: 10px; font-family: monospace; font-size: 12px; word-break: break-all;
        direction: ltr; text-align: left; color: #555; display: none; }}
</style>
</head>
<body>
<header>
  <h1>תרגול יומי</h1>
  <div class="date">{date}</div>
</header>
<main id="quiz"></main>
<footer>
  <button id="done">סיימתי - שליחה ב-WhatsApp ✓</button>
  <div id="code"></div>
</footer>
<script>
const DATE = "{date}";
const WA = "{wa}";
const QUESTIONS = {questions};
const BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz";

function checkChar(date, b64) {{
  const s = "AYL~" + date + "~" + b64;
  let sum = 0;
  for (let i = 0; i < s.length; i++) sum += s.charCodeAt(i);
  return BASE36[sum % 36];
}}

function utf8ToB64(str) {{
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/=+$/, "");  // standard base64, padding stripped
}}

const answers = {{}};  // id -> string

function render() {{
  const root = document.getElementById("quiz");
  QUESTIONS.forEach((q, i) => {{
    const card = document.createElement("div");
    card.className = "q";
    const num = document.createElement("div");
    num.className = "num";
    num.textContent = "שאלה " + (i + 1);
    card.appendChild(num);
    const prompt = document.createElement("div");
    prompt.className = "prompt";
    // >, <, = are bidi-mirrored in this RTL page; isolate each symbol run as LTR
    // so it keeps its glyph (otherwise ">" would display — and read — as "<").
    q.prompt.split(/([<>=]+)/).forEach(part => {{
      if (/[<>=]/.test(part)) {{
        const span = document.createElement("span");
        span.dir = "ltr";
        span.textContent = part;
        prompt.appendChild(span);
      }} else if (part) {{
        prompt.appendChild(document.createTextNode(part));
      }}
    }});
    card.appendChild(prompt);
    if (q.exercise) {{
      const ex = document.createElement("div");
      ex.className = "exercise";
      ex.dir = "ltr";
      ex.textContent = q.exercise;
      card.appendChild(ex);
    }}
    if (q.widget === "choice") {{
      const wrap = document.createElement("div");
      wrap.className = "choices";
      (q.options || []).forEach(opt => {{
        const b = document.createElement("button");
        b.type = "button";
        if (/[<>=]/.test(opt)) b.dir = "ltr";  // keep >,<,= from bidi-mirroring
        b.textContent = opt;
        b.onclick = () => {{
          answers[q.id] = opt;
          wrap.querySelectorAll("button").forEach(x => x.classList.remove("sel"));
          b.classList.add("sel");
        }};
        wrap.appendChild(b);
      }});
      card.appendChild(wrap);
    }} else {{
      const inp = document.createElement("input");
      inp.type = "text";              // never type=number: must accept / , . -
      inp.inputMode = "text";
      inp.autocomplete = "off";
      inp.oninput = () => {{ answers[q.id] = inp.value; }};
      card.appendChild(inp);
    }}
    root.appendChild(card);
  }});
}}

function buildCode() {{
  const arr = QUESTIONS.map(q => [q.id, (answers[q.id] || "").trim()]);
  const json = JSON.stringify(arr);
  const b64 = utf8ToB64(json);
  return "AYL~" + DATE + "~" + b64 + "~" + checkChar(DATE, b64);
}}

document.getElementById("done").onclick = () => {{
  const code = buildCode();
  const box = document.getElementById("code");
  box.style.display = "block";
  box.textContent = code;
  window.location.href = "https://wa.me/" + WA + "?text=" + encodeURIComponent(code);
}};

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
