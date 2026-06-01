# /practice — Generate Daily Math Practice Session

Generates a daily Hebrew math practice session for Ayala, formats it for WhatsApp copy-paste.

## Invocation

`/practice [topic] [count] [difficulty]`

Examples:
- `/practice` — automatic, driven by progress
- `/practice fractions 10 hard` — override topic/count/difficulty
- `/practice multiplication-table` — only multiplication warmup
- `/practice fractions=hard division=easy` — per-topic difficulty, topic selection automatic

## Behavior

### 1. Parse arguments

If arguments are provided, map them:
- topic words like "fractions", "division", "multiplication" → map to topic keys
- count = integer
- difficulty = a single global level ("easy"/"medium"/"hard"), OR one or more
  per-topic assignments of the form `topic=level` (e.g. `fractions=hard division=easy`)

Topic name mapping (Hebrew or English accepted):
- fractions / שברים → fraction-addition, fraction-comparison, fraction-subtraction
- multiplication / כפל → multiplication-table, multiplication
- division / חילוק → division
- arithmetic / חשבון → addition, subtraction, multiplication, division
- geometry / צורות → geometry
- probability / סיכויים → probability

**Difficulty syntax:**
- A bare positional level (`hard`) is the **global** difficulty applied to all questions.
- `topic=level` tokens set the tier for a specific topic only; precedence is
  per-topic > global > automatic. A per-topic override applies only when that
  topic is selected — it does not force the topic in. To guarantee a topic
  appears, also pass it as the positional topic (which maps to `--topics`).
- The two forms compose: `medium fractions=hard` → global medium, fractions hard.

### 2. Check if today's session already exists

Run:
```bash
python -c "import sys; sys.path.insert(0,'src'); from wiki import generated_path, today; p=generated_path(today()); print('exists' if p.exists() else 'new')"
```

**If exists:** Ask: "A session already exists for today. Show the existing one or regenerate?"
- Show existing: read and display `wiki/sessions/{today}/generated.json` formatted
- Regenerate: proceed with `--force`

### 3. Show progress context

Read `wiki/progress/summary.json`. If it exists, show one line:
```
Today's focus: multiplication ({mult_rate}% correct) + {main_topic} ({rate}% correct). Weak facts: {weak_facts}
```

If no summary.json: "First diagnostic session — starting at an easy pace."

### 4. Build arguments for generate.py

**Without overrides:**
```bash
python generate.py
```

**With overrides:**
```bash
python generate.py --topics {topic} --count {count} --difficulty {difficulty}
```

- Pass the global level as a bare token: `--difficulty hard`.
- Pass per-topic tiers as `topic=level` tokens (no `--topics` needed if you only
  want to set difficulty): `--difficulty fractions=hard division=easy`.
- `--difficulty` accepts multiple tokens and may mix a global with per-topic
  assignments: `--difficulty medium fractions=hard`.

Add `--force` if regenerating an existing session.

### 5. Display output

Show the WhatsApp-ready text exactly as printed by generate.py.

Add at the bottom:
```
────────────────────────
Copy the text above and send it to Ayala on WhatsApp.
After the practice, run /results to record the results.
```

## Error handling

- If generate.py fails: show the error and suggest checking `src/curriculum.py`
- If summary.json is malformed: warn and proceed in bootstrap mode
