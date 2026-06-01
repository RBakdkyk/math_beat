## MODIFIED Requirements

### Requirement: Skill asks for clarification when needed
If the parent skips a question or the report is ambiguous, the skill SHALL ask for the specific answer in English.

#### Scenario: Missing question
- **WHEN** parent reports results for q1-q5 and q7-q8 but skips q6
- **THEN** skill asks "What did Ayala answer for q6 — {question text}?"

#### Scenario: Ambiguous report
- **WHEN** parent says "q3 she kind of got it"
- **THEN** skill asks "What exactly did she write? The correct answer is {answer}"

### Requirement: Skill writes results.json
After all questions are accounted for, the skill SHALL confirm with the parent in English before writing `wiki/sessions/{date}/results.json`. All persisted notes in results.json SHALL be in English.

#### Scenario: Confirmation prompt
- **WHEN** all answers have been processed and the summary table is shown
- **THEN** skill asks "Write results?" (not Hebrew "לכתוב את התוצאות?")

#### Scenario: Results already exist warning
- **WHEN** results.json already exists for the date
- **THEN** skill warns "Results already exist for {date}. Continuing will overwrite them. Continue?"

#### Scenario: Notes stored in English
- **WHEN** the skill records a note for a wrong answer (e.g., child didn't understand or wrote a wrong value)
- **THEN** the note field in results.json is in English (e.g., "wrote 54 instead of 56", "didn't understand concept")

### Requirement: Skill runs analyze and shows summary
After writing results.json, the skill SHALL run `python analyze.py {date}` and display a progress summary in English.

#### Scenario: Progress summary shown
- **WHEN** results are written and analyze completes
- **THEN** skill shows English summary: total correct/wrong, per-topic breakdown, and tomorrow's focus as "Tomorrow: focus on {weakest_topic} ({rate}% correct)."

#### Scenario: No session found
- **WHEN** `/results` is invoked and no generated.json exists for today
- **THEN** skill reports "No questions found for {date}. Did you generate today's session? Try running /practice first."

## ADDED Requirements

### Requirement: All skill output SHALL be in English
The `/results` skill SHALL use English for all conversational output including prompts, confirmations, summary tables, error messages, and progress focus lines. Hebrew content is only acceptable in answer matching logic (recognizing Hebrew child answers) and in displaying the original Hebrew question text.

#### Scenario: Summary table in English with English topic labels
- **WHEN** skill shows the results summary table
- **THEN** table uses English labels and English topic names: "Results Summary:", "Q1 (mult 7x8): correct", "Q2 (fraction 1/2+1/4): wrong (answered 3/8)", "Q4 (addition 91+60): correct", "Correct: X out of Y". Topic labels SHALL be English (mult, fraction, addition, subtraction, division) not Hebrew (כפל, שבר, חיבור, חיסור, חילוק).

#### Scenario: Invite parent to report
- **WHEN** skill is ready for the parent to report answers
- **THEN** skill asks in English, e.g. "Please tell me Ayala's answers. For example: 'Q1 she said 56, Q2 she didn't know, Q3 she wrote 12...'"
