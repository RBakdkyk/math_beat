## ADDED Requirements

### Requirement: Accept a pasted code as an input mode

`/results` SHALL accept a pasted return code as an alternative to a verbal report. When the invocation contains an `AYL~…` code (with or without a `CODE:` prefix, and possibly surrounded by other text), the skill SHALL extract it by anchoring on the `AYL~` marker and matching the date, base64 payload, and exactly one trailing check char, ignoring surrounding text or emoji and trimming whitespace.

#### Scenario: Code pasted directly
- **WHEN** `/results AYL~2026-06-08~W1sx…~j` is invoked
- **THEN** the skill decodes the code, uses `2026-06-08` from the envelope as the session date, and grades the decoded answers without asking the parent to report

#### Scenario: Code embedded in surrounding text
- **WHEN** the pasted text is `done! AYL~2026-06-08~W1sx…~j 🎉`
- **THEN** the skill still extracts and processes the `AYL~…~j` code

### Requirement: Validate the checksum and date before grading

Before grading, the skill SHALL recompute `BASE36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]` and compare it case-insensitively to the code's trailing check char, and SHALL confirm a `generated.json` exists for the envelope's date. On mismatch or unknown date it SHALL stop with a clear English message and not write results.

#### Scenario: Corrupt code rejected
- **WHEN** a pasted code's recomputed check char does not match its trailing char
- **THEN** the skill reports the code looks corrupted and asks the parent to re-paste it, and writes nothing

#### Scenario: No session for the code's date
- **WHEN** a code decodes to date `2026-06-08` but no `generated.json` exists for that date
- **THEN** the skill reports there is no session for that date and writes nothing

### Requirement: Decode id-tagged answers and skip blanks

The skill SHALL decode the base64 payload as `[[id,"answer"], …]`, map each answer to the question of the same `id` in `generated.json`, and OMIT any entry whose answer is the empty string `""` so skipped questions are not counted. Ids present in `generated.json` but absent from the payload (e.g. excluded needs-visual questions) are likewise not counted.

#### Scenario: Blank answers are skipped
- **WHEN** a code decodes to `[[1,"65"],[2,"54"],[3,"35"],[4,""],[5,""],[6,"44"],[7,"44"],[8,"1"]]`
- **THEN** questions 4 and 5 are omitted from `results.json` (neither correct nor wrong) and the other six are graded

### Requirement: Normalize numbers and strip units before grading

For text-widget numeric and fraction answers the skill SHALL strip `,` thousands separators and trailing stray punctuation while preserving `.` and `/`, and SHALL strip the unit suffix from measurement answer keys before comparing. Existing fraction equivalence (unreduced ↔ reduced ↔ decimal) is preserved.

#### Scenario: Thousands separator accepted
- **WHEN** the stored answer is `1038` and the child's decoded answer is `"1,038"`
- **THEN** the answer is graded correct

#### Scenario: Trailing stray punctuation ignored
- **WHEN** the stored answer is `381` and the child's decoded answer is `"381,"`
- **THEN** the answer is graded correct

#### Scenario: Unit stripped from measurement key
- **WHEN** the stored answer is `"247 מ\"ר"` and the child's decoded answer is `"247"`
- **THEN** the answer is graded correct

### Requirement: Derive the comparison symbol for fraction-comparison

For `fraction-comparison` questions, where `generated.json` stores the answer as the larger fraction (or `"שווים"` when equal), the skill SHALL parse the two operands from `exercise`, derive the correct symbol — `>`/`<` from which operand the stored answer matches, or `=` when the stored answer is `"שווים"` — and compare that derived symbol to the child's tapped symbol.

#### Scenario: Tapped symbol graded against derived symbol
- **WHEN** `exercise` is `1/5 ___ 5/8`, the stored answer is `5/8`, and the child's decoded answer is `">"`
- **THEN** the skill derives the correct symbol `<` and marks the child's `>` as wrong

#### Scenario: Equal fractions
- **WHEN** `exercise` is `2/4 ___ 1/2`, the stored answer is `"שווים"`, and the child's decoded answer is `"="`
- **THEN** the skill derives the correct symbol `=` and marks the answer correct

### Requirement: Record the child's raw answer as the note

When grading from a code, the skill SHALL store the child's decoded raw answer as the result note (at least for wrong answers) so the parent can see what she actually wrote, since no human is present to describe the mistake.

#### Scenario: Wrong answer note
- **WHEN** the stored answer is `56` and the child's decoded answer is `"54"`
- **THEN** the written result for that question is marked wrong with a note recording `54`

### Requirement: Re-processing a date rebuilds rather than increments

Because `analyze.py {date}` appends to progress with no per-date dedup, when the code's date already has `results.json` the skill SHALL rewrite it with `--force` and then run `analyze.py --rebuild` (wipe and replay all sessions) instead of `analyze.py {date}`, so progress is not double-counted. First-time processing uses the incremental `analyze.py {date}`.

#### Scenario: First-time processing increments
- **WHEN** a code is graded for a date that has no existing `results.json`
- **THEN** the skill writes `results.json` and runs `analyze.py {date}`

#### Scenario: Re-processing rebuilds
- **WHEN** a code is graded for a date that already has `results.json` and the parent confirms overwrite
- **THEN** the skill rewrites `results.json` with `--force` and runs `analyze.py --rebuild`, leaving `summary.json` consistent with each session counted once

### Requirement: Reuse the existing write and analyze tail

After grading and (re)analyzing, the skill SHALL produce the same progress summary and next-day focus line as the verbal-report path. No change to `progress.py`, `session.py`, or `analyze.py` is required.

#### Scenario: Progress updated from a code
- **WHEN** a valid code is graded and confirmed
- **THEN** `summary.json` is updated and the usual "Tomorrow: focus on {topic} ({rate}%)" line is shown
