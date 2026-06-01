## 0. Dependency

- [x] 0.1 Land change A (`define-per-topic-difficulty-levels`) first — these controls select among the bands A defines

## 1. Manual per-topic difficulty override

- [x] 1.1 `generate.py`: **drop `choices=` and set `nargs="+"`** on `--difficulty` (the current single-value+choices config rejects `topic=level`); parse tokens into a `{topic: level}` map + optional bare global fallback; validate each token (level ∈ {easy,medium,hard}; topic resolves via alias map) with a clear error on garbage
- [x] 1.2 `src/session.py`: add a shared `resolve_difficulty(qtype, map, global, summary)` helper and thread the map+global through **all three** `build_session_plan` paths — `topics_override`, `_bootstrap_plan`, `_adaptive_plan` (only `_adaptive_plan` calls `_infer_difficulty` today). Precedence: per-topic > global > auto. Override applies only when the topic is selected (does NOT force inclusion)
- [x] 1.3 Apply the topic alias map (same as `/practice`) when matching override keys to subtopic qtypes (e.g. `fractions` → the three fraction subtopics)

## 2. Advanced selection-skew (session.py)

- [x] 2.1 `_bootstrap_plan`: start non-warmup questions at `medium`, not `easy`
- [x] 2.2 `_infer_difficulty`: shift thresholds down (proposed easy < 0.3, hard > 0.65) so harder tiers are reached sooner
- [x] 2.3 Confirm warmup stays weakness-targeted and is unaffected by the pitch/override

## 3. Skill arg mapping

- [x] 3.1 `.claude/skills/practice.md` + `.claude/commands/practice.md` (both, kept in sync): document and parse per-topic difficulty syntax (`topic=level`), passing it through to `generate.py --difficulty`; keep positional difficulty as global

## 4. Validation

- [x] 4.0 Add `tests/test_selection.py` (stdlib, run via `python tests/test_selection.py`) — separate from A's `tests/test_bands.py`
- [x] 4.1 Assert precedence: per-topic override beats global, global beats auto, auto applies where neither is set; assert override no-ops when its topic isn't selected (and works when forced via `--topics`)
- [x] 4.2 Assert bootstrap yields `medium` non-warmup slots and `_infer_difficulty(0.7)` → `hard`; assert override is honored in the bootstrap and `--topics` paths (not just adaptive)
- [x] 4.3 Assert a `multiplication-table=hard` override still targets weak facts
- [x] 4.4 Assert invalid `--difficulty` tokens (`fractions=banana`, unknown topic) raise a clear CLI error
