## MODIFIED Requirements

### Requirement: Session structure
When progress data exists, each generated session SHALL be organized into zones: **warmup** (multiplication facts), **primary drill** (depth on the highest-priority topic), and **rotation** (one question each across the next-highest-priority distinct topics). There is no separate "coverage" pick — least-touched topics already rank highly via the priority algorithm, so long-tail coverage emerges from the distinct-topic spread. The default count is 10; a default session SHALL contain **at least 5 distinct topics**. Zone sizes SHALL be derived from `--count` for any count ≥ 1, summing exactly to `--count`, with the warmup shrinking first for small counts. If the number of distinct available topics is smaller than the number of rotation slots, the planner MAY repeat topics only after all distinct topics are used. The warmup zone SHALL retain 3 multiplication questions at the default count, preserving the multiplication-warmup contract. All kita4 topics are available — no "current topic" configuration needed.

#### Scenario: Default session composition
- **WHEN** generate.py is run with no arguments and progress data exists
- **THEN** the session contains 10 questions: 3 warmup + 2 primary-drill (highest-priority topic) + 5 rotation (next-highest-priority distinct topics, one each), spanning at least 5 distinct topics

#### Scenario: Breadth when priorities tie
- **WHEN** many never-practiced topics share the same top priority score
- **THEN** the planner spreads the non-warmup slots across distinct topics in priority order rather than repeating only the first two, so the session is not narrowed to an arbitrary pair

#### Scenario: First session with no progress
- **WHEN** generate.py is run and no summary.json exists
- **THEN** the cold-start (bootstrap) path is used unchanged: 3 multiplication questions (random facts) plus a curated diagnostic core of distinct fundamentals (addition, subtraction, division, fraction-comparison, fraction-addition) at the default **medium** difficulty (the "advanced pitch"), not the priority-driven adaptive spread

#### Scenario: Small count scales gracefully
- **WHEN** user runs `python generate.py --count 5`
- **THEN** the session contains exactly 5 questions composed of a scaled warmup plus a distinct-topic spread, with no empty or oversized zone

### Requirement: Topic selection by weakness, not configuration
The non-warmup zones SHALL be selected purely from progress data: lowest `correct_rate`, longest time since `last_practiced`, and fewest `times_practiced`. A topic that has been answered **incorrectly** (low `correct_rate`) SHALL be prioritized **at least as highly** as a never-practiced topic — weakness SHALL never rank below mere unfamiliarity. Untouched topics (times_practiced: 0) still surface naturally through the priority algorithm. The `multiplication-table` topic SHALL be excluded from the non-warmup zones, since it owns the warmup. Topic frequency is driven by weakness rotation only; curriculum hour-weights SHALL NOT bias selection.

#### Scenario: Wrong answers outrank unseen topics
- **WHEN** subtraction has been practiced once at correct_rate 0.0 and several other topics have never been practiced
- **THEN** subtraction is prioritized at least as highly as the never-practiced topics

#### Scenario: Untouched topic surfaces
- **WHEN** fractions has been practiced 5 times but geometry has never been practiced
- **THEN** geometry gets higher priority than the well-practiced fractions topic

#### Scenario: Two weak topics compete
- **WHEN** fractions has correct_rate 0.4 (practiced yesterday) and division has correct_rate 0.5 (practiced 5 days ago)
- **THEN** the algorithm weighs both weakness and staleness to order the primary and rotation zones

### Requirement: Question count argument
The `--count` argument SHALL control total questions (default: 10). Zone sizes SHALL be derived from the count so that the warmup, primary, and rotation zones together sum exactly to the requested count, for **any count ≥ 1** (the warmup shrinks first, then the primary, then rotation), so small or large counts never produce empty, negative, or oversized zones.

#### Scenario: Custom count
- **WHEN** user runs `python generate.py --count 5`
- **THEN** the session contains exactly 5 questions, distributed across the zones by the scaling rule
