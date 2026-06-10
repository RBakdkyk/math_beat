## Context

The session planner lives in `src/session.py`. `build_session_plan` delegates to `_adaptive_plan` (when progress exists) or `_bootstrap_plan` (cold start). `_adaptive_plan` currently:

1. Reserves 3 warmup slots for `multiplication-table`, targeting the weakest facts.
2. Calls `_prioritized_topics(exclude={"multiplication-table"})` → a list sorted by `_topic_priority` (weakness 0.5 + staleness 0.3 + coverage 0.2).
3. Takes only `sorted_topics[0]` (main) and `sorted_topics[1]` (secondary), splitting the remaining slots ~65/35.

Two empirical problems were confirmed against live `summary.json`:

- **12 topics tie at 0.750** (all never-practiced), so "top-2" is arbitrary set ordering, not merit.
- A wrong-answer topic (subtraction, correct_rate 0.0) scores **0.701 — below** the 0.750 of unseen topics. Staleness+coverage (capped) outweigh weakness for fresh topics, so "new" beats "wrong".

Separately, the question catalog (`src/curriculum.py`, `TOPICS` + `_GENERATORS`) has no generator for Ministry topic ח.2 (cuboid volume / surface area), so it can never be selected.

Constraints: stdlib-only, Hebrew question text, English code, write-once session files, signatures `"{type}:{params}"`. The grader supports only `numeric`, `categorical`, and `text` answer types. The 3-warmup contract in `CLAUDE.md` must be preserved.

## Goals / Non-Goals

**Goals:**
- A default 10-question session covers **≥5 distinct topics** while keeping 3 multiplication warmups and 2-deep drill on the top weakness.
- Topic selection is deterministic-by-merit, not arbitrary among ties; breadth spreads across the tied block.
- A wrong-answer topic ranks **≥** a never-practiced topic.
- One new template topic (`volume-surface-area`) fills the ח.2 coverage gap and slots into the existing planner/grader unchanged.
- The `/practice` focus line stops naming a single main topic.

