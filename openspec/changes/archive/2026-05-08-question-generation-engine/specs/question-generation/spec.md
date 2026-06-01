## ADDED Requirements

### Requirement: Template engine generates deterministic questions
The system SHALL generate questions for computation-based subtopics using Python templates with rule-based parameter generation. Parameters are generated at runtime from difficulty constraints (number ranges + validation rules), not from enumerated lists. No LLM calls SHALL be made for these question types.

#### Scenario: Multiplication question generated deterministically
- **WHEN** a multiplication warmup question is needed for fact 7×8
- **THEN** Python picks a Hebrew template and fills in the numbers without calling Claude

#### Scenario: Fraction question generated from rules
- **WHEN** a medium-difficulty fraction addition question is needed
- **THEN** Python generates denominators within {max_denom: 10, max_numerator: 5}, validates the constraint (one divides the other), selects a template, computes the answer — all without Claude

### Requirement: Claude CLI for creative question types only
The system SHALL invoke `claude -p <prompt> --output-format json` via subprocess ONLY for: word problems, geometry descriptions, data/probability scenarios, and estimation/number sense.

#### Scenario: Word problem needs Claude
- **WHEN** session plan includes a word problem question
- **THEN** Claude CLI is called with curriculum context and constraints

#### Scenario: No Claude needed for computation session
- **WHEN** all questions are computation-based
- **THEN** the entire session is generated with zero token cost

### Requirement: Signature-based deduplication
Each generated question SHALL have a mathematical signature. Template-generated: `"{type}:{params}"` (e.g., `"mult:7×8"`, `"fraction-add:1/2+1/4"`). Claude-generated: `"wordproblem:{category}:{level}"`. The generator SHALL reject signatures found in summary.json's used_params within the last 15 days.

#### Scenario: Recent signature rejected
- **WHEN** signature "fraction-add:1/2+1/4" was used 3 days ago
- **THEN** the question is rejected and the engine generates new parameters

#### Scenario: Old signature reused
- **WHEN** a signature was last used 16+ days ago
- **THEN** it has been pruned from used_params and is eligible for reuse

### Requirement: Weakness-aware parameter selection
For wrong answers, the generator SHALL select similar but not identical parameters. For right answers, the generator SHALL select new parameters to expand coverage.

#### Scenario: Wrong fraction answer drives similar question
- **WHEN** the child got "1/2+1/4" wrong recently
- **THEN** the generator prioritizes similar denominator families (e.g., "1/2+1/6", "3/4+1/4")

#### Scenario: Correct answer expands coverage
- **WHEN** the child got "1/3+1/6" correct
- **THEN** the generator picks an untried combination

### Requirement: Fallback to Claude on generation failure
If the template engine cannot find a non-duplicate question after N attempts (default 10), it SHALL fall back to Claude CLI.

#### Scenario: Rules can't produce non-duplicate
- **WHEN** all easy fraction pairs within the rules have been used in the last 15 days
- **THEN** Claude CLI is called to generate a varied fraction question

### Requirement: Non-numeric answer support
The generator SHALL support questions with categorical answers (prime/composite, yes/no, shape classification) and include the answer type in generated.json.

#### Scenario: Prime identification question
- **WHEN** a prime/composite question is generated for number 17
- **THEN** generated.json includes `{"answer": "ראשוני", "answer_type": "categorical"}`

### Requirement: Generated session persistence
After generation, the system SHALL save `generated.json` to `wiki/sessions/{date}/` with signatures and answer types included.

#### Scenario: Output saved
- **WHEN** generation completes for 2026-05-08
- **THEN** `wiki/sessions/2026-05-08/generated.json` exists with all metadata
