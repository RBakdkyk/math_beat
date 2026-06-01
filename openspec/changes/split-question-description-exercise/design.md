## Context

Every question is currently a single Hebrew string in the `"he"` field that interleaves the prompt text with the math formula. WhatsApp's BiDi rendering reverses mixed RTL/LTR text unpredictably, and Hebrew words used as math operators (כפול for ×, פחות for −) create ambiguity. `formatter.py` has a partial workaround (`_bidi_split`) that only handles the `: ` pattern.

The fix is to make the split structural: every question carries a `"description"` (Hebrew, RTL) and an `"exercise"` (math symbols, LTR) as separate fields.

## Goals / Non-Goals

**Goals:**
- Every question renders as two lines: Hebrew description then pure-math exercise
- No Hebrew words appear inside the exercise expression
- Formatter is simplified (no heuristic string splitting)
- Claude-generated questions follow the same contract

**Non-Goals:**
- Changing question difficulty, answer values, or curriculum coverage
- Migrating existing `wiki/sessions/*/generated.json` files (read-only history)
- Internationalising the exercise line (it stays ASCII/Unicode math symbols)

## Decisions

### D1: Two fields instead of one

Replace `"he"` with `"description"` + `"exercise"` in the question dict.

**Alternatives considered:**
- Keep `"he"` with a separator token (e.g. `\n`) — fragile; callers must know to split
- Keep `"he"` and derive the split in the formatter — forces heuristics back in

**Rationale:** Explicit fields are unambiguous. The formatter just renders them; no parsing needed.

### D2: Drop Hebrew-operator templates entirely, don't try to salvage them

Templates like `כמה זה {a} כפול {b}?` embed a Hebrew word where the exercise symbol belongs. Rather than reconstructing them as split templates, remove them. Each generator has enough remaining templates to maintain variety.

**Rationale:** Simpler. These templates exist only because the old single-string model required them.

### D3: Exercise format conventions

| Situation | Exercise format |
|---|---|
| Compute result | `{a} × {b} =` |
| Fill blank | `{a} × ___ = {result}` |
| Compare fractions | `{a}/{d1} ___ {b}/{d2}` |
| Divisibility check | `{n} ÷ {d}` |
| Prime / factorize | `{n}` |
| Place value | `{n:,}` |
| Area / perimeter | `{l} × {w} =` |

### D4: Formatter renders description + indented exercise

```
{id}. {description}
   {exercise}
```

No special-casing per question type — the formatter is generic.

### D5: Claude prompt updated to return JSON with both fields

The Claude fallback in `generator.py` currently asks for a `"he"` field. Update the prompt to ask for `"description"` and `"exercise"` separately. Add a validation step that rejects responses missing either field.

## Risks / Trade-offs

- **Existing session files use `"he"`** → Formatter must guard against old sessions (display `q.get("description") or q.get("he", "")`) or old files are just not re-rendered. Since sessions are write-once history, accepting the incompatibility is acceptable.
- **Claude may hallucinate Hebrew in the exercise field** → Validation in `generator.py` should warn if Hebrew characters appear in `"exercise"`. Not a hard error for now.
- **Reduced template variety per generator** → Removing 1-2 templates per generator is acceptable; remaining templates still provide variation.

## Migration Plan

1. Update `_q()` and all generators in `curriculum.py`
2. Update `formatter.py`
3. Update `generator.py` Claude prompt + validation
4. Smoke-test: `python generate.py --force` and verify WhatsApp output
5. No database migration needed — old session files are not re-rendered

## Open Questions

- Should the formatter add a blank line between description and exercise, or just a newline + indent? (Current proposal: newline + 3-space indent — matches the user's stated preference.)
