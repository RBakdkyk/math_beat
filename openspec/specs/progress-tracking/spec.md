## ADDED Requirements

### Requirement: Structured summary.json with item-level tracking
The progress summary SHALL track per-topic: `correct_rate`, `times_practiced`, `last_practiced`. Multiplication SHALL track individual facts with correct/wrong counts. Other topics SHALL track `used_params` with signatures, dates, and correctness.

#### Scenario: Multiplication fact-level state
- **WHEN** summary.json is read for multiplication-table
- **THEN** each of the 55 unique facts has individual `correct` count, `wrong` count, and `last_seen` date

#### Scenario: Fraction used_params state
- **WHEN** summary.json is read for fraction-addition
- **THEN** `used_params` contains a list of `{sig, date, correct}` entries for recent parameter combinations

### Requirement: Analyze merges results into summary
`analyze.py` SHALL read a session's `generated.json` (with signatures) and `results.json`, then merge into summary.json: update correct/wrong counts per item, update used_params, recalculate correct_rate per topic.

#### Scenario: After first analyzed session
- **WHEN** analyze.py processes the first session with 8 questions
- **THEN** summary.json contains entries with correct/wrong from that session

#### Scenario: Incremental update
- **WHEN** analyze.py processes a second session
- **THEN** existing fact counts are incremented (not replaced), new used_params are appended, correct_rate recalculated

### Requirement: 15-day retention prune on used_params
When analyze.py updates summary.json, it SHALL prune `used_params` entries older than 15 days. Multiplication `facts` are never pruned (cumulative counts).

#### Scenario: Old params pruned
- **WHEN** analyze.py runs and used_params contains entries from 20 days ago
- **THEN** those entries are removed; entries from 10 days ago are retained

#### Scenario: Multiplication facts never pruned
- **WHEN** analyze.py runs
- **THEN** multiplication fact correct/wrong counts are preserved regardless of age

### Requirement: Results.json input format
Results SHALL be `{id, correct: bool, note?: string}`. Skipped questions are omitted (not counted as wrong).

#### Scenario: Partial results
- **WHEN** the child answered 6 of 8 questions
- **THEN** results.json contains 6 entries; skipped questions omitted

### Requirement: Overwrite protection for results
If results.json already exists for a date, the results skill SHALL warn and require confirmation before overwriting.

#### Scenario: Double results entry blocked
- **WHEN** `/results` is run for a date that already has results.json
- **THEN** skill warns "Results already exist for 2026-05-08. Overwrite?" and waits for confirmation

### Requirement: Analyze CLI
`analyze.py` SHALL accept a date argument and update summary.json.

#### Scenario: Analyze run
- **WHEN** user runs `python analyze.py 2026-05-08`
- **THEN** summary.json is updated with stats from that session

### Requirement: Summary rebuild
`python analyze.py --rebuild` SHALL rebuild summary.json from scratch by replaying all sessions chronologically.

#### Scenario: Corrupted summary
- **WHEN** user runs `python analyze.py --rebuild`
- **THEN** summary.json is deleted and rebuilt from all sessions
