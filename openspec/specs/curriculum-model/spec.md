## ADDED Requirements

### Requirement: Topic tree with rule-based difficulty tiers
The system SHALL define a topic tree with three levels: topic → subtopic → skill. Each subtopic SHALL define difficulty tiers (easy/medium/hard) as number range constraints and validation rules — NOT as enumerated lists of parameter combinations. Python generates valid parameters at runtime from these rules.

#### Scenario: Fraction addition rules generate valid pairs
- **WHEN** the template engine needs an easy fraction addition question
- **THEN** the rule `{max_denom: 6, unit_fractions: True, constraint: "denom2 % denom1 == 0"}` generates valid pairs like (2,4), (3,6) at runtime

#### Scenario: Division rules respect curriculum scope
- **WHEN** the template engine needs a medium division question
- **THEN** the rule `{dividend_max: 500, divisor_range: (2,9)}` generates dividends and single-digit divisors at runtime, with the constraint that results are within 4th grade range

### Requirement: Hebrew question templates per subtopic
Each subtopic SHALL have at least 3 Hebrew template strings with placeholders for numbers. Templates provide phrasing variety while the rule-based generation provides number variety.

#### Scenario: Multiple multiplication templates
- **WHEN** a multiplication question is generated for fact 7×8
- **THEN** the system can choose from templates like: "כמה זה {a} × {b}?", "{a} × ___ = {result}, מה המספר החסר?", "מה המכפלה של {a} ו-{b}?"

### Requirement: Non-numeric answer types
Subtopics with categorical answers (prime/composite, symmetric/not, possible/impossible) SHALL define their answer type and valid answer values so the results skill can compare non-numeric responses.

#### Scenario: Prime/composite question
- **WHEN** a prime identification question is generated for number 17
- **THEN** the answer type is "categorical" with value "ראשוני" (prime) and the results skill can match the child's answer against it

### Requirement: Pedagogical constraints enforced via rules
Each subtopic SHALL carry constraint functions that validate generated parameters. The rules themselves ARE the constraints — no separate validation layer.

#### Scenario: Fraction constraint enforced
- **WHEN** generating parameters for fraction addition
- **THEN** the constraint `denom2 % denom1 == 0` ensures only "close" denominator pairs are generated

### Requirement: Multiplication table as discrete facts
The curriculum module SHALL define the multiplication table as 55 unique facts (exploiting commutativity). Each fact SHALL be individually trackable.

#### Scenario: Fact enumeration
- **WHEN** the multiplication table data is loaded
- **THEN** exactly 55 unique facts are available (2×2 through 10×10, deduplicated by commutativity)

### Requirement: Hour-weight exposure
Each topic SHALL expose its kita4 hour allocation as a numeric weight.

#### Scenario: Arithmetic operations weighted highest
- **WHEN** session composition reads topic weights
- **THEN** arithmetic operations has weight 50, fractions 25, shapes 15, measurements 11, natural numbers 10, data & probability 8, symmetry 4, number line 2
