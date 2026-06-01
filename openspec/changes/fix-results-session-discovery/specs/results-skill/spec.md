## MODIFIED Requirements

### Requirement: Skill loads today's session
When `/results` is invoked, the skill SHALL first check if a date was provided. If yes, load that date's `generated.json`. If no date was provided, the skill SHALL use session discovery to identify and select an unprocessed session before loading.

#### Scenario: No date provided, discovery finds a session
- **WHEN** `/results` is invoked without a date and session discovery identifies `2026-05-08` as the only unprocessed session
- **THEN** after parent confirms, the skill loads `2026-05-08/generated.json` and proceeds with results entry

#### Scenario: No date provided, no unprocessed sessions
- **WHEN** `/results` is invoked without a date and session discovery finds no unprocessed sessions
- **THEN** the skill reports "All sessions have results. To re-process one, run `/results YYYY-MM-DD`."

#### Scenario: Explicit date provided
- **WHEN** `/results 2026-05-07` is invoked
- **THEN** the skill loads `2026-05-07/generated.json` directly (unchanged behavior)

### Requirement: Inline results bypass the reporting prompt
When the parent provides results directly in the `/results` invocation args (alongside or instead of a date), the skill SHALL skip the "report results" prompt and proceed directly to processing those inline results against the loaded questions.

#### Scenario: Inline results with no date
- **WHEN** `/results two wrong answers: 63/9, 4/5 vs 1/5` is invoked
- **THEN** the skill uses session discovery to select a session, loads its questions, and processes the inline results ("two wrong answers: 63/9, 4/5 vs 1/5") without re-asking the parent to report

#### Scenario: Inline results with explicit date
- **WHEN** `/results 2026-05-08 all correct except q3 she wrote 42` is invoked
- **THEN** the skill loads `2026-05-08/generated.json` and processes the inline results without re-asking

#### Scenario: No inline results provided
- **WHEN** `/results` or `/results 2026-05-08` is invoked with no result details
- **THEN** the skill shows questions and asks the parent to report (existing behavior)

### Requirement: All skill output is in English
All prompts, confirmations, summaries, error messages, and notes in results.json SHALL be in English. Hebrew is permitted only when displaying the child's original question text and when matching Hebrew answer values.

#### Scenario: Error message language
- **WHEN** no session is found for the requested date
- **THEN** the error message is in English: "No questions found for {date}."

#### Scenario: Summary table language
- **WHEN** results are confirmed and the summary table is shown
- **THEN** all labels and status text are in English (e.g., "correct", "wrong", "Results Summary")
