# /results — Record Session Results

Guided conversational flow for entering a session's results. The parent reports what the child answered; the skill determines correctness and writes results.json.

**All output from this skill MUST be in English.** This includes prompts, confirmations, summary tables, error messages, notes stored in results.json, and progress focus lines. The only Hebrew allowed is in answer matching logic (recognizing Hebrew child answers) and when displaying the original Hebrew question text.

## Invocation

`/results [date] [inline results | AYL~…code]`

- `/results` — discover unprocessed sessions, ask which to process
- `/results 2026-05-07` — process a specific session
- `/results two wrong: 63/9, 4/5 vs 1/5` — discover session + process inline results
- `/results 2026-05-07 all correct except q3` — specific date + inline results
- `/results AYL~2026-06-08~W1sx…~j` — **code mode**: decode a quiz return code
- `/results CODE:AYL~2026-06-08~W1sx…~j` — same, with optional `CODE:` prefix
- `/results done! AYL~2026-06-08~W1sx…~j 🎉` — code embedded in pasted text

## Input modes

**Before anything else, scan the raw invocation text for an `AYL~` marker** (with or without a `CODE:` prefix, possibly surrounded by other text or emoji).

- **If an `AYL~…` code is present → use Code mode** (below). The child solved the quiz on her phone and the parent pasted the return code; decode and grade it instead of taking a verbal report. The envelope carries the session date, so no discovery is needed.
- **Otherwise → use Verbal mode** (the `## Behavior` flow further down).

### Code mode

The decode/grade/checksum logic lives in `quiz_results.py` so grading is deterministic. Pass the pasted text **starting from the `AYL~` marker** (drop any leading words), single-quoted. An `AYL~` code itself never contains a single quote, so single-quoting is safe; trailing text/emoji after the check char is ignored by the extractor.

