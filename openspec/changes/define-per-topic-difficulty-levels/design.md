## Context

`src/curriculum.py` defines 18 template-based generators (plus 4 Claude-only topics). Each generator already branches on `easy`/`medium`/`hard`, and `src/session.py:_infer_difficulty` already selects a difficulty per topic from that topic's `correct_rate`. So per-topic difficulty selection exists today — but the **bands themselves were never validated against the curriculum**. This document captures a full audit of all 18 generators against `src/curriculum_knowledge.md` (the authoritative kita4 extract, 855 lines), and the rule we adopt for defining the three levels.

All line references (`L###`) below point into `src/curriculum_knowledge.md`.

## The definition rule

The curriculum distinguishes **"all students"** tasks from **"advanced classes" (כיתות מתקדמות)** tasks (L841). We anchor the three levels to that native tiering, so the grade-4 ceiling is guaranteed by construction. Because Ayala is treated as an **advanced student** (§0.4), `hard` fully embraces the advanced-class grade-4 tier:

```
easy   = entry / competency-floor task for the topic
medium = the standard "all students" grade-4 task
hard   = the advanced-class (כיתות מתקדמות) grade-4 task — embraced,
         e.g. 3-digit-factor multiplication, fraction-as-quotient
         — but NEVER a grade-5 method (no fraction reduction/expansion
           algorithm, no unrelated-denominator comparison, no
           fraction×fraction or fraction÷fraction)
```

`hard` is the hardest *4th-grade* task — including the advanced track — but never a 5th-grade task. The advanced/grade-4 line, not the all-students/advanced line, is the guarantee this change enforces.

## Audit results — all 18 template generators

| # | Generator | easy | med | hard | Verdict |
|---|---|---|---|---|---|
| 1 | multiplication-table | ✅ | ✅ | ✅ | Clean — facts are gr-3 mastery, full table fine |
| 2 | addition | ✅ | ✅ | ✅ | Resolved: 4-digit is endorsed by-hand (L208) — see §0.2 |
| 3 | subtraction | ✅ | ✅ | ✅ | Resolved: same as addition — see §0.2 |
| 4 | multiplication | ✅ | ✅ | ✅ | Resolved: 2×3-digit hard is advanced gr-4, OK for advanced student — see §0.4 |
| 5 | division | ⬇️ | ⬇️ | ✅ | Whole-tens divisors never generated |
| 6 | order-of-operations | ⬇️ | ⬇️ | ⬇️ | Division never appears in expressions |
| 7 | prime-composite | ✅ | ✅ | ✅ | Clean — range to 100 matches exactly |
| 8 | divisibility | 🟡 | 🟡 | ✅ | Divisor `2` is off-spec (rules are 3/6/9) |
| 9 | fraction-comparison | ✅ | 🟡 | 🔴 | Hard forces forbidden algorithm |
| 10 | fraction-addition | ✅ | ✅ | 🔵 | Scope-clean; hard ⊂ medium (no real step-up) |
| 11 | fraction-subtraction | ✅ | ✅ | 🔵 | Same — weak differentiation |
| 12 | measurements-area | ✅ | ✅ | ✅ | Clean (framing note below) |
| 13 | measurements-perimeter | ✅ | ✅ | ✅ | Clean (framing note below) |
| 14 | exponents | ✅ | ✅ | 🟡 | Hard (10⁴, 5⁴) past introductory intent |
| 15 | natural-numbers | ✅ | ✅ | ✅ | Clean — to 999,999 ⊂ one million |
| 16 | arithmetic-sequences | ⚪ | ⚪ | ⚪ | Not a named kita4 topic |
| 17 | multiplication-by-tens | 🟡 | ✅ | 🟡 | Includes ×1000 (spec: tens & hundreds) |
| 18 | equations-unknown | ✅ | ✅ | ✅ | Clean — missing-number is in-scope |

Legend: ✅ aligned · 🔴 out of grade-4 scope · ⬇️ in-scope band missing · 🟡 minor over-reach · 🔵 weak differentiation · ⚪ topic-grounding question.

### 🔴 Out of grade-4 scope (forces a forbidden or advanced-only path)

