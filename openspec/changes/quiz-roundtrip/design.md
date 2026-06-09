## Context

The session pipeline already exists end to end: `generate.py` → `session.py` (weakness-driven selection) → `generator.py` → `wiki/sessions/{date}/generated.json`, and `analyze.py` → `progress.py` → `summary.json`, which `session.py` reads back to pick the next day's topics. The only manual hop is recording results: today the parent reports verbally through the `/results` skill.

A prior version inserted a phone round-trip in that hop. It is gone from the working tree (never committed), but three real return codes survived and were decoded, pinning down the wire format exactly. This design reconstructs the round-trip around that recovered format, reusing the entire grading/progress/selection engine.

## Goals / Non-Goals

**Goals:**
- Wrap a session into a self-contained `quiz.html` the parent can attach in WhatsApp.
- Accept the returned `AYL~…` code as a `/results` input mode and grade it on the machine.
- Make the grading subtleties the three codes exposed (comparison symbols, units, thousands separators, blanks) explicit, testable rules.
- Reuse `analyze.py` / `progress.py` / `session.py` without modification.

**Non-Goals:**
- Any hosting, server, or automated WhatsApp send/receive.
- On-phone grading or feedback.
- Figure-dependent topics in the quiz.

## Recovered wire format (authoritative)

```
ENVELOPE   AYL ~ <date> ~ <base64(JSON)> ~ <check>
           check = BASE36[ sum(bytes("AYL~" + date + "~" + b64)) % 36 ]
                   BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"

PAYLOAD    JSON: [[id, "answer"], …]
           • carries only RENDERED questions; "" means rendered-but-unanswered
           • answer is a STRING (fractions, symbols, Hebrew all survive)
           • base64 is STANDARD (not urlsafe); decode tolerates missing padding
```

Verified: the check function reproduces `j`, `3`, `9` for the three sample codes. This is the contract both `quiz.py` (encode) and the `/results` code branch (decode + validate) implement.

## Decisions

### D1 — Grading stays on the machine; the phone never sees the answer key

The HTML carries questions only. The return code carries her raw answers. All correctness is decided here against `generated.json`. This reuses every existing matching rule, prevents view-source cheating, and matches the project's existing "parent mediates grading" model. Consequence: no on-phone score; feedback comes later, exactly as today.

### D2 — Comparison: normalize to symbol framing, derive the symbol on the grader

`fraction-comparison` randomly picks one of three prompts (`curriculum.py:387-389`) and always stores the answer as the **larger fraction** (e.g. `"5/8"`), or the literal **`"שווים"`** when the two are equal — never a symbol. The quiz collects a **symbol** (`>`/`<`/`=`; see sample `[7,">"]`).

To keep the displayed text consistent with the widget, the quiz renders **every** comparison question with the canonical prompt `"סמני > או < או ="` and `>`/`<`/`=` buttons, regardless of which prompt the generator stored (parent decision: use the `"סמני"` framing only). This is a quiz-render override; it does not change `curriculum.py` or the verbal `/results` path.

The grader then: parses the two operands from `exercise`, and
- if the stored answer equals one of the operands, derives `>`/`<` from which side that operand is,
- if the stored answer is `"שווים"`, the correct symbol is `=`,

then compares the derived symbol to her tapped symbol. Implemented in the `/results` decode branch — `generated.json`'s existing shape is untouched.

### D3 — Widget comes from per-question metadata, not from `type` or `answer_type`

A `type`→widget table is unsound: `exponents` alone emits a numeric question (`base^exp =`), a typed-string categorical (`כתוב/י כחזקה` → `"2^3"`), and a yes/no categorical (`האם שווה?` → `כן`/`לא`), and `answer_type == "categorical"` covers both button-choice and typed-string answers. So the **generator emits per-question widget metadata** into `generated.json`:

- a `widget` kind: `text` (free entry; numeric, fraction, or typed strings like `2^3`) or `choice`,
- for `choice`, an `options` list of button labels (e.g. `["ראשוני","פריק"]`, `["כן","לא"]`).

`fraction-comparison` is the one render-time override (D2): it is presented as a `choice` of `>`/`<`/`=` even though its stored answer is a fraction. The wrap step reads `widget`/`options`; it never infers them from `type`.

### D4 — Needs-visual topics are excluded, not faked

