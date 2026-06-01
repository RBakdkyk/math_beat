## Context

Difficulty selection today (`src/session.py`):
- `build_session_plan(count, topics_override, difficulty_override)` returns a list of `{qtype, difficulty}` slots.
- `difficulty_override` is a single string applied to every slot.
- Without it, `_adaptive_plan` calls `_infer_difficulty(summary, qtype)` per topic: `rate < 0.4 → easy`, `rate > 0.8 → hard`, else `medium`.
- `_bootstrap_plan` (no progress yet) hardcodes warmup at `medium` and the rest at `easy`.

The band *definitions* these select among are change A's concern. This change adds per-topic selection control and an advanced default pitch. The full rationale for "treat Ayala as advanced" is in A's design §0.4; this design covers only its selection consequences.

## Decisions

### D1: Difficulty precedence and scope
For each question slot, difficulty resolves as: **per-topic override > global `--difficulty` > auto `_infer_difficulty`** (or the bootstrap default when no progress exists). A per-topic override for topic X does not affect topic Y, which still falls through to global/auto.

**Scope (resolved):** a per-topic override sets the tier *only when that topic is actually selected for the session* — it does **not** force the topic in. If the auto-planner doesn't pick the topic, the override is a no-op. To guarantee a topic appears, combine with `--topics` (e.g. `--topics fractions --difficulty fractions=hard`). This keeps topic-selection logic untouched and composable.

### D2: `--difficulty` argument shape
A single token with no `=` is the global value (current behavior, backward compatible). One or more `topic=level` tokens are per-topic assignments. The two forms may not be mixed in a way that's ambiguous; if both a bare value and `topic=level` tokens are given, the bare value is the global fallback and the assignments override specific topics.

- `--difficulty hard` → global hard (unchanged).
- `--difficulty fractions=hard division=easy` → fractions hard, division easy, everything else auto.
- `--difficulty medium fractions=hard` → global medium, fractions overridden to hard.

Topic tokens use the same alias map the `/practice` skill already defines (e.g. `fractions` → the three fraction subtopics).

### D3: Advanced default pitch
- `_bootstrap_plan`: non-warmup questions start at `medium` instead of `easy`. Warmup (multiplication-table) is unchanged.
- `_infer_difficulty`: thresholds shift down so an advanced student reaches harder tiers sooner. Proposed: `rate < 0.3 → easy`, `rate > 0.65 → hard`, else `medium` (was 0.4 / 0.8).
- The threshold values are tunable; the requirement is that the advanced student is pitched up relative to the prior 0.4/0.8 split.

### D4: Warmup stays weakness-targeted
The multiplication-table warmup selects weak facts regardless of the advanced pitch or any per-topic override. Overrides apply to non-warmup topics; an override naming `multiplication-table` MAY set its tier but MUST NOT disable weak-fact targeting.

### D5: argparse must change (review gap B6)
`generate.py` currently declares `--difficulty` with `choices=["easy","medium","hard"]` and a single value — which would **reject** `fractions=hard` outright. Implementation must: drop `choices=`, set `nargs="+"`, and validate tokens manually — each token is either a bare level (`easy`/`medium`/`hard`, the global fallback) or `topic=level` where `level` is valid and `topic` resolves via the `/practice` alias map. Invalid tokens raise a clear CLI error.

### D6: Thread the per-topic map through all three plan paths (review gap B7)
`build_session_plan` has three branches — `topics_override`, `_bootstrap_plan`, `_adaptive_plan` — and only `_adaptive_plan` calls `_infer_difficulty` today. The per-topic map + global fallback must be threaded into **all three**, or an override silently no-ops in bootstrap (the current cleared-state default) and `--topics` sessions. The resolution helper (`resolve_difficulty(qtype, map, global, summary)`) should be shared by all three paths.

### Standalone rationale
"Treat Ayala as advanced" (full rationale in A's design §0.4, and in project memory `ayala-advanced-student.md`): raises the pitch within grade 4, never to grade 5. This change implements the *selection* side; A implements the *content ceiling*. Duplicated here so B stands alone if A is archived first.