**#4 `_multiplication` hard — RESOLVED, not a violation (§0.4).** Hard generates `2-digit × 3-digit` (10–99 × 100–999). The audit flagged this because 3-digit-factor multiplication is **advanced-only** (L227, L841) — but Ayala is treated as an advanced student, and this is exactly the advanced grade-4 task (still grade 4, not grade 5). **Keep 2×3-digit hard.** Ladder: easy = 1×2-digit, medium = standard 2×2-digit (L226), hard = 2×3-digit (advanced).

**#9 `_fraction_comparison` hard — forbidden algorithm (still 🔴; advanced does NOT rescue it).** Being advanced raises the ceiling within grade 4, but the cross-multiply / common-denominator algorithm is **grade 5 for everyone** (L132, L776) — not an advanced grade-4 task. Hard picks two **unrelated** denominators from `{3,4,5,6,7,8}` (e.g. `2/3` vs `3/7`), which can only be compared via a common-denominator/cross-multiply **algorithm** — explicitly prohibited in grade 4 (L64, L132, L777). Mastery restricts comparison to equal numerators or equal denominators (L718). Also uses denominator **7**, outside the familiar set `{2,3,4,5,6,8,10}` (L136, L772–773). Fix (advanced-but-intuitive): hard uses harder *intuitive* strategies only — related-denominator renaming (e.g. `2/3` vs `3/6` → recognize `2/3 = 4/6`), proximity to ½/1 (L68–69), same-numerator (`1/7` vs `1/9`, L76) — within familiar denominators. Never an unrelated-denominator pair that forces the algorithm.

### ⬇️ In-scope content never generated (missing bands)

**#5 `_division`.** All bands use single-digit divisors only (2–9). Scope is **single-digit OR whole tens** (L255, L278, L794), worked example `840 ÷ 20` (L286). The whole-tens band — a natural "harder" tier — is missing. Remainder appears only at hard, though mastery treats "up to 100 including with remainder" as core (L728).

**#6 `_order_of_ops`.** Composes only `+ − ×`. Flagship curriculum examples include `÷`: `47 × 5 − 63 ÷ 3` (L380), `5,200 × 100 ÷ 10` (L381). The ÷-before-+ rule (L813–814) is never exercised.

### 🟡 Minor over-reach (in scope to teach, past the by-hand mastery band)

- **#2/#3 addition/subtraction hard = 4-digit.** ~~Audit's initial read: past the 1,000 by-hand mastery cap (L727, L837).~~ **Resolved (§0.2): acceptable, no change.** Column add/sub of 4–5 digit numbers is an *explicit* grade-4 task (L208); the 1,000 figure is a mastery *floor*, and the "calculator above 1,000" note (L837) concerns incidental large numbers in word problems, not deliberate column-arithmetic practice. This app has no calculator in its loop, and `hard` is only selected at >80% accuracy. Keep at 4-digit; the audit's "calculator-tier" framing is dropped.
- **#17 multiplication-by-tens includes ×1000.** Spec names **whole tens and whole hundreds** only (L223, L759).
- **#14 exponents hard does 10⁴, 5⁴.** A 3-hour introductory *notation* topic; examples are tiny (`2³`, L473). Heavy computation exceeds intent. Signature tasks "write 8 as a power of 2" and "is 2⁵ = 5²?" (L474–475) are never generated.
- **#8 divisibility uses divisor 2.** The taught rules are **3, 6, 9** (L441–443); divisibility-by-2 is prior knowledge, not a rule in this subtopic. Hard (3/6/9 only) is the most aligned band.

### 🔵 Weak differentiation (undermines the 3-level goal)

**#10/#11 fraction add/sub.** In `_DENOM_PAIRS` (curriculum.py:284), `hard` is a strict **subset** of `medium` — same denominators, same operation, so "hard" isn't harder. Grade-4-valid levers for real differentiation: equal-denom (easy) → related-denom (medium) → related-denom with **mixed-number results / missing-addend** (hard), all intuitive-only (L102–107).

### ⚪ Topic grounding

**#16 arithmetic-sequences is not a kita4 topic.** None of the 8 official topics (L11–20) is "sequences." Skip-counting content is harmless and supports number sense ("first-class," L829) and the times tables, but the topic is *invented* with no citation. Decision needed: keep as documented number-sense enrichment, or remove.

