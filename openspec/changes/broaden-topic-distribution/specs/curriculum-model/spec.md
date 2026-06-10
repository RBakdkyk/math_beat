## ADDED Requirements

### Requirement: Volume and surface-area question generation
The curriculum module SHALL provide a `volume-surface-area` topic (Ministry subtopic ח.2) that generates Hebrew questions on the volume and surface area of a cuboid (תיבה), consistent with the existing `measurements-*` topics. Generation SHALL be stdlib-only, produce **numeric** answers (the existing grader's supported answer type), and use stable signatures of the form `volume:{params}` and `surface:{params}`. Difficulty tiers SHALL follow the same rule-based style as existing topics and SHALL stay within the kita4 scope defined in `curriculum_knowledge.md`.

#### Scenario: Cuboid volume question
- **WHEN** a `volume-surface-area` question is generated for volume
- **THEN** the question gives the cuboid's dimensions in Hebrew and expects the volume (`a×b×c`) as a numeric answer with a `volume:` signature

#### Scenario: Cuboid surface-area question
- **WHEN** a `volume-surface-area` question is generated for surface area
- **THEN** the question gives the cuboid's dimensions in Hebrew and expects the surface area (`2(ab+bc+ca)`) as a numeric answer with a `surface:` signature

#### Scenario: Difficulty tiers respected
- **WHEN** the difficulty rises from easy to hard
- **THEN** the cuboid's dimensions grow according to the tier range constraints, distinct across easy, medium, and hard

### Requirement: New topic integrates with the topic catalog and generators
The `volume-surface-area` topic SHALL have a `TOPICS` entry, a registered template generator in `_GENERATORS`, and defined difficulty tiers, so the session planner can select it and the results skill can grade it like any existing template topic. It SHALL be a template (non-Claude) topic, and SHALL be **quiz-renderable** — it presents the cuboid's dimensions as text with a numeric answer, so it requires no drawn figure and SHALL NOT be added to `NEEDS_VISUAL_TOPICS`.

#### Scenario: New topic is quiz-renderable
- **WHEN** `is_quiz_renderable("volume-surface-area")` is checked
- **THEN** it returns True, so the topic can appear in the HTML quiz round-trip alongside other numeric topics

#### Scenario: Planner can select the new topic
- **WHEN** the session planner prioritizes topics and `volume-surface-area` is among the highest-priority distinct topics
- **THEN** the planner can place it in a rotation slot and `make_question` produces a valid question for it without invoking Claude

#### Scenario: New topic is gradeable
- **WHEN** a `volume-surface-area` question is answered
- **THEN** its numeric answer type and value allow the results skill to compare the child's response, the same way existing template topics are graded
