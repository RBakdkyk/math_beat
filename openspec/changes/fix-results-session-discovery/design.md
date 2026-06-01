## Context

The `/results` skill currently defaults to today's date when no argument is given. If today has no `generated.json`, it hits a dead end. The parent then has to re-invoke with an explicit date — but they may not remember the exact date.

Meanwhile, `wiki.py` already exposes `list_sessions()` and `read_results()`, which together can identify sessions that have questions but no results yet. No new Python code is needed.

## Goals / Non-Goals

**Goals:**
- When no date is given, discover unprocessed sessions and let the parent pick one
- Auto-select when there's exactly one obvious choice
- Keep all skill output in English

**Non-Goals:**
- Changing the Python codebase (wiki.py, analyze.py, etc.)
- Handling multi-session batch entry
- Changing behavior when an explicit date IS provided

## Decisions

### Discovery logic lives entirely in the skill file

The skill file (`.claude/skills/results.md`) already contains inline Python snippets for loading data. The session discovery step will use the same pattern — a small inline Python snippet that calls `list_sessions()`, checks each for `generated.json` and `results.json`, and returns the list of unprocessed dates.

**Why not add a helper to wiki.py?** This is a single query composed of two existing functions. Adding a dedicated function would be premature — the skill file is the only consumer, and the inline snippet is ~5 lines.

### Auto-select when exactly one unprocessed session exists

If discovery finds exactly one session without results, the skill auto-selects it and confirms: "Found unprocessed session from {date}. Process this one?" This avoids a pointless menu for the common case (parent runs /results the day after practice).

**Why confirm instead of just proceeding?** The parent might have invoked /results by mistake or might want to re-process an older session. A one-line confirmation costs almost nothing.

### Three-way branch: zero, one, or many unprocessed sessions

- **Zero:** "All sessions have results. To re-process one, run `/results YYYY-MM-DD`."
- **One:** Auto-select with confirmation.
- **Many:** Show numbered list, ask parent to pick.

## Risks / Trade-offs

- **[Risk] Session directory exists but generated.json is corrupt or empty** → The existing `read_generated()` returns `None` for missing/broken files, so these are naturally filtered out. No extra handling needed.
- **[Trade-off] Inline Python in skill file vs. wiki.py helper** → Keeps wiki.py clean but means the discovery logic isn't reusable. Acceptable since no other consumer exists.
