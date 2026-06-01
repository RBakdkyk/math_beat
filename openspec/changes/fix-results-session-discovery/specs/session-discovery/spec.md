## ADDED Requirements

### Requirement: Discover unprocessed sessions when no date provided
When `/results` is invoked without a date argument, the skill SHALL scan all session directories to find sessions that have `generated.json` but no `results.json`.

#### Scenario: One unprocessed session exists
- **WHEN** `/results` is invoked without a date and only `2026-05-08` has generated.json without results.json
- **THEN** the skill says "Found unprocessed session from 2026-05-08. Process this one?" and waits for confirmation

#### Scenario: Multiple unprocessed sessions exist
- **WHEN** `/results` is invoked without a date and `2026-05-07` and `2026-05-08` both have generated.json without results.json
- **THEN** the skill shows a numbered list of unprocessed dates and asks the parent to pick one

#### Scenario: No unprocessed sessions exist
- **WHEN** `/results` is invoked without a date and all sessions already have results.json (or no sessions exist at all)
- **THEN** the skill says "All sessions have results. To re-process one, run `/results YYYY-MM-DD`."

#### Scenario: Explicit date provided — bypass discovery
- **WHEN** `/results 2026-05-07` is invoked with an explicit date
- **THEN** the skill skips discovery and loads that date directly (existing behavior unchanged)