1. **Preview** (decodes, validates the checksum case-insensitively, confirms a `generated.json` exists for the envelope's date, grades; writes nothing):
   ```bash
   python quiz_results.py preview '<entire pasted text>'
   ```
   The output is one JSON object:
   - `{"error": "..."}` → show the message to the parent and **stop, writing nothing**. A checksum failure means "the code looks corrupted — please re-paste it"; a missing-session error means there is no session for that date.
   - otherwise `{date, exists, correct, total, graded:[{id, exercise, description, stored, child, correct, type}]}`. Blank (`""`) and excluded/absent questions are already omitted.

2. **Show the summary** (English). One line per `graded` entry — its `exercise`, the child's `child` answer, and ✓/✗ — then `Correct: {correct} of {total}`. Note any omitted questions as skipped.

3. **Confirm before writing.** Ask: "Write results for {date}?" If `exists` is true, warn that this overwrites and re-processes the existing results.

4. **Write** on confirmation:
   ```bash
   python quiz_results.py write '<entire pasted text>'
   ```
   (`write` auto-forces when `results.json` already exists; add `--force` to be explicit.) The output JSON includes `reprocessed` (true when the date already had results). The child's raw answer is recorded as each result's note.

5. **Analyze** — feed progress, choosing the path that avoids double-counting (see below):
   - first-time (`reprocessed` is false): `python analyze.py {date}`
   - re-processing (`reprocessed` is true): `python analyze.py --rebuild`

6. **Focus line.** Display the analyze output, then add: "Tomorrow: focus on {weakest_topic} ({rate}% correct)." — same tail as Verbal mode.

## Behavior

### 1. Parse arguments

Parse the invocation args to extract two things:
- **Date**: a YYYY-MM-DD string, if present
- **Inline results**: any remaining text describing what the child answered (e.g., "two wrong: 63/9, 4/5 vs 1/5", "all correct except q3 she wrote 42")

If no date is found in the args, leave it unset (do NOT default to today).

### 2. Resolve the session date

**If a date was provided in step 1:** use it directly.

**If no date was provided:** run session discovery:

```bash
python -c "
import sys, json
sys.path.insert(0,'src')
from wiki import list_sessions, read_generated, read_results
unprocessed = []
for d in list_sessions():
    if read_generated(d) is not None and read_results(d) is None:
        unprocessed.append(d)
print(json.dumps(unprocessed))
"
```

Then branch:
- **Zero unprocessed sessions:** "All sessions have results. To re-process one, run `/results YYYY-MM-DD`." — stop here.
- **One unprocessed session:** "Found unprocessed session from {date}. Process this one?" — wait for confirmation. If no, stop.
- **Multiple unprocessed sessions:** Show a numbered list and ask the parent to pick one.

### 3. Load generated.json

```bash
python -c "
import sys, json
sys.path.insert(0,'src')
from wiki import read_generated
qs = read_generated('{date}')
if qs: print(json.dumps(qs, ensure_ascii=False))
else: print('null')
"
```

**If null:** "No questions found for {date}. Did you generate that session? Try running /practice first."

**If found:** Load all questions. You now know: id, description (Hebrew prompt), exercise (pure math), answer, answer_type, signature. Old sessions may have a single `he` field instead of `description`+`exercise`.

### 4. Check if results.json already exists

```bash
python -c "
import sys
sys.path.insert(0,'src')
from wiki import results_path
print('exists' if results_path('{date}').exists() else 'new')
"
```

**If exists:** Warn: "Results already exist for {date}. Continuing will overwrite them. Continue?"
- If no: abort
- If yes: proceed (will use --force when writing)

### 5. Invite parent to report results

**If inline results were provided in step 1:** skip this step — go directly to step 6, using the inline text as the parent's report.

**Otherwise:** show a summary of the questions (numbered list) and ask:
"Please tell me Ayala's answers. For example: 'Q1 she said 56, Q2 she didn't know, Q3 she wrote 12...'"

### 6. Process the parent's report

For each question:
- Parse the parent's text to identify which question number was addressed
- Compare the child's answer to the correct answer:
  - **Numeric answers:** allow minor variations ("56" vs "56.0", spaces)
  - **Categorical answers (כן/לא, ראשוני/פריק):** case-insensitive Hebrew string match
  - **Fraction answers:** accept any mathematically equivalent form. Stored answers are UNREDUCED (grade 4 does not reduce — reduction is grade 5), so e.g. the stored answer "2/4" MUST also accept "1/2" and "0.5"; stored "6/6" must accept "1". Match reduced ↔ unreduced ↔ decimal as equal.
- Mark as correct or wrong
- Record a note in English if the parent described what was written (e.g., "wrote 54 instead of 56", "didn't understand concept")

**For any skipped or ambiguous questions**, ask specifically:
"What did Ayala answer for Q{n}: '{description} {exercise}'?" (or `he` for old sessions)

If parent says "didn't do it" or "skipped" → omit from results (not counted as wrong).

### 7. Confirm before writing

Show a summary table using English topic labels (mult, fraction, addition, subtraction, division):
```
Results Summary:
Q1 (mult 7×8): ✓ correct
Q2 (fraction 1/2+1/4): ✗ wrong (answered 3/8)
...
Correct: X out of Y
```

Ask: "Write results?"

### 8. Write results.json

```bash
python -c "
import sys, json
sys.path.insert(0,'src')
from wiki import write_results
results = {json_results}
write_results(results, '{date}', force={force})
print('done')
"
```

### 9. Run analyze.py and show progress summary

```bash
python analyze.py {date}
```

Display the output, then add a one-line focus for tomorrow:
"Tomorrow: focus on {weakest_topic} ({rate}% correct)."

## Answer matching notes

- For exercise "7 × 8 =" — correct answer is "56". Match "56", "חמישים ושש" (if parent types Hebrew)
- For exercise "17" (description: "ראשוני או פריק?") — correct is "ראשוני". Match "ראשוני", "כן", "yes", "prime"
- For exercise "1/4 + 1/4 =" — stored answer is "2/4" (unreduced). Match "2/4", "1/2", "0.5"
- For exercise "1/2 + 1/4 =" — stored answer is "3/4". Match "3/4", "0.75"
- For an exponent exercise "8 =" (description: "כתוב/י כחזקה") — correct is "2^3". Match "2^3", "2³"; for "is a^b = b^a?" match כן/לא (yes/no)
- If unclear, ask rather than guess wrong