### Framing note (non-blocking)

`measurements-area` / `-perimeter` compute the formulas cleanly and in-range, but the curriculum insists these be done **"without formulas," from the unit-square meaning** (L652, L748). Presenting `"L × W ="` as formula-plugging is in mild tension with that pedagogy. Not a band/scope bug — recorded for completeness.

## Decisions

### D1: Anchor levels to the curriculum's "all students" vs "advanced classes" tiering
See the definition rule above. This makes the grade-4 ceiling structural rather than a per-generator judgement call.

### D2: Fix scope violations by changing the band, not by removing difficulty
🔴 topics keep three levels; only the out-of-scope band is replaced with a curriculum-true harder variant (hardest 2×2 for multiplication; intuitive strategies for fraction-comparison).

### D3: Scope this change to band *definitions* only
The persistent, ratcheting per-topic "level ladder" (a stored level in `summary.json` that promotes/demotes over time) is a separate, behavioral change. It must be built on top of well-defined bands, so it is explicitly deferred. This change does not touch `_infer_difficulty`'s logic.

### D4: arithmetic-sequences — KEEP and ground (resolved, see §0.3 below)

## Resolved decisions (2026-06-01)

### §0.1 — Exactly 3 levels. **Resolved: keep 3.**
The audit's findings were definition/overlap bugs, not resolution shortfalls — fixing the definitions gives ample range for one student. Three levels map 1:1 onto the curriculum's own floor / all-students / advanced tiering (L841). Adding a 4th level would churn `generate.py` argparse choices, `_infer_difficulty` thresholds (session.py), the skill docs, and the implicit 3-way assumption in progress tracking, for marginal gain.

### §0.2 — Addition/subtraction `hard`. **Resolved: keep 4-digit by-hand; no calculator tier.**
Column add/sub of 4–5 digit numbers is an explicit grade-4 task (L208). The 1,000 competency figure (L727) is a mastery floor; the "calculator above 1,000" note (L837) concerns incidental large numbers in word problems, not arithmetic practice. This app has no calculator in its loop, and `hard` is only selected at >80% accuracy. Keep `hard` at 4-digit (`1000–9999`), never beyond 4 digits. The audit's "calculator-tier" idea is dropped; no code change needed for #2/#3.

### §0.3 — arithmetic-sequences. **Resolved: keep, ground, and document.**
Skip-counting by 6/7/8 rehearses the exact multiplication facts this app exists to strengthen, and supports the curriculum's first-class number-sense strand ד.4 (L323–332, L763). Keep the generator but: (a) constrain step sizes to 2–10 so sequences rehearse table facts; (b) document the grounding (number-sense/skip-counting enrichment tied to ד.4) so the "everything aligns to curriculum_knowledge.md" invariant holds. Topic name and signature key unchanged to avoid churn.

### §0.4 — Treat Ayala as an advanced student. **Resolved: yes (parent directive, 2026-06-01).**
`hard` embraces the curriculum's **advanced-class (כיתות מתקדמות)** grade-4 tier — never grade 5. Consequences:
- **Reverses the multiplication fix:** `_multiplication` hard keeps 2×3-digit (advanced grade-4, L227/L841); it is no longer a 🔴 violation. (Was §1.1.)
- **Does NOT rescue fraction-comparison:** the cross-multiply algorithm is grade 5 for everyone (L132); hard stays intuitive-only.
- **Advanced-only content now permissible** where useful: fraction-as-quotient (L38), algebraic notation of properties (L412) — available, not mandated.
- **Selection skews up → moved to change B.** The bootstrap-at-medium and `_infer_difficulty` threshold shift are the *selection* side of "advanced"; they're implemented in `add-difficulty-selection-controls` (change B). This change (A) owns only the *content ceiling*.
- **Compatible with the app's premise:** advanced overall, but the multiplication-table warmup remains her remediation focus (it targets weak facts regardless of pitch).

