## MODIFIED Requirements

### Requirement: Skill accepts optional overrides
The parent SHALL be able to pass arguments: `/practice fractions 10 hard` to override the automatic selection. The difficulty argument MAY be a single global level (`easy`/`medium`/`hard`) OR one or more per-topic assignments of the form `topic=level`, which the skill passes through to `generate.py --difficulty`. Positional difficulty remains global; per-topic control is expressed only via explicit `topic=level` tokens to avoid ambiguity.

#### Scenario: Override applied
- **WHEN** parent runs `/practice fractions 10 hard`
- **THEN** skill runs `python generate.py --topics fractions --count 10 --difficulty hard`

#### Scenario: Per-topic difficulty passed through
- **WHEN** parent runs `/practice fractions=hard division=easy`
- **THEN** skill runs `python generate.py --difficulty fractions=hard division=easy`, leaving topic selection automatic