`geometry` and `symmetry` generally require a drawn figure the static HTML cannot provide. Topics are classified `quiz_renderable` vs needs-visual. The everyday path is unaffected: the adaptive planner (`session.py:_prioritized_topics`) only iterates `TEMPLATE_TOPICS`, so a normal session never contains these. If a session is *forced* to include one (`--topics geometry`), `quiz.py` skips that question with a warning; the excluded question is simply **absent** from the rendered set and therefore from the payload (a missing id is not counted — distinct from a rendered-but-blank `""`). `word-problems` and `probability` are text-plus-typed-answer and remain quiz-renderable as long as their answer is machine-checkable.

### D5 — Normalization and unit-stripping before numeric compare

The codes show free-typed numbers: `"1,038"` (thousands separator), `"381,"` (trailing stray comma), `"52.1"` (decimal). Before a numeric/fraction compare the grader strips `,` and trailing punctuation and keeps `.` and `/`. Separately, measurement keys carry units (`"247 מ\"ר"`, `"192 ס\"מ"`) while she types only the number, so the grader strips the unit suffix from the **key** for area/perimeter. Reuses the existing fraction-equivalence rule (unreduced ↔ reduced ↔ decimal) untouched. Because answers may contain `/`, `,`, `.`, the numeric widget is a **free-text field**, never an `<input type="number">`.

### D6 — Blank means skipped; absent means not-rendered

A rendered-but-unanswered question is encoded `""` and omitted from `results.json`; an excluded (needs-visual) question is absent from the payload entirely. Both end up uncounted — `progress.py` only counts ids present in results — so neither is ever scored wrong.

### D7 — Robust paste handling

The decoder anchors on the `AYL~` marker and matches the date, base64 charset, and exactly one trailing check char via a strict pattern, so surrounding text/emoji ("done! AYL~…~j 🎉") don't break parsing. It trims surrounding whitespace and treats the check char case-insensitively (lower-cased before compare) to survive mobile autocorrect. On checksum mismatch or unknown date it stops with a clear English message and writes nothing.

### D8 — `.env` parsed with stdlib only

`PARENT_WHATSAPP` is read from `.env` with a tiny `KEY=VALUE` parser (no new dependency, per the project's stdlib-only rule), normalized to `wa.me` form (digits only, no `+`/spaces) when building the Done-button link. `.env` is added to `.gitignore` so the number never lands in a commit.

### D9 — The Done button URL-encodes the code

Standard base64 can contain `+` and `/`; in a `wa.me?text=` URL an unencoded `+` decodes to a space and corrupts the code (the three recovered samples avoided this only because their payloads were short digit arrays). The Done button therefore wraps the whole `AYL~…~check` string in `encodeURIComponent(...)` before placing it in the link. Base64 stays **standard** so the recovered checksum definition still holds; the `~` separators survive encoding.

### D10 — Re-processing a date rebuilds, never increments

`analyze.py {date}` → `update_summary` **appends** `used_params`, bumps per-fact counts and `times_practiced` with no per-date dedup (`progress.py`). Re-pasting a code (easy via `--force`) would therefore double-count into `summary.json`. So when a date already has `results.json`, the code branch rewrites `results.json` with `--force` and then runs `analyze.py --rebuild` (wipe + replay all sessions) instead of the incremental `analyze.py {date}`. First-time processing keeps the cheaper incremental path.

## Risks / Trade-offs

- **Mobile opening of a `.html` attachment is inconsistent** (esp. iOS). Accepted: this is how the lost version worked in practice for this family; not solving hosting here.
- **A single check char** catches accidental corruption, not deliberate tampering. Acceptable for a 4th-grader's practice loop.
- **Claude-generated answers must be machine-checkable** (number/fraction/categorical) for `word-problems`/`probability` to be quiz-renderable; a free-text answer would fall back to manual `/results`. Noted, not enforced here.
- **Per-question widget metadata is a `generated.json` schema addition.** Old sessions without it must still grade via the verbal path; the quiz only consumes sessions generated after this change.

## Reused unchanged

`session.py` (selection), `progress.py` (merge/prune/recalculate), `analyze.py` (CLI, including `--rebuild`), `wiki.py` (read/write/`results_path`/`--force`), and the existing `/results` write + analyze + "tomorrow focus" tail. The code branch only adds decode + the D2/D5/D6/D10 rules in front of the existing grading.