### §0.5 — Fraction answers and grade-4 non-reduction. **Resolved: expect unreduced, accept both.**
Python's `Fraction` auto-reduces (`Frac(1,4)+Frac(1,4) → 1/2`, `Frac(2,6) → 1/3`), but reduction is a **grade-5** skill (L134, L776). So `_fraction_addition`/`_fraction_subtraction` currently expect `"1/2"` where a correct grade-4 answer is `"2/4"` — marking right answers wrong.
- **Generation:** compute the answer **keeping the grade-4-natural denominator** (the common/related denominator actually used), not `Fraction`'s reduced form. Equal-denom: keep that denom (`2/4`, `6/6→"6/6"` or `"1"`). Related-denom: express in the larger denominator. Mixed-number results still allowed via `_frac_str`, but built on the unreduced fraction.
- **Matching (`/results`):** accept **both** the unreduced (expected) and any equivalent reduced form as correct — a child who does reduce is not punished.
- **Cross-capability:** this touches `results-skill` (answer matching), not just `curriculum-model`.

### §0.6 — Manual per-topic difficulty. **Resolved: add manual override → change B.**
Today `--difficulty` is a single global value; auto per-topic difficulty comes only from `_infer_difficulty`. Add the ability to pin difficulty **per topic** in one session, e.g. `fractions=hard division=easy`, alongside the existing global flag and auto-adaptation. Precedence: **per-topic override > global `--difficulty` > auto `_infer_difficulty`**. Touches `generate.py`, `session.py`, `practice.md` (`session-composition` + `practice-skill`). **Implemented in change B** (`add-difficulty-selection-controls`); recorded here because it emerged from this exploration.

## Concrete band definitions (implementation spec)

Target state for every template generator's three tiers. Each tier is a parameter rule (range + constraint), distinct from the tier below, bounded by advanced grade-4. `Δ` flags whether code changes. All fraction work is intuitive-only; fraction denominators ∈ familiar set **F = {2, 3, 4, 5, 6, 8, 10}**.

### Topics that CHANGE

**#9 fraction-comparison** (Δ rewrite hard+medium) — intuitive strategies only, never the cross-multiply algorithm. Denominators ∈ F.

| Tier | Rule | Strategy / cite |
|---|---|---|
| easy | equal denominators `d∈F`; numerators `a≠b<d` | bigger numerator wins (L718) |
| medium | **equal numerators**, different denominators `d1,d2∈F` | smaller denominator = bigger piece (`1/7` vs `1/9`, L76) |
| hard | **related** denominators (`d2 % d1 == 0`), ≥1 non-unit numerator | requires equivalent-name renaming, e.g. `2/3` vs `3/6` → `4/6` vs `3/6` (L57–61) |

Removes: unrelated-denominator pairs and denominator 7. Answer stays the larger fraction string or `"שווים"`.

**#10 fraction-addition** (Δ rewrite hard; redo `_DENOM_PAIRS`) — intuitive, denoms ∈ F.

| Tier | Rule | Cite |
|---|---|---|
| easy | equal denominators `d∈F`; result ≤ 1 (proper) | L93, L778 |
| medium | related denominators (`d2 % d1 == 0`); proper result | L96, L780 |
| hard | related denominators, **improper → mixed-number result** OR **missing-addend** (`□ + 1/4 = 3/4`, `1 + □ = 1½`) | L102–107, L782 |

**#11 fraction-subtraction** (Δ rewrite hard) — mirror of addition; result ≥ 0.

| Tier | Rule | Cite |
|---|---|---|
| easy | equal denominators `d∈F`; proper, result ≥ 0 | L94, L779 |
| medium | related denominators; result ≥ 0 | L781 |
| hard | **whole/mixed minus fraction** (`1 − 1/3`, `2 − 3/4`, `1½ − 2/3`) OR **missing-number** (`□ − 1/4 = 3/4`) | L121–123 |

**#5 division** (Δ add whole-tens divisor + remainder at medium) — divisor ∈ {1–9} ∪ {10,20,…,90}; dividend ≤ ~999.

| Tier | Rule | Cite |
|---|---|---|
| easy | divisor 2–9, **exact** (no remainder), dividend ≤ 90, quotient 2–10 | L797 |
| medium | divisor 2–9, dividend ≤ ~500, **mix exact + remainder** | L256, L801 |
| hard | **whole-tens divisor** (10–90) e.g. `840 ÷ 20`, and/or single-digit with remainder, dividend ≤ ~900 | L255, L278, L286 |

