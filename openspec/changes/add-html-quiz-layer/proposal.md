## Why

Today a session is delivered to Ayala as WhatsApp text and her answers come back ad-hoc, forcing the parent to manually reconstruct what she answered before `/results` can record anything. This is error-prone and loses detail. A self-contained HTML quiz she can open on phone or computer — that collects her answers and sends them back in one tap — closes the loop reliably and feeds the adaptive engine with what is actually hard for her.

## What Changes

- Add a new layer that turns a session's `generated.json` into a self-contained `quiz.html` (inline CSS + JS, no network/CDN dependencies) saved to `wiki/sessions/{date}/quiz.html`.
- The quiz renders each question's Hebrew `description` + `exercise` with a **free-text answer box** (no multiple choice, no distractors), laid out RTL, working offline on phone and computer.
- The quiz does **not** embed correct answers and does **not** grade — it is a pure collect-and-send form. Grading is performed later by the `/results` skill's existing (LLM-based) judgment, keeping a single source of truth for correctness.
- On finish, the page builds a compact **result code** carrying: session date + **all of the child's typed answers** (in question order) + a checksum character. Unanswered questions are carried as blanks.
- A one-tap **"שלחי לאבא" WhatsApp button** opens `wa.me/<parent-number>?text=<code>` pre-filled with the code (parent number from a small config); a copy-the-code fallback is shown in case `wa.me` misbehaves in her browser.
- `/results` is extended to accept a pasted result code, validate its checksum, decode it against the matching session's `generated.json`, and grade the decoded answers the way it already grades natural-language reports — writing `results.json` (with notes capturing specific wrong answers) and updating `summary.json`.
- The WhatsApp text formatter is unchanged and remains a zero-dependency fallback delivery format.

## Capabilities

### New Capabilities
- `html-quiz`: Building a self-contained, offline, RTL Hebrew `quiz.html` from a session's `generated.json` (questions + free-text inputs only, no embedded answers, no grading), including result-code generation (date + all typed answers + checksum) and the WhatsApp pre-filled return button with copy fallback.

### Modified Capabilities
- `results-skill`: `/results` SHALL additionally accept a pasted result code, validate its checksum, decode it against the matching session's `generated.json`, and grade the decoded answers using its existing judgment — recording specific wrong answers as notes in `results.json`.

## Impact

- **New code**: a quiz builder (e.g. `src/quiz.py`) and a CLI entry point (e.g. `build_quiz.py`, or folded into the `/practice` flow); a small config value for the parent WhatsApp number; a small Python code-decoder used by `/results`.
- **Modified code**: `/results` skill instructions (`.claude/skills/results.md` and `.claude/commands/results.md` — kept in sync) and supporting decode logic.
- **New artifact per session**: `wiki/sessions/{date}/quiz.html`.
- **Shared contract**: the result-code format is the contract between `quiz.html` (encoder) and `/results` (decoder) — both must agree on encoding, escaping (Hebrew + fractions), and checksum.
- **Out of scope**: no change to `progress-tracking` / `summary.json` schema. Specific wrong answers are surfaced for the parent via `results.json` notes; adaptive selection continues to run off `correct_rate` per topic as it does today.
- **No new runtime dependencies**: stdlib-only Python; the HTML uses only inline vanilla JS/CSS. Consistent with the project's no-external-dependencies convention.
