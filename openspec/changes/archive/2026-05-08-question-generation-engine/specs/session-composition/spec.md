## ADDED Requirements

### Requirement: Session structure
Each generated session SHALL contain 5-10 questions organized into blocks: warmup (multiplication), main (weakest topic), and optional secondary (second weakest topic). All kita4 topics are available — no "current topic" configuration needed.

#### Scenario: Default session composition
- **WHEN** generate.py is run with no arguments and progress data exists
- **THEN** the session contains 3 warmup questions + 4-5 main questions (weakest topic) + 1-2 secondary questions (second weakest)

#### Scenario: First session with no progress
- **WHEN** generate.py is run and no summary.json exists
- **THEN** the session generates a diagnostic set: 3 multiplication questions (random facts), and remaining questions spread across arithmetic operations and fractions at easy difficulty

### Requirement: Topic selection by weakness, not configuration
The main and secondary blocks SHALL be selected purely from progress data: lowest `correct_rate`, longest time since `last_practiced`, and fewest `times_practiced`. Untouched topics (times_practiced: 0) naturally surface through the priority algorithm.

#### Scenario: Untouched topic surfaces
- **WHEN** fractions has been practiced 5 times but geometry has never been practiced
- **THEN** geometry gets higher priority due to times_practiced: 0

#### Scenario: Two weak topics compete
- **WHEN** fractions has correct_rate 0.4 (practiced yesterday) and division has correct_rate 0.5 (practiced 5 days ago)
- **THEN** the algorithm weighs both weakness and staleness to pick main and secondary blocks

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
- **THEN** session contains exactly 5 questions (2 warmup + 3 main)

### Requirement: Overwrite protection
If `generated.json` already exists for the target date, generate.py SHALL refuse and print a warning. Use `--force` to overwrite.

#### Scenario: Double run blocked
- **WHEN** user runs `python generate.py` and today's generated.json already exists
- **THEN** system prints "Session already generated for 2026-05-08. Use --force to overwrite." and exits
