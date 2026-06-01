## ADDED Requirements

### Requirement: Numbered list format
The formatter SHALL output questions as a numbered Hebrew list, one question per line, suitable for WhatsApp copy-paste.

#### Scenario: Standard session output
- **WHEN** a session with 8 questions is formatted
- **THEN** output looks like:
  ```
  תרגול יומי - 08/05/2026

  חימום - לוח הכפל:
  1. כמה זה 7 × 8?
  2. כמה זה 6 × 9?
  3. כמה זה 4 × 7?

  שברים:
  4. מה גדול יותר: 1/3 או 1/5?
  5. חשבי: 1/2 + 1/4 = ?
  ```

### Requirement: Plain text only
Output SHALL NOT contain LaTeX, markdown formatting, emoji, or special Unicode characters. Fractions as `1/2`, multiplication as `×` (Unicode ×, the standard multiply sign WhatsApp renders well).

#### Scenario: No special formatting
- **WHEN** any question is formatted
- **THEN** it contains only Hebrew text, digits, basic arithmetic operators (+, -, ×, ÷, =, /), and punctuation

### Requirement: Block headers in Hebrew
Each question block SHALL have a Hebrew header identifying the topic (e.g., "חימום - לוח הכפל", "שברים", "חילוק עם שארית").

#### Scenario: Block labeling
- **WHEN** a session has warmup and main blocks
- **THEN** each block has a Hebrew header before its questions
