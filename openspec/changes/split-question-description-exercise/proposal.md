## Why

Questions currently mix Hebrew description and math formula into a single string, which causes BiDi rendering issues in WhatsApp and makes formulas hard to read (e.g. `ב-9` looks like "and -9"). Splitting each question into a Hebrew prompt and a pure-math exercise line improves readability and eliminates the rendering ambiguity.

## What Changes

- **BREAKING**: Replace the `"he"` field in question dicts with two fields: `"description"` (Hebrew prompt) and `"exercise"` (pure math expression, no Hebrew)
- Remove all templates that embed Hebrew words in place of math operators (`כפול`, `פחות`, `ועוד`, `חלקי`, `בחזקת`)
- Update the formatter to render each question as two lines: description then indented exercise
- Update the Claude prompt (for word-problem/geometry/etc. topics) to return `description` and `exercise` separately
- Drop the now-unnecessary `_bidi_split` helper in `formatter.py`

## Capabilities

### New Capabilities

- `question-format`: Two-field question structure (description + exercise) and the rendering contract for all question types

### Modified Capabilities

<!-- none — no existing specs to delta -->

## Impact

- `src/curriculum.py` — `_q()` signature + all 15 generator functions; remove Hebrew-formula templates
- `src/formatter.py` — drop `_bidi_split`, new two-line render logic
- `src/generator.py` — update Claude prompt to return `description` + `exercise`
- `.claude/skills/practice.md` — may reference `q["he"]` directly
- `wiki/sessions/*/generated.json` — existing files use old `he` field (non-blocking; old sessions are read-only history)
