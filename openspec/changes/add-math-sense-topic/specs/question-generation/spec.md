## MODIFIED Requirements

### Requirement: Claude CLI for creative question types only
The system SHALL invoke `claude -p <prompt> --output-format json` via subprocess ONLY for: word problems, geometry descriptions, and data/probability scenarios. Estimation/number-sense content is covered by the deterministic `math-sense` template topic instead — it SHALL NOT require Claude.

#### Scenario: Word problem needs Claude
- **WHEN** session plan includes a word problem question
- **THEN** Claude CLI is called with curriculum context and constraints

#### Scenario: No Claude needed for computation session
- **WHEN** all questions are computation-based
- **THEN** the entire session is generated with zero token cost

#### Scenario: Math-sense question needs no Claude
- **WHEN** a session plan includes a math-sense question
- **THEN** it is generated entirely by `curriculum.py`'s template engine, with zero token cost
