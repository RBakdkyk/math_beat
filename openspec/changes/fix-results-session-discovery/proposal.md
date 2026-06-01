## Why

When `/results` is invoked without a date, it blindly defaults to today — even if today has no session. The user expects the skill to discover which sessions exist (and which still need results) and ask which one to process. This caused a dead-end when yesterday's session was the obvious target but the skill looked at today and gave up.

A secondary issue: the skill's prompts and output were rendered in Hebrew. Parent-facing output should be in English (Hebrew is only for displaying the child's original question text and matching Hebrew answers).

## What Changes

- When no date argument is given, the skill lists sessions that have `generated.json` but no `results.json` and asks the user to pick one — instead of silently defaulting to today.
- If exactly one unprocessed session exists, auto-select it (with confirmation).
- If no unprocessed sessions exist, say so clearly.
- Ensure all skill output text (prompts, confirmations, summaries, error messages) is in English.

## Capabilities

### New Capabilities
- `session-discovery`: When no date is provided, scan available sessions, identify which ones lack results, and prompt the user to choose.

### Modified Capabilities
- `results-skill`: Update the invocation flow to use session-discovery before falling back to today. Ensure English-only output.

## Impact

- **Skill file**: `.claude/skills/results.md` — updated invocation flow (step 1-2)
- **No code changes needed**: `wiki.list_sessions()`, `wiki.read_results()`, and `wiki.results_path()` already provide everything needed for discovery
- **No breaking changes**: providing an explicit date still works exactly as before
