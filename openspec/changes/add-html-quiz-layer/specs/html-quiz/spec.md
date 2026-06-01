## ADDED Requirements

### Requirement: Build self-contained quiz HTML from a session
The system SHALL build a single self-contained `quiz.html` from a session's `generated.json`, containing all CSS and JavaScript inline with no external network, CDN, or font dependencies, saved to `wiki/sessions/{date}/quiz.html`. The page SHALL open and function fully offline on both phone and computer browsers.

#### Scenario: Build from an existing session
- **WHEN** the quiz builder runs for a date whose `wiki/sessions/{date}/generated.json` exists
- **THEN** it writes `wiki/sessions/{date}/quiz.html` containing every question and requiring no network access to load or operate

#### Scenario: No session to build from
- **WHEN** the quiz builder runs for a date with no `generated.json`
- **THEN** it reports that no session exists for that date and writes no file

#### Scenario: Write-once protection
- **WHEN** `quiz.html` already exists for the date and `--force` is not supplied
- **THEN** the builder does not overwrite it and reports the existing file (consistent with `generated.json`/`results.json` write-once convention)

### Requirement: Free-text answer entry rendered RTL in Hebrew
The quiz SHALL render each question's Hebrew instruction and exercise with a free-text answer input per question, laid out right-to-left. Except for fraction-comparison questions (see below), the quiz SHALL NOT present multiple-choice options or distractors. Numeric and categorical questions SHALL be rendered with the same free-text mechanism. The builder SHALL render `description` + `exercise` when present and fall back to the `he` field when they are absent, so no question renders blank.

#### Scenario: Numeric question rendered
- **WHEN** a question has `answer_type` "numeric" (e.g. `57 + 87`)
- **THEN** the page shows its Hebrew instruction and exercise with an empty text box for her answer

#### Scenario: Categorical question rendered
- **WHEN** a question has `answer_type` "categorical" (e.g. a yes/no or prime/composite question)
- **THEN** the page shows it with the same free-text box, with no fabricated options

### Requirement: Comparison questions use tappable sign buttons
Fraction-comparison questions (exercise of the form `<left> ___ <right>`) SHALL be rendered NOT as a free-text box but as three tappable sign buttons (`<`, `=`, `>`) in a forced left-to-right row between the two fractions. This avoids the RTL mirroring that flips `<`/`>` in a right-to-left text box. The tapped sign SHALL be stored as the question's answer in the result code; if no sign is tapped, the answer is blank.

#### Scenario: Comparison rendered as sign buttons
- **WHEN** a question's subtopic is `fraction-comparison` and its exercise contains `___`
- **THEN** the page shows the left fraction, three buttons `<` `=` `>`, and the right fraction in a left-to-right row, with no free-text box for that question

#### Scenario: Tapped sign captured faithfully
- **WHEN** the child taps a sign for a comparison question
- **THEN** the result code carries exactly that sign (`<`, `=`, or `>`) for that question, unaffected by the page's right-to-left direction

#### Scenario: Legacy he-only question rendered
- **WHEN** a question has only a `he` field and no `description`/`exercise`
- **THEN** the page renders the `he` text with a free-text box rather than a blank entry

### Requirement: Quiz does not embed answers or grade
The quiz SHALL NOT embed correct answers and SHALL NOT compute correctness in the browser. It is a collect-and-send form; grading is performed later by `/results`.

#### Scenario: No answers in the page
- **WHEN** the generated `quiz.html` is inspected (e.g. view-source)
- **THEN** it contains no correct answers and no grading logic

#### Scenario: No score shown to the child
- **WHEN** the child finishes the quiz
- **THEN** the page does not display a score or per-question correct/incorrect feedback

### Requirement: Generate a result code with all answers and a checksum
On finish, the quiz SHALL build a compact result code carrying the session date, all of the child's typed answers in question order (blanks for unanswered questions), and a trailing checksum character. The encoding SHALL safely round-trip Hebrew text and fraction answers (including `/`) through a `wa.me` URL, and the checksum SHALL be computed over the canonical payload so a corrupted code can be detected.

#### Scenario: Code reflects all answers
- **WHEN** the child finishes a session of 8 questions, answering 6 and leaving 2 blank
- **THEN** the generated code encodes the date, all 8 answer slots (6 filled, 2 blank), and a checksum

#### Scenario: Hebrew and fraction answers survive encoding
- **WHEN** a typed answer contains Hebrew text or a fraction such as `4/5`
- **THEN** the code encodes it such that the decoder reconstructs the exact original string

### Requirement: One-tap WhatsApp return with copy fallback
The quiz SHALL provide a "שלחי לאבא" control that opens `wa.me/<parent-number>?text=<code>` with the result code pre-filled, where the parent number comes from configuration baked into the generated HTML in international format with no `+`. The page SHALL also always display the code in a copyable form as a fallback for browsers where the `wa.me` link does not work.

#### Scenario: Pre-filled WhatsApp message
- **WHEN** the child taps "שלחי לאבא" after finishing
- **THEN** WhatsApp (app on phone, Web on desktop) opens addressed to the configured parent number with the result code already in the message body, requiring only a send tap

#### Scenario: Fallback copy path
- **WHEN** the `wa.me` link does not open in the child's browser
- **THEN** the result code is visible on the page in a form she can copy and send manually
