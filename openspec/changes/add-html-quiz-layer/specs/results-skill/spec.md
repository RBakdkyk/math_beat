## ADDED Requirements

### Requirement: Skill accepts a pasted result code from the quiz
When the parent pastes a result code produced by `quiz.html`, `/results` SHALL validate the code's checksum, decode it against the matching session's `generated.json`, and grade the decoded answers using the skill's existing judgment — the same way it grades natural-language reports today. Decoding (checksum validation + extracting the ordered `{id, typed answer}` list) SHALL be performed deterministically in Python; grading SHALL be performed by the skill against the known correct answers.

#### Scenario: Valid code recorded
- **WHEN** the parent pastes a valid result code whose date matches an existing `generated.json`
- **THEN** the skill decodes the typed answers, grades each against the correct answer, writes `results.json`, runs `analyze.py`, and shows the progress summary

#### Scenario: Checksum mismatch rejected
- **WHEN** the parent pastes a code whose checksum does not validate (e.g. a character was dropped or altered)
- **THEN** the skill rejects the code and asks the parent to re-send it rather than recording corrupted results

#### Scenario: Wrong answer captured as a note
- **WHEN** a decoded answer is graded incorrect (e.g. she typed 54, correct is 56)
- **THEN** the `results.json` entry marks the question wrong with a note capturing her actual answer ("wrote 54 instead of 56")

#### Scenario: Blank answer counted as wrong
- **WHEN** a decoded answer slot is blank (the child left it empty)
- **THEN** the skill writes a `results.json` entry for that question with `correct: false` and a note ("left blank"), so it counts against `correct_rate`

#### Scenario: Code date has no matching session
- **WHEN** a code's encoded date has no corresponding `generated.json`
- **THEN** the skill reports that the session for that date was not found and does not write results

#### Scenario: Manual reporting still supported
- **WHEN** the parent reports answers in natural language instead of pasting a code
- **THEN** the skill processes them as before, unchanged
