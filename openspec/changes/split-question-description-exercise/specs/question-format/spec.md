## ADDED Requirements

### Requirement: Question dict has description and exercise fields
Every question dict produced by `curriculum.py` or `generator.py` SHALL contain a `"description"` field (Hebrew prompt text) and an `"exercise"` field (pure math expression using only math symbols and digits — no Hebrew characters).

#### Scenario: Template-generated question
- **WHEN** `make_question()` is called for any template-based topic
- **THEN** the returned dict contains `"description"` (non-empty Hebrew string) and `"exercise"` (non-empty string with no Hebrew characters)

#### Scenario: Claude-generated question
- **WHEN** `generator.py` falls back to Claude for a topic like word-problems
- **THEN** the returned dict contains `"description"` and `"exercise"` fields matching the same contract

#### Scenario: Old "he" field absent
- **WHEN** a question is generated after this change
- **THEN** the dict does NOT contain a `"he"` field

### Requirement: Exercise field contains no Hebrew
The `"exercise"` field SHALL contain only digits, math operators (`× ÷ + − = < > _`), fraction notation (`/`), exponent notation (`^`), parentheses, spaces, and comma-separated digit groupings. No Hebrew Unicode characters (`\u05D0`–`\u05EA`) are permitted.

#### Scenario: Multiplication exercise
- **WHEN** a multiplication-table question is generated
- **THEN** `exercise` is a string like `"7 × 8 ="` or `"3 × ___ = 12"` with no Hebrew letters

#### Scenario: Divisibility exercise
- **WHEN** a divisibility question is generated
- **THEN** `exercise` is a string like `"36 ÷ 9"` with no Hebrew letters (no `ב-`)

#### Scenario: Fraction comparison exercise
- **WHEN** a fraction-comparison question is generated
- **THEN** `exercise` is a string like `"3/4 ___ 7/8"` with no Hebrew letters

### Requirement: Formatter renders two lines per question
`formatter.py` SHALL render each question as:
```
{id}. {description}
   {exercise}
```
where the exercise is indented by 3 spaces on the line immediately below the description.

#### Scenario: Standard two-line render
- **WHEN** `format_session()` processes a question with `description` and `exercise`
- **THEN** output contains `"{id}. {description}\n   {exercise}"`

#### Scenario: Backwards-compatible fallback
- **WHEN** a question dict has `"he"` but no `"description"` (old session file)
- **THEN** formatter renders the `"he"` value on a single line without crashing

### Requirement: Hebrew-operator templates removed
No question template SHALL use Hebrew words in place of math operators. Specifically, templates containing `כפול`, `פחות`, `ועוד`, `חלקי`, or `בחזקת` as stand-ins for `×`, `−`, `+`, `÷`, `^` SHALL be deleted.

#### Scenario: Multiplication table variety
- **WHEN** `_mult_table()` is called 100 times
- **THEN** no generated `exercise` contains the word `כפול`

#### Scenario: Subtraction variety
- **WHEN** `_subtraction()` is called 100 times
- **THEN** no generated `exercise` contains the word `פחות`
