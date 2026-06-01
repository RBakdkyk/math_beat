## Context

The `/results` skill is a Claude Code skill defined in `.claude/skills/results.md`. It instructs Claude how to converse with the parent when recording session results. Currently all example output, prompts, and confirmation messages in the skill file are in Hebrew. The parent (user) operates in English.

The Python backend (`analyze.py`, `progress.py`, `wiki.py`) already uses English for output and data structures. No Python changes are needed.

## Goals / Non-Goals

**Goals:**
- All `/results` conversational output (prompts, confirmations, summary tables, error messages, focus lines) in English
- Maintain Hebrew answer matching (the child answers in Hebrew, so matching logic must still handle Hebrew inputs like "ראשוני")

**Non-Goals:**
- Changing the generated questions language (questions stay in Hebrew for the child)
- Changing `summary.json` or `results.json` schema
- Changing `/practice` skill output language
- Changing answer matching behavior

## Decisions

**Single file change:** The entire change is in `.claude/skills/results.md`. This file contains the instructions that guide Claude's conversational behavior. By switching the example outputs and template strings to English, Claude will naturally output in English.

**Why not a code change?** The Hebrew output doesn't come from Python code — it comes from the skill instructions that Claude follows. The skill file is the single source of truth for the conversational UX.

**Keep Hebrew in answer matching notes:** The answer matching section references Hebrew strings like "ראשוני" and "חמישים ושש" because those are valid child answers. These stay as-is — they're matching rules, not output.

## Risks / Trade-offs

- [Minimal risk] Claude may occasionally fall back to Hebrew for certain outputs if the skill instructions don't fully override its tendencies → Mitigation: be explicit in the skill file that all output must be in English
