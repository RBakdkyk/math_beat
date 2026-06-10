## MODIFIED Requirements

### Requirement: Skill shows brief progress context
Before showing questions, the skill SHALL show a one-line progress summary so the parent knows why these questions were chosen. The summary SHALL NOT name a single "main topic", since the zoned planner spreads each session across several distinct topics rather than choosing one main topic. The summary SHALL still surface the multiplication-warmup context (overall multiplication rate and the weak facts being targeted).

#### Scenario: Progress context shown
- **WHEN** progress data exists
- **THEN** skill shows something like: "Focus today: multiplication (58% correct), plus rotating practice across your weakest topics. 7×8, 6×7 still weak." — without naming a single main topic
