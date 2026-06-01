# /results — Record Session Results

Guided conversational flow for entering a session's results. The parent reports what the child answered; the skill determines correctness and writes results.json.

**All output from this skill MUST be in English.** This includes prompts, confirmations, summary tables, error messages, notes stored in results.json, and progress focus lines. The only Hebrew allowed is in answer matching logic (recognizing Hebrew child answers) and when displaying the original Hebrew question text.

## Invocation

`/results [date] [inline results]`

- `/results` — discover unprocessed sessions, ask which to process
- `/results 2026-05-07` — process a specific session
- `/results two wrong: 63/9, 4/5 vs 1/5` — discover session + process inline results
- `/results 2026-05-07 all correct except q3` — specific date + inline results
- `/results AYL~2026-06-01~…~7` — paste a result code produced by the HTML quiz (carries the date + all of Ayala's typed answers)

## Behavior

### 1. Parse arguments

Parse the invocation args to extract:
- **Result code**: a token starting with `AYL~` — this is a code from the HTML quiz. If present, handle it via step 1b and SKIP the inline-results parsing.
- **Date**: a YYYY-MM-DD string, if present
- **Inline results**: any remaining text describing what the child answered (e.g., "two wrong: 63/9, 4/5 vs 1/5", "all correct except q3 she wrote 42")

If no date is found in the args, leave it unset (do NOT default to today).

### 1b. Decode a pasted result code (if present)

If a `AYL~…` result code was found, decode it deterministically in Python (validates the checksum and extracts the date + ordered answers):

```bash
python -c "
import sys, json
sys.path.insert(0,'src')
from quizcode import decode
try:
    print(json.dumps(decode('''{code}'''), ensure_ascii=False))
except ValueError as e:
    print(json.dumps({'error': str(e)}))
"
```

- **If the output has an `error`** (e.g. checksum mismatch): tell the parent "That code looks corrupted ({error}). Please ask Ayala to re-send it." — stop here. Do NOT record anything.
- **If decoded:** the result is `{"date": "...", "answers": [{"id": N, "answer": "..."}, ...]}`. Use `date` as the session date (skip step 2's discovery). Keep the `answers` list as the child's report and grade it in step 6 — there is no parent free-text to parse.

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

**If a result code was provided (step 1b):** skip this step — go directly to step 6 using the decoded `answers` list as the child's report.

**If inline results were provided in step 1:** skip this step — go directly to step 6, using the inline text as the parent's report.

**Otherwise:** show a summary of the questions (numbered list) and ask:
"Please tell me Ayala's answers. For example: 'Q1 she said 56, Q2 she didn't know, Q3 she wrote 12...'"

### 6. Process the report

**If the report came from a result code (step 1b):** for each question in generated.json, find the matching entry in the decoded `answers` by `id`, then:
- **Blank answer (`""`)** → mark the question **wrong** with note "left blank". (Unlike a parent-skipped question, a blank in the quiz is an observed non-answer, so it counts against `correct_rate`.)
- **Non-blank answer** → grade it against the correct answer with the same matching rules below, recording her actual answer in the note when wrong ("wrote 54 instead of 56").
- **Fraction-comparison questions** (exercise like "1/8 ___ 1/2"): the quiz captures a tapped sign `<`, `=`, or `>` (left-sign-right). Map it to the stored answer (the bigger fraction, or "שווים"): `<` → the RIGHT fraction is bigger; `>` → the LEFT fraction is bigger; `=` → "שווים". Mark correct when the mapped result matches the stored answer.
Do not ask the parent for missing questions — the code is complete. Then go to step 7.

**If the report came from parent free-text (inline or conversational):** for each question:
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
- For a comparison exercise "1/8 ___ 1/2" — the HTML quiz sends a sign `<`/`=`/`>` (left-sign-right): `<` means the right side is bigger, `>` the left, `=` → "שווים". The stored answer is the bigger fraction ("1/2") or "שווים". A parent's free-text "<" / "1/2" / "the second one" all mean the same; interpret accordingly.
- If unclear, ask rather than guess wrong
