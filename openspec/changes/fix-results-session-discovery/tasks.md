## 1. Session Discovery

- [x] 1.1 Add session-discovery step to `.claude/skills/results.md`: new step between "Determine the date" and "Load generated.json" that runs an inline Python snippet calling `list_sessions()`, checking each for `generated.json` without `results.json`, and returning the list of unprocessed dates
- [x] 1.2 Implement three-way branch in the skill: zero unprocessed → inform parent; one → auto-select with confirmation; many → numbered list for parent to pick

## 2. Inline Results

- [x] 2.1 Update the "Determine the date" step in `.claude/skills/results.md` to parse invocation args for both a date and inline result text, storing any inline results for later
- [x] 2.2 Update the "Invite parent to report results" step to skip the reporting prompt when inline results were provided, proceeding directly to processing them

## 3. English Output

- [x] 3.1 Audit all prompt/message strings in `.claude/skills/results.md` and replace any remaining Hebrew text with English equivalents (keep Hebrew only for displaying original question text and answer matching)

## 4. Verification

- [x] 4.1 Test `/results` with no sessions — confirm "All sessions have results" message
- [x] 4.2 Test `/results` with one unprocessed session — confirm auto-select with confirmation prompt
- [x] 4.3 Test `/results 2026-05-08` with explicit date — confirm existing behavior unchanged
- [x] 4.4 Test `/results two wrong: 63/9, 4/5 vs 1/5` — confirm discovery + inline processing without re-asking
