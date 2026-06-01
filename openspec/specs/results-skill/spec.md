## ADDED Requirements

### Requirement: Skill loads today's session
When `/results` is invoked, the skill SHALL read the most recent (or specified date's) `generated.json` to know all questions, correct answers, and signatures.

#### Scenario: Today's session exists
- **WHEN** `/results` is invoked and `wiki/sessions/2026-05-08/generated.json` exists
- **THEN** the skill loads all questions with their correct answers and is ready to receive the parent's report

#### Scenario: No session found
- **WHEN** `/results` is invoked and no generated.json exists for today
- **THEN** the skill asks which date to process or reports that no session was generated today

### Requirement: Parent reports answers in natural language
The parent SHALL describe what the child answered per question in free-form text. The skill determines correctness by comparing against the known correct answers.

#### Scenario: Parent reports correct answer
- **WHEN** parent says "q1 she said 56" and the correct answer for q1 is 56
- **THEN** skill marks q1 as correct

#### Scenario: Parent reports wrong answer
- **WHEN** parent says "q2 she wrote 54" and the correct answer is 56
- **THEN** skill marks q2 as wrong with note "wrote 54 instead of 56"

#### Scenario: Parent reports conceptual difficulty
- **WHEN** parent says "q6 she didn't understand"
- **THEN** skill marks q6 as wrong with note "didn't understand concept"

### Requirement: Skill asks for clarification when needed
If the parent skips a question or the report is ambiguous, the skill SHALL ask for the specific answer.

#### Scenario: Missing question
- **WHEN** parent reports results for q1-q5 and q7-q8 but skips q6
- **THEN** skill asks "what did she answer for q6 — {question text}?"

#### Scenario: Ambiguous report
- **WHEN** parent says "q3 she kind of got it"
- **THEN** skill asks "what exactly did she write? The correct answer is {answer}"

### Requirement: Skill writes results.json
After all questions are accounted for, the skill SHALL write `wiki/sessions/{date}/results.json` with structured results.

#### Scenario: Complete results written
- **WHEN** parent has reported on all 8 questions (6 answered, 2 skipped)
- **THEN** results.json contains 6 entries with correct/wrong and notes; skipped questions omitted

### Requirement: Skill runs analyze and shows summary
After writing results.json, the skill SHALL run `python analyze.py {date}` to update summary.json, then display a progress summary to the parent.

#### Scenario: Progress summary shown
- **WHEN** results are written and analyze completes
- **THEN** skill shows: total correct/wrong, per-topic breakdown, notable changes ("7×8 finally clicked — 3 correct in a row"), and what the generator will focus on tomorrow

### Requirement: Skill accepts optional date argument
The parent SHALL be able to specify a date: `/results 2026-05-07` to process a previous session.

#### Scenario: Past date specified
- **WHEN** parent runs `/results 2026-05-07`
- **THEN** skill loads that date's generated.json and processes results for that session
