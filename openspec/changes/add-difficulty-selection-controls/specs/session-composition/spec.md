## MODIFIED Requirements

### Requirement: CLI argument overrides
The user SHALL be able to override automatic selection via CLI: `--topics`, `--count`, `--difficulty`. The `--difficulty` argument SHALL accept either a single global value (`easy`/`medium`/`hard`) applied to all questions, OR per-topic assignments of the form `topic=level` (e.g. `fractions=hard division=easy`), optionally combined with a bare global value as fallback. Precedence for any given question is: **per-topic override > global `--difficulty` > automatic `_infer_difficulty`**.

#### Scenario: Forced topic
- **WHEN** user runs `python generate.py --topics fractions --count 10`
- **THEN** all 10 questions are about fractions, ignoring warmup/main/secondary structure

#### Scenario: Global difficulty override
- **WHEN** user runs `python generate.py --difficulty hard`
- **THEN** every generated question uses the hard tier

#### Scenario: Per-topic difficulty override
- **WHEN** user runs `python generate.py --difficulty fractions=hard division=easy`
- **THEN** fraction questions use the hard tier, division questions use the easy tier, and any other topic falls back to automatic `_infer_difficulty`

#### Scenario: Global fallback with per-topic override
- **WHEN** user runs `python generate.py --difficulty medium fractions=hard`
- **THEN** fraction questions use hard and all other topics use medium

#### Scenario: Override applies only to selected topics
- **WHEN** user runs `python generate.py --difficulty fractions=hard` and the auto-planner does not select fractions for the session
- **THEN** no fraction questions are added by the override (it is a no-op); to force fractions in, the user combines it with `--topics fractions`

#### Scenario: Override honored in bootstrap path
- **WHEN** no progress data exists and user runs `python generate.py --topics division --difficulty division=easy`
- **THEN** the bootstrap plan generates division questions at the easy tier (the override is applied even on the bootstrap/`--topics` path, not only the adaptive path)

#### Scenario: Invalid difficulty token rejected
- **WHEN** user runs `python generate.py --difficulty fractions=banana`
- **THEN** generation fails with a clear error naming the invalid level

### Requirement: Topic selection by weakness, not configuration
The main and secondary blocks SHALL be selected purely from progress data: lowest `correct_rate`, longest time since `last_practiced`, and fewest `times_practiced`. Untouched topics (times_practiced: 0) naturally surface through the priority algorithm. Because the student is treated as advanced, the difficulty pitch SHALL skew upward: the bootstrap/diagnostic plan SHALL start non-warmup questions at `medium` (not `easy`), and `_infer_difficulty` thresholds SHALL be set so harder tiers are reached sooner than the prior 0.4/0.8 split.

#### Scenario: Untouched topic surfaces
- **WHEN** fractions has been practiced 5 times but geometry has never been practiced
- **THEN** geometry gets higher priority due to times_practiced: 0

#### Scenario: Two weak topics compete
- **WHEN** fractions has correct_rate 0.4 (practiced yesterday) and division has correct_rate 0.5 (practiced 5 days ago)
- **THEN** the algorithm weighs both weakness and staleness to pick main and secondary blocks

#### Scenario: Advanced bootstrap starts at medium
- **WHEN** no progress data exists and a diagnostic session is generated
- **THEN** non-warmup questions are generated at the `medium` tier, not `easy`

#### Scenario: Advanced threshold reaches hard sooner
- **WHEN** a topic's correct_rate is 0.7
- **THEN** `_infer_difficulty` returns `hard` (under the shifted thresholds), where the prior 0.8 threshold would have returned `medium`

### Requirement: Warmup targets weak multiplication facts
The warmup block SHALL select multiplication facts from the weakest facts in summary.json (lowest correct/wrong ratio). If no progress exists, random facts are selected. The advanced pitch and any per-topic difficulty override SHALL NOT disable weak-fact targeting for the warmup.

#### Scenario: Weak facts available
- **WHEN** summary.json shows 7×8 at 2 correct / 3 wrong and 3×4 at 5 correct / 0 wrong
- **THEN** warmup questions target 7×8 (and similar weak facts), not 3×4

#### Scenario: Override does not disable warmup targeting
- **WHEN** a per-topic override sets `multiplication-table=hard`
- **THEN** warmup questions still target the weakest facts, now drawn from the hard tier's fact pool
