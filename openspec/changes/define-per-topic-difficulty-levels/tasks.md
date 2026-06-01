## 0. Decisions (resolved 2026-06-01 — see design.md §0)

- [x] 0.1 Keep **exactly 3** levels (easy/medium/hard); fix definitions, don't add levels
- [x] 0.2 Addition/subtraction `hard`: **keep 4-digit by-hand** (L208); drop the calculator-tier framing — no magnitude change for #2/#3
- [x] 0.3 `arithmetic-sequences`: **keep + ground + document**; constrain steps to 2–10; topic key unchanged
- [x] 0.4 Treat Ayala as **advanced** (content side): `hard` = advanced-class grade-4 tier, never grade 5; reverses 1.1. (Selection-skew side → change B.)
- [x] 0.5 Fraction answers: **expect unreduced, accept both** (reduction is grade 5) — adds §8

## 1. 🔴 Fix out-of-scope bands (curriculum.py)

- [x] 1.1 `_multiplication` hard: **keep 2×3-digit** (advanced gr-4 per §0.4) — current ladder (easy 1×2, medium 2×2, hard 2×3) already matches; verify no tier exceeds grade-4 magnitude
- [x] 1.2 `_fraction_comparison` hard: remove unrelated-denominator pairs and denominator 7; restrict to familiar set {2,3,4,5,6,8,10}; implement harder *intuitive* hard strategies (related-denominator renaming, proximity to ½/1, same-numerator) — never the cross-multiply algorithm

## 2. ⬇️ Add missing in-scope bands (curriculum.py)

- [x] 2.1 `_division`: add a whole-tens-divisor band (÷10, ÷20, ÷30 …) with in-range dividends; surface remainder at medium (not only hard)
- [x] 2.2 `_order_of_ops`: include `÷` at **medium and hard only** (easy stays `×`-only); enforce invariants — every `÷` exactly divisible, every result a non-negative integer
- [x] 2.3 Add signatures/answer_types for new shapes per design "Implementation specifics" (whole-tens `div:840÷20`; see §3/§4 for fraction & exponent shapes)

## 3. 🔵 Strengthen weak differentiation (curriculum.py)

- [x] 3.1 `_fraction_addition`: make hard genuinely harder than medium (related-denom + mixed-number results / missing-addend `frac-add-missing:?+1/4=3/4`), intuitive-only; ensure hard ⊄ medium
- [x] 3.2 `_fraction_subtraction`: same treatment (whole/mixed − fraction, missing-number); ensure tier distinctness
- [x] 3.3 Revisit `_DENOM_PAIRS` so easy/medium/hard are provably distinct sets
- [x] 3.4 Compute fraction answers **unreduced** (target denominator), not via `Fraction`'s reduced form — applies to all fraction generators (§8)
- [x] 3.5 Add a non-reducing `(num, denom)` formatter (or change `_frac_str` to take the pair); `_frac_str(Frac)` cannot represent unreduced values. Store whole results unreduced (`6/6`, not `1`)

## 4. 🟡 Trim minor over-reach (curriculum.py)

- [x] 4.1 `_addition` / `_subtraction` hard: **no change** per §0.2 (4-digit by-hand retained, calculator-tier framing dropped) — verify hard never exceeds 4 digits
- [x] 4.2 `_multiplication_by_tens`: scope to whole tens & hundreds (drop ×1000)
- [x] 4.3 `_exponents` hard: keep within introductory intent (exp ≤ 3, drop 10^4); add "write N as a power" — N constrained to **unique** prime-power (`8=2³`, `25=5²`; exclude `16/64/81`) — and "is a^b = b^a?" including the `2^4 vs 4^2` equality case sometimes (not always "לא"). Categorical answer_types per design table
- [x] 4.4 `_divisibility`: drop divisor 2 (taught rules are 3/6/9); keep 3 at easy

## 5. ⚪ Topic grounding

- [x] 5.1 `arithmetic-sequences`: constrain step sizes to 2–10 (so sequences rehearse table facts) per §0.3
- [x] 5.2 Document `arithmetic-sequences` grounding: note it as number-sense/skip-counting enrichment tied to curriculum strand ד.4 (L323–332, L763) — add a cross-reference comment/section so the curriculum-alignment invariant holds

## 8. Fraction non-reduction (curriculum.py + /results)

- [x] 8.1 (curriculum.py) covered by 3.4 — answers kept in the grade-4-natural denominator
- [x] 8.2 (/results) update answer matching to accept BOTH the stored unreduced form and any equivalent (incl. reduced) form for fractions; keep `.claude/skills/results.md` and `.claude/commands/results.md` in sync

## 6. Validation

- [x] 6.1 Add `tests/test_bands.py` (stdlib, run via `python tests/test_bands.py`) calling `make_question()` **directly** (not via `_generate_template_question`, which swallows exceptions); for every subtopic generate N samples/tier and assert each tier's parameter space ⊄ the tier below
- [x] 6.2 Curriculum-bound assertions: mult factor ≤ 2×3-digit; add/sub ≤ 4-digit; division divisor ∈ {1–9} ∪ whole-tens; fraction denominators ∈ {2,3,4,5,6,8,10}; fraction-comparison pairs equal-denom / equal-numerator / related-denom only; exponent exp ≤ 3; mult-by-tens has no thousands; order-of-ops results non-negative integers with exact ÷
- [x] 6.3 Assert fraction answers are unreduced (e.g. `1/4+1/4` → `"2/4"`)
- [x] 6.4 Spot-check generated samples for each fixed topic against the cited curriculum lines in design.md
