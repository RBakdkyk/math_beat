## MODIFIED Requirements

### Requirement: Topic tree with rule-based difficulty tiers
The system SHALL define a topic tree with three levels: topic → subtopic → skill. Each subtopic SHALL define difficulty tiers (easy/medium/hard) as number range constraints and validation rules — NOT as enumerated lists of parameter combinations. Python generates valid parameters at runtime from these rules.

Each subtopic's three tiers SHALL be **distinct**: the parameter space of `hard` MUST NOT be a subset of `medium`, and `medium` MUST NOT be a subset of `easy`. A tier that does not widen or harden the space relative to the tier below it is invalid.

#### Scenario: Fraction addition rules generate valid pairs
- **WHEN** the template engine needs an easy fraction addition question
- **THEN** the rule `{max_denom: 6, unit_fractions: True, constraint: "denom2 % denom1 == 0"}` generates valid pairs like (2,4), (3,6) at runtime

#### Scenario: Division rules respect curriculum scope
- **WHEN** the template engine needs a medium division question
- **THEN** the rule `{dividend_max: 500, divisor_range: (2,9)}` generates dividends and single-digit divisors at runtime, with the constraint that results are within 4th grade range

#### Scenario: Tiers are genuinely distinct
- **WHEN** the easy/medium/hard parameter spaces for any subtopic are compared
- **THEN** each higher tier admits at least one parameter combination the lower tier does not, so `hard` is provably harder than `medium`

### Requirement: Pedagogical constraints enforced via rules
Each subtopic SHALL carry constraint functions that validate generated parameters. The rules themselves ARE the constraints — no separate validation layer.

Constraints SHALL encode the kita4 pedagogical prohibitions, in particular: fraction comparison and fraction operations use intuitive strategies only (no common-denominator or cross-multiplication algorithm); fraction denominators are restricted to the familiar set {2, 3, 4, 5, 6, 8, 10}; division divisors are single-digit OR whole tens.

#### Scenario: Fraction constraint enforced
- **WHEN** generating parameters for fraction addition
- **THEN** the constraint `denom2 % denom1 == 0` ensures only "close" denominator pairs are generated

#### Scenario: Fraction comparison avoids forbidden algorithm
- **WHEN** generating any fraction-comparison question at any difficulty
- **THEN** the two fractions share a denominator, share a numerator, or are comparable by proximity to ½/1 — never an unrelated-denominator pair that would require a common-denominator algorithm
- **AND** both denominators are drawn from the familiar set {2, 3, 4, 5, 6, 8, 10}

#### Scenario: Division divisor stays in scope
- **WHEN** generating any division question
- **THEN** the divisor is either single-digit (1–9) or a whole ten (10, 20, 30, …)

## ADDED Requirements

### Requirement: Difficulty bands are curriculum-validated and grade-4-bounded
Every difficulty tier of every subtopic SHALL be validated against `src/curriculum_knowledge.md`. Because the student is treated as advanced, the `hard` tier SHALL be the curriculum's "advanced classes" (כיתות מתקדמות) grade-4 task, embraced — and SHALL NOT require any method or magnitude reserved for grade 5 or above. The advanced/grade-4 boundary, not the all-students/advanced boundary, is the ceiling.

#### Scenario: Multiplication hard is the advanced grade-4 task
- **WHEN** a hard multiplication question is generated
- **THEN** it MAY be a 2-digit × 3-digit product (the advanced grade-4 written-multiplication task, L227/L841), and SHALL NOT exceed it into larger-than-grade-4 magnitudes; easy is 1-digit × 2-digit and medium is the standard 2-digit × 2-digit

#### Scenario: No grade-5 fraction methods
- **WHEN** a hard fraction question is generated
- **THEN** it is solvable by equal/related-denominator intuition (including mixed-number results), and never requires formal reduction/expansion or unrelated-denominator comparison (grade-5 methods)

#### Scenario: Column arithmetic stays within grade-4 magnitude
- **WHEN** a hard addition or subtraction question is generated
- **THEN** operands are at most 4-digit — column addition/subtraction of 4–5 digit numbers is an explicit grade-4 task (L208) done by hand — and never extend beyond, so every tier remains by-hand grade-4 practice (no calculator tier)

### Requirement: In-scope difficulty bands are not omitted
Where the curriculum defines a harder-but-in-scope variant of a topic, the generator SHALL be able to produce it. Specifically: division SHALL be able to produce whole-tens divisors and remainder cases below the hard tier; order-of-operations SHALL be able to include division within expressions.

#### Scenario: Whole-tens division is reachable
- **WHEN** division questions are generated across difficulties
- **THEN** at least one tier produces whole-tens divisors (e.g. 840 ÷ 20), not only single-digit divisors

#### Scenario: Order of operations includes division
- **WHEN** order-of-operations questions are generated
- **THEN** generated expressions can include the ÷ operator, exercising division-before-addition precedence

#### Scenario: Order of operations stays integer and non-negative
- **WHEN** an order-of-operations expression containing ÷ is generated
- **THEN** every ÷ has exactly-divisible operands and the whole expression evaluates to a non-negative integer (no fractions, no negatives in grade 4)

### Requirement: Fraction answers are stored unreduced
Because formal reduction/expansion is a grade-5 skill (L134, L776), generated fraction answers SHALL be expressed in the grade-4-natural denominator actually used (the common or related denominator), NOT in Python `Fraction`'s automatically reduced form. Mixed-number results are permitted, built on the unreduced fraction.

#### Scenario: Equal-denominator sum keeps the denominator
- **WHEN** a fraction-addition question `1/4 + 1/4` is generated
- **THEN** the stored answer is `"2/4"`, not `"1/2"`

#### Scenario: Related-denominator result uses the larger denominator
- **WHEN** a fraction-addition question `2/3 + 1/6` is generated
- **THEN** the stored answer is expressed in sixths (e.g. `"5/6"`), not a reduced form
