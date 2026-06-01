## 1. Update data model in curriculum.py

- [x] 1.1 Change `_q()` signature to accept `description` and `exercise` instead of `he`, return dict with those two fields (no `"he"` key)
- [x] 1.2 Update `_mult_table()`: remove `כפול` and `מה ש-` templates; split remaining templates into description + exercise pairs (including the two missing-number templates)
- [x] 1.3 Update `_addition()`: remove `ועוד` template; split remaining templates
- [x] 1.4 Update `_subtraction()`: remove `פחות` template; split remaining templates
- [x] 1.5 Update `_multiplication()`: remove `כפול` template; split remaining templates
- [x] 1.6 Update `_division()`: remove `חלקי` template; split remaining templates (including remainder case)
- [x] 1.7 Update `_order_of_ops()`: split all templates (exercise = the expression string)
- [x] 1.8 Update `_prime_composite()`: split all templates (exercise = just the number `n`)
- [x] 1.9 Update `_divisibility()`: split all templates; exercise = `{n} ÷ {d}` (no `ב-`)
- [x] 1.10 Update `_fraction_comparison()`: split all templates; exercise = `{a}/{d1} ___ {b}/{d2}`
- [x] 1.11 Update `_fraction_addition()`: split all templates; exercise = `{a}/{d1} + {b}/{d2} =`
- [x] 1.12 Update `_fraction_subtraction()`: split all templates; exercise = `{a}/{d1} - {b}/{d2} =`
- [x] 1.13 Update `_measurements_area()`: move dimensions to description; exercise = `{l} × {w} =`
- [x] 1.14 Update `_measurements_perimeter()`: move dimensions to description; exercise = `2 × ({l} + {w}) =`
- [x] 1.15 Update `_exponents()`: remove `בחזקת` template; split remaining templates; exercise = `{base}^{exp} =`
- [x] 1.16 Update `_natural_numbers()`: split all templates; exercise = `{n:,}`

## 2. Update formatter.py

- [x] 2.1 Remove `_bidi_split()` function
- [x] 2.2 Update `format_session()` to render `"{id}. {description}\n   {exercise}"` for questions with both fields
- [x] 2.3 Add backwards-compatible fallback: if question has `"he"` but no `"description"`, render single line with `"he"`

## 3. Update generator.py (Claude fallback)

- [x] 3.1 Update Claude prompt (line 65) to request `"description"` and `"exercise"` JSON fields instead of `"he"`
- [x] 3.2 Update `_call_claude()` return dict (lines 80-81): unpack `data.get("description", "")` and `data.get("exercise", "")` instead of `data.get("he", "")`
- [x] 3.3 Add validation: warn (don't crash) if `"exercise"` contains Hebrew Unicode characters (`\u05D0`–`\u05EA`)

## 4. Update skills

- [x] 4.1 Check `.claude/skills/practice.md` for any reference to `q["he"]` and update if found
- [x] 4.2 Update `.claude/skills/results.md` line 33: change "id, he (Hebrew text)" → "id, description, exercise, answer, answer_type, signature"
- [x] 4.3 Update `.claude/skills/results.md` line 66: question text shown to parent should combine `description` + `exercise` (with fallback to `he` for old sessions)
- [x] 4.4 Update `.claude/skills/results.md` line 108: rewrite answer-matching examples to use new two-field format

## 5. Smoke test

- [x] 5.1 Run `python generate.py --force` and verify WhatsApp output shows two-line questions for all block types
- [x] 5.2 Verify no `"he"` key appears in the generated `wiki/sessions/.../generated.json`
- [x] 5.3 Verify no Hebrew characters appear in any `"exercise"` value across 50+ generated questions
