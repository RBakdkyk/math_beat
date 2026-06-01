## Context

The backend produces a session as `wiki/sessions/{date}/generated.json` — a list of question dicts, each carrying `description` (Hebrew instruction), `exercise` (pure math), `answer` (correct answer string), `answer_type` (`numeric`/`categorical`), `type`/`subtopic`, `signature`, `id`, and `difficulty`. Delivery is currently WhatsApp text via `formatter.py`, and results return ad-hoc for the parent to feed into `/results`.

Importantly, `/results` is a **markdown skill executed by the LLM**, not a Python module: "the skill determines correctness" means the model judges the child's answer against the known correct answer (e.g. "she wrote 54, correct is 56 → wrong"). There is no reusable Python answer-matching function. `progress.py`/`summary.json` store only a boolean `correct` per question (plus per-fact counts for multiplication) — not the literal wrong answer.

This change adds an HTML delivery layer between generation and `/results`. The child opens a self-contained quiz, types answers, and sends them back to the parent in one tap via a pre-filled WhatsApp message. The parent pastes the code into `/results`, which decodes it and grades it exactly as it grades natural-language reports today. Constraints: stdlib-only Python, no external JS/CSS/CDN, Hebrew RTL, must open offline on both phone and computer (including WhatsApp's in-app browser).

## Goals / Non-Goals

**Goals:**
- Turn a session's `generated.json` into a single self-contained `quiz.html` (inline CSS + JS, zero network dependencies).
- Free-text answer entry (no multiple choice, no distractors).
- A compact, machine-generated result code carrying the session date + all of the child's typed answers + a checksum.
- One-tap return via `wa.me` pre-filled message, with an on-screen copy fallback.
- `/results` accepts the pasted code, validates the checksum, decodes against `generated.json`, and grades the answers using its existing LLM judgment.

**Non-Goals:**
- No server, hosting, or URL-based delivery — the `.html` is sent manually as a WhatsApp document.
- **No in-browser grading and no embedded correct answers** — the page is a pure collect-and-send form; it cannot show the child a score.
- No replacement of the WhatsApp text formatter — it stays as a zero-dependency fallback.
- No reframing of question semantics (yes/no questions stay yes/no; free-text entry sidesteps the "3 options" problem).
- **No change to `progress-tracking` / `summary.json`** — specific wrong answers are surfaced via `results.json` notes; adaptive selection keeps running off `correct_rate` per topic.

## Decisions

### Decision: Free-text entry instead of multiple choice
The original idea was 3-option multiple choice, which required generating 2 plausible distractors per question and broke down for naturally binary (yes/no) questions. Free-text entry eliminates distractor generation entirely and renders uniformly for numeric and categorical questions alike.
**Alternatives considered:** Multiple choice with rule-based distractors (large hand-written misconception catalog + binary-question awkwardness); Claude-generated distractors (slow, daily dependency).

### Decision: The LLM grades; the HTML holds no answers
Grading is done by the `/results` skill's existing LLM judgment — the same mechanism that already grades natural-language reports. Consequently the quiz does not embed correct answers and does not self-grade. This keeps a single source of truth for correctness, avoids duplicating fragile Hebrew/fraction matching into JavaScript, and removes the "child can view-source the answers" risk.
**Trade-off accepted:** the page cannot give the child instant feedback (no score/✓✗). This is acceptable because the priority is reliable result return, not gamification.
**Alternatives considered:** Embed answers and self-grade in JS for child feedback (duplicates matching logic, divergence risk, view-source cheating); build a new shared Python `match_answer()` (net-new work not needed once the LLM is the grader).

### Decision: Comparison questions use tappable sign buttons (not free text)
Discovered during live testing: a `<`/`>` typed into a free-text box on an RTL page mirrors visually, so the child's correct comparison was captured as the opposite sign. Fraction-comparison answers are a finite set (`<`, `=`, `>`), so for that question type only, the quiz renders three tappable sign buttons in a forced-LTR row between the two fractions; the tapped sign is stored verbatim and `/results` maps it to the stored answer (bigger fraction or "שווים"). This is not "multiple choice with distractors" — it is the natural finite answer space of a comparison, and it removes the RTL ambiguity entirely.
**Alternatives considered:** force `dir=ltr` on the text box (still lets a misread produce the wrong sign); ask her to type the bigger fraction (matches the stored answer but is a less natural task than picking a sign).

### Decision: Result code = date + all typed answers + checksum
Because the page can't determine right/wrong, the code carries **all** of the child's answers in question order (blanks for unanswered), not just wrong ones. The code is built by the page and carried verbatim by WhatsApp, so it can be richer than a hand-typed string. Shape (illustrative): a recognizable prefix, the session date, an encoded ordered list of `{question id → typed answer}`, and a trailing checksum character. Encoding MUST safely round-trip Hebrew text and fractions (e.g. `/`) through a `wa.me` URL — so the answer payload uses a transport-safe encoding (e.g. base64 of a small JSON), then the whole code is URL-encoded; the checksum is computed over the canonical payload.
**Alternatives considered:** Right/wrong bitmask (impossible — the page can't grade); screenshot the parent eyeballs (manual, lossy, no clean parse).

### Decision: Blank answers count as wrong
An unanswered question is carried as a blank in the code. Because the quiz is self-administered (the child had the question in front of her), a blank is treated as **wrong** — `/results` writes a `results.json` entry with `correct: false` and a note ("left blank"), so it counts against `correct_rate` and the adaptive engine targets it. This needs no `progress.py` change: the entry is present, so the existing pipeline counts it like any other wrong answer.
**Note on divergence:** the natural-language manual path still *omits* unreported questions (parent silence = unknown, not failure). Only the quiz-code path treats a blank as wrong, because there the blank is an observed non-answer rather than missing data.
**Alternative considered:** treat blank as skipped/omitted (matches the manual path, but for a self-administered quiz a blank is real evidence of difficulty, not a data gap).

### Decision: Deterministic decode in Python, grading by the LLM
The `/results` markdown skill shells out to Python (as it already does for session discovery) to **decode** the code: validate the checksum and produce a clean `[{id, typed_answer}]` list. The skill then grades that list with its existing LLM judgment and writes `results.json`. The decoder lives in a small named module (e.g. `src/quizcode.py`) so the same canonical format is implemented once for encode-reference and once for decode.
**Alternatives considered:** Decode inside the markdown/LLM (error-prone for base64 + checksum); a standalone CLI (heavier than an inline `python -c` call).

### Decision: One-tap return via `wa.me`, copy fallback
A `שלחי לאבא` button links to `wa.me/<parent-number>?text=<url-encoded-code>`. On phone it opens the WhatsApp app; on desktop, WhatsApp Web — both with the code pre-filled. The parent number lives in a small config value baked into the generated HTML and MUST be in international format with no `+`. A copy-the-code block is always shown as a fallback for browsers where `wa.me` misbehaves (notably some in-app browsers).
**Alternatives considered:** Hosted page that POSTs results (reintroduces a server); pure copy-code (more friction for a 9-year-old).

### Decision: Build as a small module + CLI, parallel to the text formatter
A `src/quiz.py` builds the HTML string from a questions list; a thin CLI (`build_quiz.py`, mirroring `generate.py` conventions) writes `wiki/sessions/{date}/quiz.html`, write-once unless `--force`. It may also be invoked from the `/practice` flow.

## Risks / Trade-offs

- **Encoder/decoder drift** (page encode vs Python decode disagree on Hebrew/fraction escaping or checksum) → Define one canonical, documented code format in `src/quizcode.py`; add round-trip tests over representative sessions (numeric, fraction, Hebrew categorical answers).
- **No instant feedback for the child** → Accepted trade-off; priority is reliable return, not gamification. The text formatter and future iterations remain options if feedback becomes desired.
- **`wa.me` unreliable in WhatsApp's in-app browser** → Always render the copy-code fallback; instruct opening in a real browser. Text formatter remains as ultimate fallback.
- **WhatsApp sends `.html` as a download, not an inline page (2-tap open)** → Accept as inherent to manual file delivery; document the open-in-browser step.
- **Long code / long `wa.me` URL** (all answers carried, URL-encoded Hebrew ≈ 9 chars/char) → The child never types the code, so length mainly stresses URL limits; keep answers compact and test with a worst-case Hebrew-heavy session. Copy fallback covers any link-length failure.
- **`he`-only questions**: `formatter.py` still has a `q['he']` fallback for questions lacking `description`/`exercise` → the builder SHALL render `description`+`exercise` when present and fall back to `he`, so no question renders blank.
- **Wrong answers not in `summary.json`** → By design: they live in `results.json` notes for the parent; adaptive selection runs off `correct_rate`. Revisit only if misconception-driven selection is ever wanted.

## Open Questions

- Exact code grammar and encoding for the answer payload (base64 of small JSON vs a custom delimiter scheme) — to be fixed in `src/quizcode.py` and locked by round-trip tests.
- Whether quiz building is auto-triggered by `/practice` or stays a separate `build_quiz.py` step the parent runs.
- Whether to also embed a minimal printable/text fallback inside the HTML for fully offline, no-WhatsApp situations.
