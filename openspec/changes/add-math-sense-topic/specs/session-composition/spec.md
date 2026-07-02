## ADDED Requirements

### Requirement: Constant math-sense slot appended to every session
Every generated session SHALL include exactly 1 `math-sense` question, appended after the normally computed weakness-ranked plan — additive, not a replacement of an existing slot. A session requested with `--count N` SHALL therefore contain `N + 1` questions when math-sense is included.

#### Scenario: Default session gets an extra math-sense question
- **WHEN** `python generate.py --count 8` is run
- **THEN** the session contains the normal 8 weakness-ranked questions plus 1 additional math-sense question, for 9 total

#### Scenario: Topic-override session still gets math-sense
- **WHEN** `python generate.py --topics fractions --count 10` is run
- **THEN** the session contains 10 fraction questions plus 1 additional math-sense question, for 11 total

### Requirement: Math-sense excluded from priority-based rotation
The `math-sense` topic SHALL NOT compete in the weakness/staleness/coverage priority ranking used to select the primary and rotation zones. It is never selected as a result of `_prioritized_topics`; its single slot is always appended separately.

#### Scenario: Math-sense never wins a rotation slot
- **WHEN** priority is computed for all template topics, and `math-sense` has a low correct_rate
- **THEN** `math-sense` is still excluded from the ranked list and does not occupy a primary or rotation slot — its 1 slot is added on top regardless of its priority score
