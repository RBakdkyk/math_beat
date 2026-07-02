## Why

Ayala's sessions are entirely computation-driven — every question drills a curriculum subtopic ranked by weakness. The Ministry curriculum also calls out number-sense/reasoning skills (estimation, parity-without-computing, relational fill-in) as first-class content (`curriculum_knowledge.md` lines 300-332, 845), distinct from raw computation. There's no topic that exercises this "math sense" muscle today, and it shouldn't compete with weakness-driven drill for a slot — it should show up every session regardless of performance elsewhere.

## What Changes

- Add a new `math-sense` qtype: a single template generator (mirrors the `arithmetic-sequences` precedent — one generator, multiple internal question-shapes) covering three ministry-grounded shapes: relational fill-in, parity-without-computing, and estimate-and-judge.
- Add `math-sense` to `TOPICS` and `_GENERATORS` in `curriculum.py`.
- Exclude `math-sense` from priority-based rotation (`_prioritized_topics`/`_topic_priority`) — it never competes on weakness/staleness/coverage.
- `build_session_plan` always appends exactly 1 `math-sense` question on top of the normally computed plan — additive, not a replacement of an existing slot. Session size becomes `count + 1`.
- `math-sense` results still flow through the normal results/progress pipeline into `summary.json` under `topics.math-sense`, for visibility — just never read by the priority ranking.

## Capabilities

### New Capabilities
(none — this extends existing capabilities rather than introducing a new domain)

### Modified Capabilities
- `curriculum-model`: new topic tree entry (`math-sense`) with three internal question-shape rules, following the same rule-based (not enumerated) generation approach as other topics.
- `question-generation`: new deterministic template generator for `math-sense`, added to the no-Claude-needed set.
- `session-composition`: session plans now always include exactly 1 additional `math-sense` slot appended after the normal weakness-ranked plan is built; total question count becomes `count + 1`.
- `progress-tracking`: `math-sense` accumulates `correct_rate`/`times_practiced`/`last_practiced` like any topic, but is explicitly excluded from the topic-priority calculation used for rotation.

## Impact

- `src/curriculum.py`: new `_math_sense` generator function, `TOPICS` entry, `_GENERATORS` entry.
- `src/session.py`: `AUTO_EXCLUDED_TOPICS` (or a new exclusion set) gains `math-sense`; `build_session_plan` appends the extra slot.
- `src/progress.py`: no code change expected — existing generic per-topic merge logic already handles any qtype found in `generated.json`/`results.json`.
- `wiki/progress/summary.json`: gains a `topics.math-sense` entry after the first session that includes it.
- No changes to `generator.py`, `formatter.py`, or the Claude-fallback path — `math-sense` is template-only, no Claude CLI involvement.
