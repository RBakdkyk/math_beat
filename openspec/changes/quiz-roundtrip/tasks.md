## 1. Curriculum model & generator metadata

- [ ] 1.1 Add a `quiz_renderable` / needs-visual classification to the topic model in `src/curriculum.py` (needs-visual = `geometry`, `symmetry`); expose a helper to query it
- [ ] 1.2 Emit per-question `widget` (`text`|`choice`) and, for `choice`, an `options` list from the generators in `src/curriculum.py` (`prime-composite` → `["ראשוני","פריק"]`; `divisibility` and yes/no exponent → `["כן","לא"]`; numeric/fraction/`2^3` → `text`)
- [ ] 1.3 Mark `fraction-comparison` as a `choice` of `>`/`<`/`=` rendered with the canonical prompt `"סמני > או < או ="`, independent of the stored `description` variant

## 2. Code envelope (encode + decode)

- [ ] 2.1 Implement the envelope codec (stdlib only): encode `[[id,"answer"], …]` → `AYL~<date>~<base64>~<check>` and decode back, with `check = BASE36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]`
- [ ] 2.2 Implement a tolerant extractor that anchors on `AYL~` and matches date + base64 charset + one check char inside surrounding text/emoji
- [ ] 2.3 Verify the codec reproduces the three recovered sample codes exactly (`j`, `3`, `9`) round-trip

## 3. .env handling

- [ ] 3.1 Add a stdlib-only `.env` `KEY=VALUE` reader and a `PARENT_WHATSAPP` accessor that normalizes to digits-only `wa.me` form
- [ ] 3.2 Add `.env` to `.gitignore`

## 4. Quiz generation (`quiz.py` + `quiz.html`)

- [ ] 4.1 Add `quiz.py` CLI: read `wiki/sessions/{date}/generated.json`, write self-contained `quiz.html`; support `--force`; error clearly when the session or `PARENT_WHATSAPP` is missing
- [ ] 4.2 Render each question's `description` + `exercise` with the widget from its metadata (`text` → free-text field accepting `/`,`,`,`.`; `choice` → option buttons); never `<input type="number">`
- [ ] 4.3 Render `fraction-comparison` with the fixed `"סמני > או < או ="` prompt + `>`/`<`/`=` buttons
- [ ] 4.4 Strip the answer key from the HTML entirely
- [ ] 4.5 Exclude needs-visual questions with a generation-time warning; keep them out of the rendered set and the code
- [ ] 4.6 Implement the Done button: encode rendered answers (rendered-but-unanswered → `""`), build the `AYL~…` code, and open `https://wa.me/<number>?text=<encodeURIComponent(code)>`
- [ ] 4.7 RTL/Hebrew layout with LTR math expressions rendered correctly

## 5. `/results` code branch

- [ ] 5.1 Update `.claude/skills/results.md` (and `.claude/commands/results.md`) to detect a pasted `AYL~…` code, extract it, and branch into code mode
- [ ] 5.2 Validate the check char and confirm the envelope date has a `generated.json`; reject corrupt/unknown with a clear English message and write nothing
- [ ] 5.3 Decode id-tagged answers, map to questions by `id`, omit blank `""` answers and ids absent from the payload
- [ ] 5.4 Apply grading rules: number normalization (strip `,` + trailing punctuation, keep `.`/`/`), unit-strip on measurement keys, and comparison-symbol derivation for `fraction-comparison` (incl. `"שווים"` → `=`)
- [ ] 5.5 Record the child's raw decoded answer as the result note (at least for wrong answers)
- [ ] 5.6 Confirm → `write_results(force=…)`; run `analyze.py {date}` first-time or `analyze.py --rebuild` when the date already had results; show the existing "Tomorrow: focus on …" tail

## 6. Verification

- [ ] 6.1 Decode each of the three recovered codes and confirm the graded `results.json` matches the corresponding session's answer key
- [ ] 6.2 Test blank-skip: a code with `""` entries omits those ids from `results.json`
- [ ] 6.3 Test normalization: `"1,038"`, `"381,"`, `"247"` vs unit-bearing keys all grade as expected
- [ ] 6.4 Test comparison: a tapped symbol grades against the derived symbol (correct, wrong, and `"שווים"`/`=` equal cases)
- [ ] 6.5 Test corrupt code (bad check char) and unknown-date code are both rejected without writing
- [ ] 6.6 Test re-processing a date runs `--rebuild` and leaves each session counted once in `summary.json` (no double-count)
- [ ] 6.7 Test the Done link percent-encodes a payload containing base64 `+`/`/` and still round-trips
- [ ] 6.8 Generate a quiz for a real session, open `quiz.html`, solve it, and confirm the Done button produces a code that round-trips through the `/results` code branch
