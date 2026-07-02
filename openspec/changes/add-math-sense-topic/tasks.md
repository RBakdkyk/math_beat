## 1. Curriculum: math-sense generator

- [x] 1.1 Add `math-sense` entry to `TOPICS` in `src/curriculum.py`
- [x] 1.2 Implement `_math_sense(difficulty)` generator with three internal shapes: relational fill-in, parity-without-computing, estimate-and-judge (mirror `_arithmetic_sequences`'s multi-shape structure and per-shape signature convention)
- [x] 1.3 Register `_math_sense` in `_GENERATORS`
- [x] 1.4 Add a `ponytail:`-style inline comment noting the ministry grounding (curriculum_knowledge.md line refs), matching the `arithmetic-sequences` precedent

## 2. Session composition: exclusion + always-append slot

- [x] 2.1 Add `math-sense` to `AUTO_EXCLUDED_TOPICS` in `src/session.py` so it never enters `_prioritized_topics`
- [x] 2.2 In `build_session_plan`, after the normal plan (topics_override / bootstrap / adaptive path) is built, append exactly one `{"qtype": "math-sense", "difficulty": resolve_difficulty("math-sense", difficulty_map, difficulty_override, summary)}` entry
- [x] 2.3 Verify the append happens for all three plan paths (override, bootstrap, adaptive) with a single code path, not duplicated per-branch

## 3. Verification

- [x] 3.1 Run `python generate.py --count 8` and confirm the session has 9 questions, with 1 tagged `math-sense`
- [x] 3.2 Run `python generate.py --topics fractions --count 5` and confirm 6 total questions (5 fractions + 1 math-sense)
- [x] 3.3 Manually record results including the math-sense question via `/results`, run `python analyze.py`, and confirm `summary.json.topics.math-sense` populates with `correct_rate`/`times_practiced`/`last_practiced`
- [x] 3.4 Confirm math-sense never appears as a primary/rotation-selected topic even when its correct_rate is artificially set low in `summary.json` (rotation exclusion holds)