Signature gains whole-tens form (e.g. `div:840÷20`). Remainder answer format unchanged (`"{q} שארית {r}"`).

**#6 order-of-operations** (Δ introduce ÷) — `÷` must produce integer operands (divisible).

| Tier | Rule | Cite |
|---|---|---|
| easy | two ops, `×` only (no `÷`), no brackets, small (`a + b×c`, `a − b×c`) | L371 |
| medium | brackets OR **`÷`-before-`+`** (`(a−b)×c`, `a + b÷c`) — `÷` first enters here | L380 |
| hard | nested/3-op with brackets and `÷`, larger (`47×5 − 63÷3`, `(a+b)×c − d÷e`) | L380, L816 |

**#14 exponents** (Δ trim magnitude; add variety) — keep introductory; exp ≤ 3.

| Tier | Rule | Cite |
|---|---|---|
| easy | forward compute, base `{2,3}`, exp `{2,3}` | L463, L473 |
| medium | forward compute, base `{2,3,4,5}`, exp `{2,3}` | L463 |
| hard | base `{2,3,4,5,10}` exp `{2,3}` **plus** inverse (`write 81 as a power`) and commutativity-check (`is 2^5 = 5^2?`) variety | L468, L474–475 |

Removes: exp=4 / large bases (no `10^4`). Hard's lift is conceptual (inverse + commutativity), not magnitude.

**#17 multiplication-by-tens** (Δ drop ×1000) — multiplier ∈ whole tens or whole hundreds only.

| Tier | Rule | Cite |
|---|---|---|
| easy | 1-digit (2–9) × `{10, 100}` | L223 |
| medium | 1–2-digit (2–99) × `{10,20,…,90, 100,200,300}` | L223, L759 |
| hard | 2-digit (12–99) × whole hundreds `{100,200,…,900}` | L237 |

Removes: ×1000 from all tiers.

**#8 divisibility** (Δ drop divisor 2) — taught rules are 3/6/9.

| Tier | Rule | Cite |
|---|---|---|
| easy | divisor `{3}`, n ∈ 10–60 | L441 |
| medium | divisor `{3,6,9}`, n ∈ 20–200 | L441–443 |
| hard | divisor `{3,6,9}`, n ∈ 100–999 | L443, L447 |

**#16 arithmetic-sequences** (Δ constrain step to 2–10) — number-sense enrichment grounded in ד.4.

| Tier | Rule | Cite |
|---|---|---|
| easy | start 1–20, **step 2–10**, length 5, find-next | L327 (number sense) |
| medium | start 1–50, **step 2–10**, length 5, find-next / find-missing-middle | L329, L763 |
| hard | start 10–100, **step 2–10**, length 6, find-rule / find-missing | L763 |

Removes: steps 15/20/25/50/100. Steps 2–10 make every sequence a skip-count of a table fact.

### Topics that DO NOT change (confirmed valid)

| # | Topic | easy | medium | hard | Note |
|---|---|---|---|---|---|
| 1 | multiplication-table | a,b≤5 | a≤8 | full 1–10 | gr-3 facts; warmup is weakness-targeted |
| 2 | addition | 2-digit + 2-digit | 3-digit + 3-digit | 4-digit + 4-digit | by-hand, ≤4-digit (§0.2, L208) |
| 3 | subtraction | 2-digit | 3-digit | 4-digit | mirror; `a > b` enforced |
| 4 | multiplication | 1-digit × 2-digit | 2-digit × 2-digit | **2-digit × 3-digit** | advanced gr-4 (§0.4, L227) — verify only |
| 7 | prime-composite | 2–20 | 2–50 | 2–100 | range matches L426; excludes 1 |
| 15 | natural-numbers | 4-digit | 5-digit | 6-digit (≤999,999) | ⊂ one million (L149) |
| 18 | equations-unknown | small | mid (≤200) | ≤500 | missing-number in scope (L102, L203) |
| 12 | measurements-area | 2–9 × 2–9 | 5–20 × 2–9 | 10–50 × 10–50 | in-range; "without formulas" framing noted only |
| 13 | measurements-perimeter | 2–9 | 5–20 × 2–9 | 15–50 × 15–50 | same framing note |

### Cross-cutting invariants (validation §6)

