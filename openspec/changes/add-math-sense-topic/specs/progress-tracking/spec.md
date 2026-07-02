## ADDED Requirements

### Requirement: Math-sense tracked like any topic despite priority exclusion
`math-sense` results SHALL flow through the same `analyze.py` merge logic as every other topic, accumulating `correct_rate`, `times_practiced`, `last_practiced`, and `used_params` in `summary.json` under `topics.math-sense`. Its exclusion from rotation priority (see session-composition) SHALL NOT affect whether it is tracked.

#### Scenario: Math-sense stats accumulate normally
- **WHEN** analyze.py processes a session that included a math-sense question
- **THEN** `summary.json.topics.math-sense.times_practiced` increments and `correct_rate` is recalculated, exactly as for any other topic
