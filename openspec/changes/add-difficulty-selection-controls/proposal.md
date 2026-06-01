## Why

This is change **B** of a two-part split. Change **A** (`define-per-topic-difficulty-levels`) defines and corrects *what* each easy/medium/hard band contains. This change governs *how a difficulty is chosen* for each topic in a session.

Two needs, both following from "treat Ayala as an advanced student":

1. **Manual per-topic override.** Today `--difficulty` is a single global value, and auto per-topic difficulty comes only from `_infer_difficulty`. There's no way to say "fractions hard, division easy" in one session — the exact "harder in some subjects, easier in others" control the project set out to provide.
2. **Advanced selection-skew.** An advanced student should be pitched up by default: the diagnostic/bootstrap session should start at `medium` (not `easy`), and `_infer_difficulty` should cross into harder tiers sooner.

**Depends on A:** these controls *select among* the bands A defines. A should land first. (B does not strictly require A's code to run — thresholds are independent — but the behavior is only meaningful once the bands are curriculum-correct.)

## What Changes

- **Manual per-topic difficulty override.** `--difficulty` accepts either a single global value OR `topic=level` assignments (e.g. `--difficulty fractions=hard division=easy`). Precedence per question: **per-topic override > global `--difficulty` > auto `_infer_difficulty`**.
- **Advanced selection-skew.** `_bootstrap_plan` starts non-warmup questions at `medium`; `_infer_difficulty` thresholds shift down (e.g. easy if rate < 0.3, hard if rate > 0.65) so harder tiers are reached sooner. The multiplication-table warmup stays weakness-targeted, unchanged.
- **Skill arg mapping.** `/practice` documents and parses per-topic difficulty syntax.

## Capabilities

### Modified Capabilities

- `session-composition`: per-topic difficulty override with defined precedence; advanced bootstrap/threshold skew.
- `practice-skill`: argument parsing maps per-topic difficulty (e.g. `fractions=hard`).

## Impact

- `generate.py` — parse `--difficulty` as global value OR `topic=level` assignments.
- `src/session.py` — `build_session_plan` accepts a per-topic difficulty map and applies the precedence rule; `_bootstrap_plan` starts at `medium`; `_infer_difficulty` thresholds shift down.
- `.claude/skills/practice.md` + `.claude/commands/practice.md` — document/parse per-topic difficulty; keep both files in sync.
- No data migration; `summary.json` schema unchanged.
- Out of scope: the persistent per-topic "level ladder" (stored, ratcheting level in `summary.json`) and weakness-aware param selection — both deferred (see A's design).
