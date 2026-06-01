## Why

The `/results` skill currently uses Hebrew for all its conversational output (prompts, confirmations, summary tables, progress focus lines). Since the parent using the tool works in English, this creates unnecessary friction. The history accumulation (summary.json content, analyze.py output) should also be consistently English.

## What Changes

- Switch all `/results` skill output from Hebrew to English: prompts, confirmation messages, summary tables, error messages, and the "tomorrow focus" line
- Update the results skill instructions (`.claude/skills/results.md`) to use English throughout
- Ensure `analyze.py` output remains English (already is) and the focus-for-tomorrow line is English

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `results-skill`: All user-facing output changes from Hebrew to English. No behavioral changes to answer matching, results writing, or progress tracking.

## Impact

- **Code**: `.claude/skills/results.md` — primary change target (skill instructions that drive Claude's output)
- **No Python changes needed**: `analyze.py` already outputs in English; `progress.py` and `wiki.py` are data-layer only
- **No breaking changes**: `results.json` schema is unchanged; `summary.json` structure unchanged
- **Questions remain in Hebrew**: this change only affects the skill's conversational output, not the generated math questions
