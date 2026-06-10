## Why

Generated sessions are far narrower than the curriculum they are meant to cover (`src/curriculum_knowledge.md`, 8 Ministry topics / ~30 subtopics). Every 8-question session touches only **3 distinct topics** (warmup + main + secondary), and worse: the two non-warmup picks are effectively **arbitrary**, because 12 never-practiced topics are tied at the same priority score (0.750) and the planner just takes the first two by set ordering. On top of that, the priority formula ranks a *never-seen* topic (0.750) **above** a topic Ayala actually got wrong (subtraction at 0% correct scores 0.701) — "new" beats "weak", which is backwards for a weakness-targeting tool. The catalog also has no generator for cuboid volume/surface area (Ministry ח.2), so that topic can never appear.

## What Changes

- **Zoned session planner.** Replace the 1-main + 1-secondary split in `_adaptive_plan` with a top-K-distinct spread: **warmup** (3 multiplication questions) + **primary depth** (2 questions on the #1-priority topic) + **rotation** (1 question each across the next distinct topics in priority order). A default 10-question session yields **≥5 distinct topics** (the default count rises from 8 to 10). There is no separate "least-touched coverage" pick — least-touched topics already rank at the top of `_topic_priority` (staleness + coverage terms), so breadth and long-tail coverage fall out of the distinct-topic spread itself.
- **Graceful zone scaling for `--count ≠ 8`.** Zone sizes are derived from `count` (sum exactly to `count`) and degrade cleanly for small counts (warmup shrinks first), defined across the supported 5–10 range. A stated fallback allows topic repeats only if distinct topics are exhausted.
- **Priority quirk fix.** Adjust `_topic_priority` so a topic answered incorrectly is prioritized **at least as highly** as a never-practiced topic. Weakness rotation stays pure — no curriculum-hours weighting is introduced.
- **One new template generator** to fill a Ministry coverage gap: `volume-surface-area` (Ministry ח.2 — cuboid volume + surface area; extends the existing `measurements-*` topics). Stdlib-only, Hebrew question text, numeric answers, stable `volume:`/`surface:` signatures.
- **Simplify the `/practice` focus line.** The skill's one-line progress summary currently names a single `{main_topic}`, which no longer exists under the zoned spread. Drop the per-session main-topic naming; the summary keeps the multiplication-warmup context (and weak facts) only.
- **Explicitly NOT changed:** no curriculum-hours weighting of topic frequency; the `TOPICS` hours table (180h vs the doc's 125h) stays cosmetic and untouched; no `calendar-time` generator (date/gematria — out of scope); no `number-line` generator (inherently visual — out of scope); no Data-investigation generator (ה.1 — needs Claude); no changes to Claude-only topics.

## Capabilities

### New Capabilities
<!-- None — all changes extend existing capabilities. -->

### Modified Capabilities
- `session-composition`: the **Session structure** requirement changes from a 3-block (warmup/main/secondary) shape to a zoned top-K-distinct spread (warmup + primary depth + rotation, ≥5 distinct topics/session) with a count-scaling rule across 5–10; the **Topic selection by weakness** requirement changes so an incorrectly-answered topic ranks at least as high as a never-practiced one; the **Question count** scaling is restated for the zones.
- `curriculum-model`: the topic catalog gains one new subtopic (`volume-surface-area`) with difficulty tiers, Hebrew templates, numeric answer type, and `volume:`/`surface:` signatures, closing the Ministry coverage gap for ח.2.
- `practice-skill`: the **Skill shows brief progress context** requirement changes to drop the single `{main_topic}` from the focus line, since the zoned planner no longer has one main topic.

## Impact

- **Code:** `src/session.py` (`_adaptive_plan`, `_topic_priority`, a zone-scaling helper), `src/curriculum.py` (one new generator function, `TOPICS` entry, `_GENERATORS` registration, difficulty bands), `.claude/skills/practice.md` (focus-line wording).
- **Behavior:** sessions become broader (≥5 vs 3 distinct topics) and selection becomes deterministic-by-merit rather than arbitrary-among-ties; weak topics resurface ahead of unseen ones.
- **Data:** new signatures (`volume:…` / `surface:…`); `summary.json` gains a progress entry for `volume-surface-area` on first practice. No migration needed — `summary.json` is rebuildable via `analyze.py --rebuild`.
- **Docs/contract:** the 3-warmup promise in `CLAUDE.md` is preserved, so no doc change is required there.
- **Out of scope / untouched:** `TOPICS` hours table, curriculum weighting, Claude-only topics, `calendar-time`, `number-line`, Data-investigation (ה.1).