**Non-Goals:**
- No curriculum-hours weighting of topic frequency (pure weakness rotation).
- No reconciliation of the `TOPICS` hours table (180h vs the doc's 125h) — it stays cosmetic.
- No `calendar-time` generator (date/gematria — hard to template and grade with stdlib; dropped).
- No `number-line` generator (inherently visual; positional reading is ambiguous as plain text; dropped).
- No Data-investigation generator (ה.1) — needs Claude.
- No changes to Claude-only topics.

## Decisions

### Decision 1: Zoned planner = warmup + primary depth + distinct-topic spread (no separate coverage pick)
Replace the main/secondary truncation with: 3 warmups (weak facts) + 2 questions on `sorted_topics[0]` (depth) + 1 question each on the next distinct topics in priority order until the budget is filled.

- **Why no "coverage" zone:** The existing `_topic_priority` already lifts least-touched topics *above* well-practiced ones (0.750 > 0.201 in live data). Least-touched therefore appears at the **top** of the spread, not in a reserved last slot — a separate "least-touched coverage" pick would contradict the ranking and duplicate logic already in `_topic_priority`. The distinct-topic spread gives long-tail coverage for free.
- **Alternative considered — explicit `_coverage_pick`:** redundant and contradictory (see above). Rejected.
- **Alternative considered — pure spread (1 each, no depth):** 1 question/topic is too noisy to update `correct_rate` meaningfully and abandons drilling. Rejected.
- `multiplication-table` stays excluded from the non-warmup spread (`exclude={"multiplication-table"}`), as today.
- **`_bootstrap_plan` (cold start) is NOT changed.** It already emits 3 warmups + a curated diagnostic core of 5 distinct fundamentals at the "advanced pitch" **medium** difficulty — i.e. it was never the narrow path; narrowness lived only in `_adaptive_plan`. Forcing the priority-driven distinct-topic spread onto a brand-new student would pull advanced/random topics (e.g. `volume-surface-area`, `exponents`) into the first diagnostic, which is undesirable. Cold start keeps the curated core and medium difficulty.

### Decision 2: Zone scaling as a function of count (any count ≥ 1)
Derive zone sizes from `count` so they always sum exactly to `count`, for any count ≥ 1 (`generate.py` does not clamp `--count`, so the helper must not assume a 5–10 window):
- warmup = `min(3, count)`; for small counts the warmup shrinks first so breadth survives (e.g. count 5 → warmup 2, count 2 → warmup 2 and nothing else).
- primary depth = 2 when the post-warmup remainder ≥ 4, else 1 (or 0 if no remainder).
- the rest are 1-each rotation slots across distinct topics in priority order.

Concretely: count 8 → 3 + 2 + 3 rotation; count 10 → 3 + 2 + 5 rotation; count 5 → 2 + 1 + 2 rotation; count 12 → 3 + 2 + 7 rotation. Implemented as a small helper returning the per-zone counts so the rule is testable in isolation. If distinct available topics < rotation slots, repeats are allowed only after all distinct topics are used (not a realistic case with ~21 template topics, but defined for safety).

- **Why:** Keeps the default-count contract exact while degrading predictably at any count; a single helper makes the arithmetic unit-testable without generating questions.

### Decision 3: Priority quirk fix — floor weakness for wrong topics
In `_topic_priority`, ensure a practiced topic with low `correct_rate` cannot rank below a never-practiced topic. Chosen approach: when `times_practiced > 0` and `correct_rate` is low, **boost the weakness contribution** so the total ≥ the never-practiced baseline (0.750). Simplest concrete form: raise the weakness weight and/or add a small "answered-wrong" floor term, tuned so `correct_rate 0.0, practiced ≥1` ≥ the unseen baseline.

- **Why:** Directly encodes "weakness ≥ unfamiliarity" without introducing curriculum weighting.
- **Alternative considered — lower the never-practiced baseline (drop staleness cap):** would suppress legitimate coverage of new topics and risk starving the catalog. Rejected.
- **Validation:** assert `_topic_priority("subtraction", {correct_rate:0.0, times_practiced:1, last_practiced:recent}) >= _topic_priority("x", {})` (the unseen default).

### Decision 4: `volume-surface-area` mirrors existing template-topic shape
Adds: a `TOPICS` entry (name + nominal hours), difficulty tiers in the same rule style as existing topics, a `_volume_surface_area` generator returning the standard `_q(...)` dict, and `_GENERATORS` registration. It is a **template** topic (not in `CLAUDE_TOPICS`).
- Cuboid `a×b×c` volume and `2(ab+bc+ca)` surface area; tiers scale the dimensions. **Numeric** answers only (no new answer type). Signatures `volume:{params}` / `surface:{params}`. Reuse the `measurements-*` unit/phrasing style for consistency.
- **Why:** Reusing `_q`, the tier convention, and numeric answers means the planner, formatter, and results grader need zero changes to support it.

### Decision 5: `/practice` focus line drops the single main topic
The zoned planner has no single main topic, so the skill's one-line summary in `.claude/skills/practice.md` (and any `{main_topic}` interpolation) is reworded to mention multiplication-warmup context + "rotating practice across weakest topics", without naming one main topic. The WhatsApp `formatter.py` needs no change — it groups questions by qtype and falls back to `TOPICS[name]`, so the new topic and multi-topic sessions already render.

## Risks / Trade-offs

- **[Breadth dilutes drilling depth]** → Keep the #1 weakness at 2 questions and preserve 3 warmups; only the *tail* slots spread. Net drill on the top priority is unchanged from today.
- **[New topic floods in via high coverage score]** → Acceptable and intended for introduction; the priority-quirk fix and ordinary staleness decay keep it from dominating once practiced.
- **[Priority tuning could over/under-shoot the 0.750 baseline]** → Pin it with a unit test asserting the wrong-vs-unseen ordering, so a future weight change can't silently regress it.
- **[Curriculum-knowledge alignment]** → `volume-surface-area` difficulty bands and scope SHALL be grep-checked against `src/curriculum_knowledge.md` (ח.2) during implementation, per project convention.

## Migration Plan

No data migration. New signatures and the `volume-surface-area` `summary.json` entry appear lazily on first practice; `analyze.py --rebuild` reconstructs `summary.json` from session history if needed. Rollback is a pure code revert — existing sessions and progress remain valid. Ship planner + priority fix + the generator + the skill wording together so the new topic actually has slots to appear in.

## Open Questions

- Exact warmup-shrink threshold for very small counts (e.g. should `--count 5` keep 2 warmups or fewer?) — resolve against the zone-scaling helper's tests.
- Whether `volume-surface-area` should later split into `volume` and `surface-area` for finer progress tracking — defaulting to combined to limit catalog growth; revisit if grading granularity matters.
