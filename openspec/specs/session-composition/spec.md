## ADDED Requirements

### Requirement: Session structure
Each generated session SHALL contain 5-10 questions organized as a warmup (multiplication) block plus up to three distinct subject blocks selected by priority. The non-warmup questions SHALL be split as evenly as possible across the chosen subjects, with any remainder going to the higher-priority subjects. If fewer than three subjects are available (small `--count` or few topics), the session covers as many distinct subjects as it can. All kita4 topics are available — no "current topic" configuration needed.

#### Scenario: Default session composition
- **WHEN** generate.py is run with no arguments and progress data exists
- **THEN** the session contains 3 warmup questions + the remaining questions spread across the 3 highest-priority subjects (e.g. count 8 → 3 warmup + 2/2/1 across three subjects)

#### Scenario: First session with no progress
- **WHEN** generate.py is run and no summary.json exists
- **THEN** the session generates a diagnostic set: 3 multiplication questions (random facts), and the remaining questions spread across three core subjects at medium difficulty

### Requirement: Topic selection by weakness, not configuration
The subject blocks SHALL be selected purely from progress data: lowest `correct_rate`, longest time since `last_practiced`, and fewest `times_practiced`. Untouched topics (times_practiced: 0) naturally surface through the priority algorithm. The top three priority topics become the session's subjects.

#### Scenario: Untouched topic surfaces
- **WHEN** fractions has been practiced 5 times but geometry has never been practiced
- **THEN** geometry gets higher priority due to times_practiced: 0

#### Scenario: Three weak topics compete
- **WHEN** several topics have differing `correct_rate` and `last_practiced`
- **THEN** the algorithm weighs weakness and staleness and selects the three highest-priority topics as the session's subjects

### Requirement: Warmup targets weak multiplication facts
The warmup block SHALL select multiplication facts from the weakest facts in summary.json (lowest correct/wrong ratio). If no progress exists, random facts are selected.

#### Scenario: Weak facts available
- **WHEN** summary.json shows 7×8 at 2 correct / 3 wrong and 3×4 at 5 correct / 0 wrong
- **THEN** warmup questions target 7×8 (and similar weak facts), not 3×4

### Requirement: CLI argument overrides
The user SHALL be able to override automatic selection via CLI: `--topics`, `--count`, `--difficulty`.

#### Scenario: Forced topic
- **WHEN** user runs `python generate.py --topics fractions --count 10`
- **THEN** all 10 questions are about fractions, ignoring warmup/main/secondary structure

### Requirement: Question count argument
The `--count` argument SHALL control total questions (default: 8).

#### Scenario: Custom count
- **WHEN** user runs `python generate.py --count 5`
- **THEN** session contains exactly 5 questions (3 warmup + 2 subject questions across up to 2 distinct subjects)

### Requirement: Overwrite protection
If `generated.json` already exists for the target date, generate.py SHALL refuse and print a warning. Use `--force` to overwrite.

#### Scenario: Double run blocked
- **WHEN** user runs `python generate.py` and today's generated.json already exists
- **THEN** system prints "Session already generated for 2026-05-08. Use --force to overwrite." and exits
