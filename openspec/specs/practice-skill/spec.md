## ADDED Requirements

### Requirement: Skill reads progress and runs generation
When `/practice` is invoked, the skill SHALL read `wiki/progress/summary.json`, determine appropriate arguments for `generate.py` (topics, count, difficulty), and run the generation.

#### Scenario: Normal daily run
- **WHEN** `/practice` is invoked with progress data available
- **THEN** skill analyzes summary.json, runs `python generate.py` with computed args, and displays output

#### Scenario: First run with no progress
- **WHEN** `/practice` is invoked with no summary.json
- **THEN** skill runs `python generate.py` in bootstrapping mode (default args)

### Requirement: Skill displays WhatsApp-ready output
After generation, the skill SHALL display the WhatsApp-formatted questions so the parent can copy-paste directly.

#### Scenario: Output displayed
- **WHEN** generation completes
- **THEN** skill shows the numbered Hebrew question list with block headers, ready for WhatsApp copy-paste

### Requirement: Skill shows brief progress context
Before showing questions, the skill SHALL show a one-line progress summary so the parent knows why these topics were chosen.

#### Scenario: Progress context shown
- **WHEN** progress data exists
- **THEN** skill shows something like: "Focus today: multiplication (58% correct) + fractions (40% correct). 7×8, 6×7 still weak."

### Requirement: Skill accepts optional overrides
The parent SHALL be able to pass arguments: `/practice fractions 10 hard` to override the automatic selection.

#### Scenario: Override applied
- **WHEN** parent runs `/practice fractions 10 hard`
- **THEN** skill runs `python generate.py --topics fractions --count 10 --difficulty hard`

### Requirement: Overwrite protection
If today's session was already generated, the skill SHALL warn and ask before regenerating.

#### Scenario: Already generated today
- **WHEN** `/practice` is run and today's generated.json exists
- **THEN** skill asks "Already generated today. Show existing questions or regenerate?"
