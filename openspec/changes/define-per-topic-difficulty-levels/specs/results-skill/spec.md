## MODIFIED Requirements

### Requirement: Parent reports answers in natural language
The parent SHALL describe what the child answered per question in free-form text. The skill determines correctness by comparing against the known correct answers. For fraction answers, the skill SHALL accept **both** the stored unreduced form and any mathematically equivalent form (including the reduced form) as correct, since reduction is a grade-5 skill not expected in grade 4.

#### Scenario: Parent reports correct answer
- **WHEN** parent says "q1 she said 56" and the correct answer for q1 is 56
- **THEN** skill marks q1 as correct

#### Scenario: Parent reports wrong answer
- **WHEN** parent says "q2 she wrote 54" and the correct answer is 56
- **THEN** skill marks q2 as wrong with note "wrote 54 instead of 56"

#### Scenario: Parent reports conceptual difficulty
- **WHEN** parent says "q6 she didn't understand"
- **THEN** skill marks q6 as wrong with note "didn't understand concept"

#### Scenario: Unreduced fraction answer accepted
- **WHEN** the stored answer is `"2/4"` and the parent reports the child wrote `"2/4"`
- **THEN** skill marks the question correct

#### Scenario: Reduced fraction answer also accepted
- **WHEN** the stored answer is `"2/4"` and the parent reports the child wrote `"1/2"`
- **THEN** skill marks the question correct (mathematically equivalent)