- Fraction denominators ∈ F for every fraction topic, every tier.
- Fraction comparison pairs are equal-denom, equal-numerator, or related-denom — never unrelated.
- Division divisor ∈ {1–9} ∪ {10,20,…,90}.
- No multiplication tier exceeds 2-digit × 3-digit; no add/sub tier exceeds 4-digit.
- Exponent exp ≤ 3; multiplication-by-tens multiplier has no thousands.
- For every subtopic, each tier's parameter space ⊄ the tier below (distinctness).

## Implementation specifics & resolved gaps

These close ambiguities found in adversarial review so `/opsx:apply` has no open questions.

### New question shapes — signatures & answer types

| Shape | Topic/tier | `answer_type` | `signature` | Answer example |
|---|---|---|---|---|
| missing-addend | fraction-addition hard | numeric | `frac-add-missing:?+1/4=3/4` | `2/4` (unreduced) |
| whole/mixed − fraction | fraction-subtraction hard | numeric | `frac-sub:1-1/3` | `2/3` |
| missing-number | fraction-subtraction hard | numeric | `frac-sub-missing:?-1/4=3/4` | `4/4` / `1` |
| inverse ("write 8 as a power") | exponents hard | categorical | `exp-inverse:8` | `2^3` |
| commutativity ("is 2^5 = 5^2?") | exponents hard | categorical | `exp-cmp:2^5vs5^2` | `לא` / `כן` |
| whole-tens division | division hard | numeric | `div:840÷20` | `42` |

All other shapes keep their existing signature/answer_type. Fraction answers are stored **unreduced** per §0.5.

**Resolved review gaps in these shapes:**
- **Unreduced answers need a non-reducing formatter (gap A1).** `_frac_str(f: Frac)` cannot help — a `Fraction` is always reduced. Add a `(numerator, denominator)`-based formatter (or change `_frac_str` to take the pair) and have each fraction generator track num/denom in the *target* denominator (convert the smaller-denom operand up, sum/diff numerators, keep the common denominator; mixed number when numerator > denominator). Equal-denom whole results store the **unreduced** form (`3/6+3/6 → "6/6"`), with `"1"` accepted as equivalent by `/results`.
- **"Write N as a power" must have a unique answer (gap A2).** Constrain `N` to a prime-power with a **single** base≥2, exp≥2 representation — e.g. `8=2³`, `25=5²`, `27=3³`, `32=2⁵`. EXCLUDE ambiguous N like `16 (2⁴=4²)`, `64`, `81 (3⁴=9²)`. Store the single canonical `base^exp`; string-match is then safe.
- **Commutativity must not be always-"לא" (gap A3).** Include the one grade-4 equality case `2^4 vs 4^2` (answer `כן`) part of the time, so the shape genuinely tests the concept rather than training "always no."

### Within-tier shape distribution (suggested; implementer may tune)

- **division medium:** ~40% remainder, ~60% exact.
- **exponents hard:** ~⅓ forward-compute, ~⅓ inverse, ~⅓ commutativity-check.
- **order-of-operations:** shape chosen uniformly among the tier's listed forms.
- Distributions only need to guarantee each shape appears with non-trivial frequency — not exact ratios.

### order-of-operations invariants (all tiers)

- Any `÷` operand pair is exactly divisible (`b % c == 0`); no fractional intermediates.
- Every expression evaluates to a **non-negative integer** (grade 4 has no negatives).

### Validation mechanism (§6)

No pytest / `tests/` exists and the project is stdlib-only. Add a plain assert script (e.g. `tests/test_bands.py`) runnable via `python tests/test_bands.py`, calling `make_question(qtype, difficulty)` **directly** (not through `_generate_template_question`, which swallows exceptions and would mask a broken band). It asserts the cross-cutting invariants above over N samples per (topic, tier).

### Explicitly out of scope (recorded, not addressed here)

- **Weakness-aware param selection** (`_wrong_params` is defined but never called in `generator.py`) — drill-the-missed-thing loop; pairs with the deferred level ladder.
- **measurements "without formulas"** pedagogy — area/perimeter compute cleanly and in-range; the framing tension is noted only.
- The persistent **per-topic level ladder** (stored, ratcheting level in `summary.json`).
