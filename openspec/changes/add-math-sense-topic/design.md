## Context

Sessions today are built entirely by `session.py:build_session_plan`, which ranks all `TEMPLATE_TOPICS` by a pure weakness/staleness/coverage score (`_topic_priority`) and fills primary + rotation zones from that ranking. `AUTO_EXCLUDED_TOPICS` already exists as a mechanism to keep a topic generatable-on-request but out of automatic rotation (currently just `prime-composite`). `arithmetic-sequences` is the existing precedent for a curriculum-grounded-but-not-Ministry-named enrichment topic, implemented as a single generator with multiple internal question shapes (`curriculum.py:655-698`).

## Goals / Non-Goals

**Goals:**
- Add `math-sense` as a template-generated topic covering three ministry-grounded reasoning shapes.
- Guarantee exactly 1 math-sense question per session, always, additive to the existing plan.
- Track math-sense performance in `summary.json` without letting it influence rotation priority.

**Non-Goals:**
- No opt-out flag or configurable slot count yet (always exactly 1, always on).
- No new CLAUDE_TOPICS / Claude-fallback path — math-sense is 100% deterministic.
- No change to how `--topics` override sessions behave for their explicitly-requested topics (math-sense is additive on top, not blended into the override cycle).

## Decisions

**One generator, three internal shapes** — mirrors `_arithmetic_sequences`. Alternative considered: three separate qtypes (`math-sense-parity`, `math-sense-estimate`, `math-sense-relational`). Rejected: multiplies bookkeeping (three TOPICS entries, three progress rows) for content that's conceptually one "flavor" the user wants sprinkled in, not tracked/ranked as distinct skills.

**Exclusion via `AUTO_EXCLUDED_TOPICS`** — reuse the existing set rather than inventing a second exclusion mechanism. `math-sense` is excluded from `_prioritized_topics` for the same structural reason `prime-composite` is (available on request, not auto-rotated) — the two differ only in that math-sense is *appended* by default while prime-composite requires explicit `--topics`. That distinction is handled by `build_session_plan` calling a separate "always append" step, not by a different exclusion set.

**Slot appended after plan construction, not woven into zones** — `build_session_plan` computes the normal plan (bootstrap or adaptive) exactly as today, then appends one `{"qtype": "math-sense", "difficulty": resolve_difficulty(...)}` entry. Alternative considered: teaching `_zone_counts` a third zone. Rejected: `_zone_counts` sums to `count` by contract (docstring says so explicitly); redefining that contract to secretly mean `count - 1` risks breaking the `--topics` override path and any other caller relying on the sum invariant. Appending post-hoc keeps `count` meaning what every other code path already assumes it means, and keeps the diff to one new line in `build_session_plan` rather than a `_zone_counts` rewrite.

**Difficulty resolution reuses `resolve_difficulty`** — math-sense's difficulty follows the same per-topic-override > global > auto-inference precedence as any topic. No special-casing.

## Risks / Trade-offs

- [Every session grows by 1 question, silently changing `--count N` semantics from "exactly N" to "N or N+1"] → Documented explicitly in the session-composition spec scenario; acceptable since it's the explicit ask (additive, not replacement) and the count only ever grows by a constant, predictable 1.
- [`_bootstrap_plan` (first-ever session, no progress) doesn't currently know about math-sense] → Append happens in `build_session_plan` after either `_bootstrap_plan` or `_adaptive_plan` returns, so both paths get it uniformly with no separate bootstrap-path change needed.
- [Three question shapes in one generator makes that function larger/harder to scan than a single-shape generator] → Same trade-off already accepted for `arithmetic-sequences`; consistent with existing style.

## Open Questions

- Should `math-sense` ever be selectable via explicit `--topics math-sense`? (Likely yes, for free — `resolve_topic_alias` already allows any direct `TOPICS` key.) Not blocking for this change; can be exercised as an incidental scenario if it falls out for free.
