## ADDED Requirements

### Requirement: Wrap a session into a self-contained HTML quiz

The system SHALL provide a `quiz.py` entry point that reads a session's `generated.json` and writes a single self-contained `wiki/sessions/{date}/quiz.html` (inline CSS/JS, no external assets, no network calls). The HTML SHALL NOT contain the answer key.

#### Scenario: Generate a quiz for an existing session
- **WHEN** `python quiz.py 2026-06-09` is run and `wiki/sessions/2026-06-09/generated.json` exists
- **THEN** `wiki/sessions/2026-06-09/quiz.html` is written as a single self-contained file containing each question's `description` and `exercise` but none of the `answer` values

#### Scenario: Quiz already exists
- **WHEN** `quiz.html` already exists for the date and `--force` is not given
- **THEN** the command refuses to overwrite and reports that `--force` is required

#### Scenario: No session for the date
- **WHEN** `python quiz.py 2026-06-09` is run and no `generated.json` exists for that date
- **THEN** the command reports that no session was found and exits without writing a file

### Requirement: Input widget chosen by per-question metadata

The quiz SHALL render each question's input from its `widget`/`options` metadata: `text` → a free-text entry field (which MUST accept `/`, `,`, `.`, `-`, never an `<input type="number">`); `choice` → buttons labeled by `options`. Widget selection SHALL NOT be derived from `type` or `answer_type`.

#### Scenario: Text question
- **WHEN** a question has `widget: "text"` (e.g. a fraction answer like `40/32`)
- **THEN** the quiz renders a free-text field that accepts `/` and `,`

#### Scenario: Choice question
- **WHEN** a question has `widget: "choice"` and `options: ["ראשוני","פריק"]`
- **THEN** the quiz renders one button per option and records the selected label

#### Scenario: Fraction-comparison framing
- **WHEN** a `fraction-comparison` question is rendered
- **THEN** the quiz shows the prompt `"סמני > או < או ="` with buttons `>`, `<`, `=`, and records the selected symbol

### Requirement: Done button builds and URL-encodes the WhatsApp return code

The quiz SHALL include a "Done" control that encodes the entered answers as `AYL~<date>~<base64 JSON [[id,"answer"], …]>~<check>` and opens `https://wa.me/<PARENT_WHATSAPP>?text=<encodeURIComponent(code)>`, where the number is read from `.env` at generation time. Base64 SHALL be standard (not urlsafe) and the check char SHALL be `BASE36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]`. The `text` parameter SHALL be percent-encoded so base64 `+`/`/` survive transport.

#### Scenario: Encode entered answers
- **WHEN** the child enters answers and presses Done
- **THEN** the quiz builds a code whose decoded payload is `[[id,"answer"], …]` for every RENDERED question, with rendered-but-unanswered questions encoded as `""` and excluded (needs-visual) questions absent entirely

#### Scenario: Return link is percent-encoded
- **WHEN** the generated code contains a base64 `+` or `/`
- **THEN** the opened link percent-encodes the `text` parameter so the pasted code round-trips intact

#### Scenario: Check char is valid
- **WHEN** a code is generated for any session
- **THEN** its trailing check char equals `BASE36[ sum(bytes("AYL~"+date+"~"+b64)) % 36 ]`

### Requirement: Needs-visual questions are excluded

The quiz SHALL exclude questions whose topic is classified needs-visual (`geometry`, `symmetry`) because static HTML cannot render the required figure, emitting a generation-time warning naming each excluded question. Excluded questions are absent from the rendered set and from the return code. All other topics — including `word-problems` and `probability` — SHALL be rendered as text plus the metadata-appropriate widget.

#### Scenario: Session forced to include a visual topic
- **WHEN** a session includes a `geometry` question and `quiz.py` runs
- **THEN** that question is omitted from `quiz.html`, a warning naming it is printed, the remaining questions are rendered normally, and the omitted id never appears in the return code

#### Scenario: Word-problem question
- **WHEN** a session includes a `word-problems` question with a numeric answer
- **THEN** it is rendered in the quiz as its `description` text plus a free-text entry field

### Requirement: Parent WhatsApp number comes from .env

The system SHALL read `PARENT_WHATSAPP` from a `.env` file using a stdlib-only `KEY=VALUE` parser (no third-party dependency) and normalize it to `wa.me` form (digits only) when building the return link. `.env` SHALL be listed in `.gitignore`.

#### Scenario: Number normalized for wa.me
- **WHEN** `.env` contains `PARENT_WHATSAPP=+972 50-123-4567`
- **THEN** the return link uses `https://wa.me/972501234567?text=...`

#### Scenario: Missing number
- **WHEN** `quiz.py` runs and `.env` has no `PARENT_WHATSAPP`
- **THEN** the command reports that `PARENT_WHATSAPP` must be set in `.env` and exits without writing a file
