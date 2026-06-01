## Why

The easy/medium/hard bands inside each generator in `src/curriculum.py` were chosen by feel, not validated against `src/curriculum_knowledge.md`. An audit of all 18 template generators (captured in `design.md`) found that "hard" drifts in three uncontrolled directions:

1. **Past the grade-4 ceiling** — e.g. multiplication hard generates `2-digit × 3-digit`, which the curriculum flags as *advanced-classes-only* (L227, L841); fraction-comparison hard forces a *forbidden* common-denominator algorithm (L64, L132).
2. **Not far enough to be distinct** — fraction-addition/subtraction `hard` is a strict subset of `medium`, so the level does nothing.
3. **Missing in-scope content entirely** — division never generates whole-tens divisors (L255, L794); order-of-operations never uses `÷` (L380).

Because difficulty is selected per-topic (`_infer_difficulty` in `src/session.py`) and can be forced per-session, these undefined bands directly produce questions that are either out-of-level or falsely "harder." This change pins each topic's three levels to the curriculum so that easy→hard always stays within grade 4.

Ayala is treated as an **advanced student** (parent directive). So `hard` is defined as the curriculum's **advanced-class (כיתות מתקדמות)** grade-4 tier — embraced, not avoided — with one hard limit: advanced means *grade 4*, never grade 5. This is why `_multiplication` hard keeps 2×3-digit (advanced grade-4, L227/L841), while `_fraction_comparison` hard still cannot use the cross-multiply algorithm (grade 5 for everyone, L132).

## What Changes

- Define, per topic, what easy/medium/hard **mean** as curriculum-validated number-range + rule constraints, with `hard` = the advanced-class grade-4 tier (never grade 5).
- **Multiplication (was 🔴, now resolved):** keep `_multiplication` hard at `2-digit × 3-digit` — it is the advanced grade-4 task (L227/L841), appropriate for an advanced student. Ladder: easy = 1×2-digit, medium = 2×2-digit, hard = 2×3-digit.
- **Fix 🔴 out-of-scope band:**
  - `_fraction_comparison` hard: unrelated denominators (forces the grade-5 algorithm; uses denom 7) → harder *intuitive* strategies (related-denominator renaming, proximity to ½/1, same-numerator) within the familiar denominator set `{2,3,4,5,6,8,10}`. Advanced does not unlock the algorithm.
- **Fix ⬇️ missing in-scope bands:**
  - `_division`: add whole-tens divisors (÷10, ÷20, ÷30 …) as a valid band; surface remainder at medium, not only hard.
  - `_order_of_ops`: include `÷` in generated expressions.
- **Fix 🔵 weak differentiation:**
  - `_fraction_addition` / `_fraction_subtraction`: make hard genuinely harder (related-denominator + mixed-number results / missing-addend), still intuitive-only.
- **Fix 🟡 minor over-reach:**
  - `_multiplication_by_tens`: scope to tens & hundreds (drop ×1000) per L223.
  - `_exponents` hard: keep within the introductory intent (small bases/exponents); optionally add inverse/`2^5 vs 5^2` variety per L474.
  - `_divisibility`: drop divisor `2` (the taught rules are 3/6/9, L441–443).
  - `_addition` / `_subtraction` hard: **no magnitude change** — 4-digit column arithmetic is an endorsed grade-4 by-hand task (L208), and this app has no calculator in its loop. Remove the "calculator-tier" framing the audit floated; keep `hard` at 4-digit (current `1000–9999`), never beyond.
- **Resolve ⚪ topic grounding:**
  - `arithmetic-sequences` — **keep**, but ground it: document as number-sense / skip-counting enrichment tied to curriculum strand ד.4 (L323–332, L763), and constrain steps to 2–10 so the sequences rehearse times-table facts. (Topic name/signature key unchanged to avoid churn.)
- **Fix fraction non-reduction bug (§0.5):** compute/store fraction answers **unreduced** (grade-4-natural denominator; reduction is grade 5, L134), and make `/results` accept both unreduced and reduced forms as correct.

> **Split note:** This is change **A** of a two-part split. The advanced *content ceiling* (hard = advanced grade-4, e.g. multiplication 2×3-digit) lives here. The *selection* side of "treat Ayala as advanced" — manual per-topic difficulty override and the bootstrap/threshold skew — is change **B** `add-difficulty-selection-controls`, which depends on A.

## Capabilities

### Modified Capabilities

- `curriculum-model`: difficulty tiers gain an explicit grade-4-ceiling guarantee, per-topic level definitions validated against `curriculum_knowledge.md`, and unreduced fraction answers.
- `results-skill`: fraction answer matching accepts both unreduced and reduced forms.

## Impact

- `src/curriculum.py` — difficulty branches in the affected generators (#5,6,8,9,10,11,14,16,17); `_DENOM_PAIRS`; new whole-tens divisor pool; new shapes (missing-addend, exponent inverse/commutativity) with new signatures/answer_types (see design "Implementation specifics"); unreduced fraction answer computation. (#2,3,4 are verify-only.)
- `/results` skill (`.claude/skills/results.md` + `.claude/commands/results.md`) — accept reduced & unreduced fraction answers; keep both files in sync.
- `tests/test_bands.py` — new stdlib assert script for the cross-cutting invariants.
- `src/curriculum_knowledge.md` — read-only reference; cited, not modified.
- No data migration: existing `wiki/sessions/*` are read-only history.
- Out of scope (this change): manual per-topic override and advanced selection-skew (→ change B); persistent per-topic "level ladder", weakness-aware param selection, measurements "without formulas" framing (see design).
