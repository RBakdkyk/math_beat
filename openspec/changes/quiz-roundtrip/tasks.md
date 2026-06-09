## 1. Curriculum model & generator metadata

- [x] 1.1 Add a `quiz_renderable` / needs-visual classification to the topic model in `src/curriculum.py` (needs-visual = `geometry`, `symmetry`); expose a helper to query it
- [x] 1.2 Emit per-question `widget` (`text`|`choice`) and, for `choice`, an `options` list from the generators in `src/curriculum.py` (`prime-composite` → `["ראשוני","פריק"]`; `divisibility` and yes/no exponent → `["כן","לא"]`; numeric/fraction/`2^3` → `text`)
- [x] 1.3 Mark `fraction-comparison` as a `choice` of `>`/`<`/`=` rendered with the canonical prompt `"סמני > או < או ="`, independent of the stored `description` variant

## 2. Code envelope (encode + decode)

- [x] 2.1 Implement the envelope codec (stdlib only): encode `[[id,"answer"], …]` → `AYL~<date>~<base64>~<check>` and decode back, with `check = BASE36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]`
- [x] 2.2 Implement a tolerant extractor that anchors on `AYL~` and matches date + base64 charset + one check char inside surrounding text/emoji
- [x] 2.3 Verify the codec reproduces the three recovered sample codes exactly (`j`, `3`, `9`) round-trip — confirmed; base64 is standard with trailing `=` padding stripped

## 3. .env handling

- [x] 3.1 Add a stdlib-only `.env` `KEY=VALUE` reader and a `PARENT_WHATSAPP` accessor that normalizes to digits-only `wa.me` form
- [x] 3.2 Add `.env` to `.gitignore`

## 4. Quiz generation (`quiz.py` + `quiz.html`)

- [x] 4.1 Add `quiz.py` CLI: read `wiki/sessions/{date}/generated.json`, write self-contained `quiz.html`; support `--force`; error clearly when the session or `PARENT_WHATSAPP` is missing
- [x] 4.2 Render each question's `description` + `exercise` with the widget from its metadata (`text` → free-text field accepting `/`,`,`,`.`; `choice` → option buttons); never `<input type="number">`
- [x] 4.3 Render `fraction-comparison` with the fixed `"סמני > או < או ="` prompt + `>`/`<`/`=` buttons
- [x] 4.4 Strip the answer key from the HTML entirely
- [x] 4.5 Exclude needs-visual questions with a generation-time warning; keep them out of the rendered set and the code
- [x] 4.6 Implement the Done button: encode rendered answers (rendered-but-unanswered → `""`), build the `AYL~…` code, and open `https://wa.me/<number>?text=<encodeURIComponent(code)>`
- [x] 4.7 RTL/Hebrew layout with LTR math expressions rendered correctly

## 5. `/results` code branch

- [x] 5.1 Update `.claude/skills/results.md` (and `.claude/commands/results.md`) to detect a pasted `AYL~…` code, extract it, and branch into code mode
- [x] 5.2 Validate the check char and confirm the envelope date has a `generated.json`; reject corrupt/unknown with a clear English message and write nothing
- [x] 5.3 Decode id-tagged answers, map to questions by `id`, omit blank `""` answers and ids absent from the payload
- [x] 5.4 Apply grading rules: number normalization (strip `,` + trailing punctuation, keep `.`/`/`), unit-strip on measurement keys, and comparison-symbol derivation for `fraction-comparison` (incl. `"שווים"` → `=`)
- [x] 5.5 Record the child's raw decoded answer as the result note (at least for wrong answers)
- [x] 5.6 Confirm → `write_results(force=…)`; run `analyze.py {date}` first-time or `analyze.py --rebuild` when the date already had results; show the existing "Tomorrow: focus on …" tail

## 6. Verification

- [ ] 6.1 Decode each of the three recovered codes and confirm the graded `results.json` matches the corresponding session's answer key — **blocked**: the recovered sessions (2026-06-08/03/01) have no `generated.json` in this repo, so there is no answer key to grade against. Codec round-trip for all three is verified in `tests/test_quiz_roundtrip.py`.
- [x] 6.2 Test blank-skip: a code with `""` entries omits those ids from `results.json`
- [x] 6.3 Test normalization: `"1,038"`, `"381,"`, `"247"` vs unit-bearing keys all grade as expected
- [x] 6.4 Test comparison: a tapped symbol grades against the derived symbol (correct, wrong, and `"שווים"`/`=` equal cases)
- [x] 6.5 Test corrupt code (bad check char) and unknown-date code are both rejected without writing
- [x] 6.6 Test re-processing a date runs `--rebuild` and leaves each session counted once in `summary.json` (no double-count) — verified on Python 3.12 (via uv): write→`analyze.py {date}` gives `times_practiced=1`; re-write→`analyze.py --rebuild` keeps it at `1`.
- [x] 6.7 Test the Done link percent-encodes a payload containing base64 `+`/`/` and still round-trips
- [x] 6.8 Generate a quiz for a real session, open `quiz.html`, solve it, and confirm the Done button produces a code that round-trips through the `/results` code branch — verified on Python 3.12: `quiz.py 2026-05-27` wrote a real `quiz.html`; driving its own `buildCode` JS in node produced a code that `quiz_results.py` decoded + graded 9/10 (blanks skipped, units/comparison/Hebrew-mixed handled). Opening on an actual phone is the only step not automatable here.
