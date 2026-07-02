## 1. Priority quirk fix (session.py)

- [x] 1.1 Add a unit test asserting `_topic_priority` ranks a wrong-answer topic (`correct_rate 0.0, times_practiced 1, recent last_practiced`) **≥** a never-practiced topic (empty data, baseline 0.750)
- [x] 1.2 Adjust `_topic_priority` so the weakness contribution floors/boosts low-`correct_rate` practiced topics to at least the never-practiced baseline, without introducing curriculum-hours weighting
- [x] 1.3 Verify the existing "untouched topic surfaces" behavior still holds (never-practiced still outranks well-practiced high-`correct_rate` topics)

## 2. Zone-scaling helper (session.py)

- [x] 2.1 Add a pure helper that maps `count` → per-zone counts (warmup, primary, rotation) summing exactly to `count` for **any count ≥ 1** (no 5–10 assumption; `--count` is unclamped), with warmup = `min(3, count)` shrinking first, then primary = 2 when the post-warmup remainder ≥ 4 else 1 (or 0), rest = rotation
- [x] 2.2 Unit-test the helper for the default 8, small counts (1, 2, 5), and a large count (12) — assert sums are exact and no zone is negative or oversized

## 3. Zoned planner (session.py)

- [x] 3.1 Rewrite `_adaptive_plan` to use the zone helper: 3 warmups (weak facts) + 2-deep primary on `sorted_topics[0]` + 1-each rotation across the next **distinct** topics in priority order; keep `exclude={"multiplication-table"}`
- [x] 3.2 Ensure no separate "coverage" pick is added — long-tail coverage comes from the distinct-topic spread; a default 8-question session yields ≥5 distinct topics
- [x] 3.3 Define the exhaustion fallback: repeat topics only after all distinct non-warmup topics are used
- [x] 3.4 Leave `_bootstrap_plan` (cold start) unchanged — it already emits 3 warmups + a curated 5-topic diagnostic core at medium difficulty; only add/keep a test asserting the first-session shape is unchanged
- [x] 3.5 Confirm `--topics` override path is unaffected (still all-on-specified-topics)
- [x] 3.6 Unit-test: default plan has ≥5 distinct topics, 3 warmups, 2 on the top-priority topic; `--count 5` produces exactly 5 across scaled zones

## 4. New generator — volume-surface-area (curriculum.py)

- [x] 4.1 Grep `curriculum_knowledge.md` for ח.2 scope and confirm difficulty bands stay within kita4
- [x] 4.2 Add `volume-surface-area` to `TOPICS`, define easy/medium/hard tiers (scaling cuboid dimensions), implement `_volume_surface_area` returning standard `_q(...)` with **numeric** answers and `volume:{params}` / `surface:{params}` signatures, reusing the `measurements-*` unit/phrasing style
- [x] 4.3 Register in `_GENERATORS`; unit-test that volume and surface variants and all three tiers produce valid, gradeable questions with correct answers
- [x] 4.4 Confirm `volume-surface-area` is NOT added to `NEEDS_VISUAL_TOPICS`; assert `is_quiz_renderable("volume-surface-area")` is True

## 5. Practice skill focus line (practice.md)

- [x] 5.1 Reword the one-line progress summary in `.claude/skills/practice.md` to drop the single `{main_topic}`; keep multiplication rate + weak facts, mention rotating practice across weakest topics
- [x] 5.2 Confirm `formatter.py` needs no change (groups by qtype, falls back to `TOPICS[name]`) and renders the new topic and multi-topic sessions correctly

## 6. Integration & verification

- [x] 6.1 Confirm the planner can select `volume-surface-area` into a rotation slot and `make_question` produces valid questions without invoking Claude
- [x] 6.2 Run `python generate.py` end-to-end and verify the session shows ≥5 distinct topics with the new topic reachable; verify formatter output and results grading handle the `volume:`/`surface:` signatures
- [x] 6.3 Run the full test suite; confirm no regressions and `analyze.py --rebuild` still reconstructs `summary.json`
- [x] 6.4 Validate the change: `openspec validate broaden-topic-distribution --strict`
