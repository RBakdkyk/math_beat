## Why

Today the loop from generated session → recorded results runs through the conversational `/results` skill: the parent watches Ayala solve on paper, then verbally reports each answer for the model to grade. That works, but it puts the parent in the loop for every question and depends on the model eyeballing each answer.

A prior (unpushed, now-lost) version replaced the back half with a **phone round-trip**: the session is wrapped into a self-contained HTML quiz, sent to Ayala's phone over WhatsApp, solved on the phone, and her answers are returned as a single compact **code** that the parent pastes back here to trigger grading. Three real codes survived and were reverse-engineered, so the wire format is fully recovered:

```
AYL~<date>~<base64 JSON [[id,"answer"], …]>~<check>
check = base36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]
```

Decoded payloads (verified against the live `results.json` / `progress.py` shapes):

```
2026-06-08 → [[1,"7"],[2,"100"],[3,"25"],[4,"1720"],[5,"24300"],[6,"868"],[7,"256"],[8,"54"]]
2026-06-03 → [[1,"65"],[2,"54"],[3,"35"],[4,""],[5,""],[6,"44"],[7,"44"],[8,"1"]]      ← ""=skipped
2026-06-01 → [[1,"70"],[2,"5"],[3,"381,"],[4,"1,038"],[5,"151"],[6,"52.1"],[7,">"],[8,"40/32"]]
```

This change re-captures that round-trip as a real capability so it isn't lost again, with the grading subtleties the three codes exposed written down as explicit requirements.

## What Changes

- **Per-question widget metadata in `generated.json`** — the generator emits a `widget` (`text` | `choice`) and, for `choice`, an `options` list on each question. Widget/options are no longer inferable from `type` or `answer_type`, since one `type` mixes shapes (e.g. `exponents` emits numeric, typed-string `2^3`, and yes/no questions).
- **New quiz-generation capability** — a `quiz.py` wrap step turns a session's `generated.json` into a self-contained `quiz.html` saved at `wiki/sessions/{date}/quiz.html`. The HTML:
  - strips the answer key (grading stays on the parent's machine),
  - renders each question's Hebrew `description` + `exercise` with the input widget from its metadata (`text` → free-text field that accepts `/`,`,`,`.`; `choice` → option buttons),
  - presents every `fraction-comparison` question with the canonical prompt `"סמני > או < או ="` and `>`/`<`/`=` buttons,
  - bakes the parent's WhatsApp number (from `.env`) into a "Done" button that builds `https://wa.me/<number>?text=<encodeURIComponent(AYL~<date>~<base64>~<check>)>` (standard base64, percent-encoded so `+`/`/` survive),
  - **excludes** any question flagged *needs-visual* (`geometry`, `symmetry`) with a generation-time warning; excluded questions are absent from the rendered set and the return code.
- **New `/results` code branch** — `/results CODE:AYL~…` (and a plain pasted `AYL~…`) decodes the envelope instead of taking a verbal report:
  - validates the check char (case-insensitive) and rejects a corrupt/mangled paste,
  - reads the session date from the envelope (no discovery needed),
  - **omits blank `""` answers** (and ids absent from the payload) so skipped/excluded questions are not counted,
  - **normalizes** free-typed numbers before grading (strip `,` and trailing punctuation; keep `.` and `/`),
  - **strips units** from measurement answer keys before comparing (`"247 מ\"ר"` vs typed `247`),
  - **derives the comparison symbol** for `fraction-comparison`: the stored answer is the larger fraction (or `"שווים"` → `=`), so the grader parses the operands from `exercise`, determines the correct `</>/=`, and compares it to her tapped symbol,
  - **records her raw answer as the result note** (no human present to describe the mistake),
  - writes `results.json`, then runs `analyze.py {date}` first-time or `analyze.py --rebuild` on re-processing (to avoid double-counting), feeding `summary.json` → next-day selection unchanged.
- **`.env` handling** — read `PARENT_WHATSAPP` (digits only, `wa.me` form) with a stdlib-only `KEY=VALUE` parser; add `.env` to `.gitignore`.

The grading engine, progress merge, and next-day topic selection (`session.py`) are **reused unchanged** — the adaptive planner already produces template-only sessions, so the everyday quiz never contains a needs-visual topic.

## Capabilities

### Added Capabilities

- `quiz-generation`: wrap a session into a self-contained, answer-stripped HTML quiz with per-`answer_type` input widgets, a WhatsApp return-code button, and needs-visual exclusion.

### Modified Capabilities

- `results-skill`: accept a pasted `AYL~…` code as an input mode — validate the checksum, decode id-tagged answers, apply the normalization / unit-strip / comparison-symbol (incl. `"שווים"`) / blank-skip rules, record the raw answer as a note, then reuse the existing write + analyze flow with rebuild-on-reprocess.
- `curriculum-model`: topics gain a `quiz_renderable` / needs-visual classification, and each generated question gains `widget`/`options` metadata so the wrap step knows how to render or exclude it without inferring from `type`.

## Non-Goals

- Hosting the quiz anywhere — it is a local file the parent attaches in WhatsApp by hand.
- Instant on-phone feedback or scoring (no answer key on the phone; grading stays on the machine, as today).
- Rendering figure-dependent topics (`geometry`, `symmetry`) in the quiz.
- Automating the WhatsApp send or receive — the parent attaches the file and pastes the returned code manually.
- Changing the next-day selection logic in `session.py` (already consumes `summary.json`).
