## 1. Result-code contract

- [x] 1.1 Define the canonical result-code grammar in `src/quizcode.py`: prefix + session date + encoded ordered answer list (all questions, blanks allowed) + trailing checksum character
- [x] 1.2 Choose the answer-payload encoding that round-trips Hebrew + fractions through a `wa.me` URL (e.g. base64 of small JSON, then URL-encode)
- [x] 1.3 Define and implement the checksum over the canonical payload
- [x] 1.4 Implement `encode(answers, date)` (reference encoder) and `decode(code) -> {date, [{id, answer}]}` with checksum validation in `src/quizcode.py`; document the format as the shared page-encode / Python-decode contract

## 2. Quiz builder (Python)

- [x] 2.1 Add a parent-WhatsApp-number config value (single constant or small config), international format with no `+`, baked into the HTML
- [x] 2.2 Create `src/quiz.py` with `build_quiz(questions, session_date, parent_number) -> str` returning a self-contained HTML string (inline CSS + JS, no CDN/network, no embedded answers)
- [x] 2.3 Render each question with a free-text input, RTL; use `description`+`exercise` when present, else fall back to `he`; same mechanism for numeric and categorical
- [x] 2.4 Implement the JS finish handler: collect all typed answers (blanks included) and build the result code per the §1 contract (no grading, no score shown)
- [x] 2.5 Add the "שלחי לאבא" button linking to `wa.me/<number>?text=<encoded-code>`, plus an always-visible copyable code fallback

## 3. CLI entry point

- [x] 3.1 Create `build_quiz.py` CLI mirroring `generate.py` conventions: `--date`, `--force`
- [x] 3.2 Read `wiki/sessions/{date}/generated.json`; error clearly if missing
- [x] 3.3 Write `wiki/sessions/{date}/quiz.html` (write-once unless `--force`)

## 4. /results code handling

- [x] 4.1 Update `.claude/skills/results.md` and `.claude/commands/results.md` (kept in sync) to detect a pasted result code in the invocation
- [x] 4.2 Add a `python -c` step that calls `src/quizcode.decode(...)`: validate checksum, extract the date and ordered `{id, answer}` list; on bad checksum, instruct the parent to re-send
- [x] 4.3 Map decoded entries to the session's `generated.json` by date and question id; if the date has no matching session, report and stop
- [x] 4.4 Grade decoded answers with the skill's existing judgment; mark blanks as wrong with note "left blank"; record wrong answers as notes ("wrote X instead of Y"); write `results.json`, run `analyze.py`, show summary
- [x] 4.5 Preserve existing natural-language reporting path unchanged

## 5. Tests

- [x] 5.1 Round-trip test in `src/quizcode.py`: `encode` → `decode` over numeric, fraction, and Hebrew answers (including blanks)
- [x] 5.2 Checksum test: a mutated code is rejected by `decode`
- [x] 5.3 Builder test: `build_quiz` output is self-contained (no `http`/`https`/`//cdn` references), contains every question, and contains no correct answers
- [x] 5.4 he-only fallback test: a question with only `he` renders with an input, not a blank

## 6. Verification

- [ ] 6.1 Manually open a generated `quiz.html` on desktop and phone; confirm offline load, RTL rendering, code generation, and the `wa.me` pre-fill + copy fallback _(requires a human on real devices — not automatable here)_
- [x] 6.2 End-to-end: build quiz → answer → tap send → paste code into `/results` → confirm grading, `results.json` notes, and `summary.json` update
