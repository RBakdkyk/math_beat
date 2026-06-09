## ADDED Requirements

### Requirement: Topics are classified for quiz rendering

The curriculum model SHALL classify each topic as either quiz-renderable or needs-visual. Needs-visual topics (`geometry`, `symmetry`) cannot be presented in static HTML without a figure and are excluded from the quiz. All template topics, plus `word-problems` and `probability`, are quiz-renderable.

#### Scenario: Visual topic flagged
- **WHEN** the wrap step inspects a `geometry` or `symmetry` question
- **THEN** the topic is reported as needs-visual and excluded from the quiz

#### Scenario: Text topic renderable
- **WHEN** the wrap step inspects a `word-problems` or `probability` question with a machine-checkable answer
- **THEN** the topic is reported as quiz-renderable

### Requirement: Each generated question carries widget metadata

The generator SHALL emit, on each question in `generated.json`, a `widget` field describing how the quiz should collect the answer: `text` for free entry (numeric, fraction, or typed strings such as `2^3`) or `choice` for button selection. For `choice` questions the generator SHALL also emit an `options` list of button labels. Widget metadata SHALL NOT be inferred from `type` or `answer_type`, since one `type` may mix shapes (e.g. `exponents` emits numeric, typed-string, and yes/no questions) and `answer_type == "categorical"` covers both typed strings and button choices.

#### Scenario: Prime-or-composite is a choice
- **WHEN** a `prime-composite` question is generated
- **THEN** it carries `widget: "choice"` and `options: ["ראשוני","פריק"]`

#### Scenario: Divisibility and yes/no exponent are choices
- **WHEN** a `divisibility` question or a `האם שווה?` exponent question is generated
- **THEN** it carries `widget: "choice"` and `options: ["כן","לא"]`

#### Scenario: Power-form exponent is text
- **WHEN** a `כתוב/י כחזקה` exponent question (answer like `2^3`) is generated
- **THEN** it carries `widget: "text"` and no `options`, because the answer is typed

#### Scenario: Numeric question is text
- **WHEN** a numeric question (e.g. multiplication, addition, fraction-addition) is generated
- **THEN** it carries `widget: "text"`

### Requirement: Fraction-comparison is presented as a symbol choice

`fraction-comparison` questions SHALL be presented as a `choice` of `>`, `<`, `=` with the canonical prompt `"סמני > או < או ="`, even though the stored answer is the larger fraction (or `"שווים"` when equal). The quiz uses this fixed framing regardless of which of the generator's prompt variants was stored.

#### Scenario: Comparison options and prompt are canonical
- **WHEN** the wrap step renders any `fraction-comparison` question
- **THEN** it shows the prompt `"סמני > או < או ="` with buttons `>`, `<`, `=`, ignoring the stored `description` variant
