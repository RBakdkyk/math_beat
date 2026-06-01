# ayala_math — Daily Math Practice Generator

A CLI tool that generates curriculum-aligned Hebrew math practice sessions for a 4th grade student (כיתה ד׳), tracks progress per topic, and adapts to weaknesses.

## Project Layout

```
ayala_math/
  src/
    curriculum_knowledge.md   # Authoritative curriculum reference (from kita4 PDF)
    curriculum.py             # Topic tree + templates + difficulty rules
    wiki.py                   # JSON read/write helpers, session listing
    progress.py               # Merge results into summary.json
    session.py                # Topic selection + session structure builder
    generator.py              # Orchestrates template engine + Claude CLI fallback
    formatter.py              # WhatsApp-ready Hebrew text output
  wiki/
    sessions/{date}/
      generated.json          # Output of generate.py
      results.json            # Parent fills via /results skill
    progress/
      summary.json            # Structured progress state (the system's memory)
  generate.py                 # CLI: generate a session
  analyze.py                  # CLI: update progress from a session's results
  .claude/skills/
    practice.md               # /practice skill instructions
    results.md                # /results skill instructions
```

## Curriculum Reference

`src/curriculum_knowledge.md` is the extracted knowledge from the official Israeli Ministry of Education kita4 document (855 lines). **Do not load it whole.** Grep it when you need specific facts:

```bash
grep -i -A 10 "fraction" src/curriculum_knowledge.md
grep -i -A 5 "divisor" src/curriculum_knowledge.md
```

All question generation must align with what it says.

## Multiplication Table — Key Practice Priority

The kita4 curriculum assumes table facts (1×1–10×10) are mastered from grade 3, but Ayala needs to strengthen them — this is the primary reason the app exists. Every session starts with 3 multiplication warmup questions targeting her weakest facts.

The 55 unique facts (commutativity-deduplicated) are defined in `src/curriculum.py` as `MULTIPLICATION_FACTS`. Progress is tracked per-fact in `summary.json` under `topics.multiplication-table.facts`.

## Conventions

- No external Python dependencies — stdlib only (json, pathlib, random, argparse, subprocess, datetime)
- Questions in Hebrew; code and variable names in English
- `generated.json` and `results.json` are write-once (use `--force` to overwrite)
- Signatures: `"{type}:{params}"` (e.g., `"mult:7×8"`, `"fraction-add:1/2+1/4"`)
- Word problem signatures: `"wordproblem:{category}:{level}"`
- `summary.json` is rebuildable from session history via `python analyze.py --rebuild`

## CLI Entry Points

```bash
python generate.py [--topics TOPIC] [--count N] [--difficulty easy|medium|hard] [--date YYYY-MM-DD] [--force]
python analyze.py [DATE] [--rebuild]
```

## Skills

- `/practice [topic] [count] [difficulty]` — generate daily session, display WhatsApp-ready output
- `/results [date]` — guided results entry, writes results.json, updates progress
