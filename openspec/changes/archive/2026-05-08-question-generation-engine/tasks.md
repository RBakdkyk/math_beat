## 0. Curriculum Knowledge Extraction

- [x] 0.1 Use CandleKeep to read the full kita4 PDF (22 pages) and extract structured curriculum knowledge: all topics, subtopics, skills, pedagogical constraints, hour weights, competency indicators, and example question types
- [x] 0.2 Save extracted knowledge as `src/curriculum_knowledge.md` — the authoritative reference for all question generation
- [x] 0.3 Add pointer in CLAUDE.md: reference `src/curriculum_knowledge.md` as the curriculum source so every Claude Code session and skill has access to it

## 1. Project Setup

- [x] 1.1 Create project directory `~/workspace/ayala_math/` with `src/` and `wiki/` subdirectories
- [x] 1.2 Create `wiki/sessions/`, `wiki/progress/` directories and empty `wiki/progress/summary.json`
- [x] 1.3 Add CLAUDE.md with project overview, conventions, and pointer to `src/curriculum_knowledge.md`

## 2. Curriculum Model + Template Engine

- [x] 2.1 Create `src/curriculum.py` with topic tree: all 8 kita4 topics, subtopics, Hebrew names, hour weights (depends on 0.1-0.2 — templates must match curriculum scope)
- [x] 2.2 Define rule-based difficulty tiers per subtopic: easy/medium/hard as number range constraints + validation functions, not enumerated lists
- [x] 2.3 Define the 55 unique multiplication facts as a data structure
- [x] 2.4 Create Hebrew question templates (3+ per subtopic) with placeholders: multiplication, arithmetic, fractions, order of operations, divisibility, primes
- [x] 2.5 Add non-numeric answer types for categorical questions (prime/composite, yes/no, shape classification)
- [x] 2.6 Implement template engine: pick template + generate params from rules + validate constraints + compute answer + generate signature

## 3. Wiki / State Layer

- [x] 3.1 Create `src/wiki.py` with helpers: read/write JSON, list sessions, get recent sessions (last N)
- [x] 3.2 Define `generated.json` schema: questions with id, topic, subtopic, he, answer, answer_type, type, and signature
- [x] 3.3 Define `results.json` schema: list of {id, correct, note?}
- [x] 3.4 Define `summary.json` schema: per-topic correct_rate/times_practiced/last_practiced, multiplication facts with per-fact correct/wrong/last_seen, other topics with used_params list of {sig, date, correct}
- [x] 3.5 Implement overwrite protection: refuse to write generated.json or results.json if file exists (unless --force)

## 4. Progress Tracking

- [x] 4.1 Create `src/progress.py` with logic to merge a session's results into summary.json — update correct/wrong counts, append used_params, recalculate correct_rate
- [x] 4.2 Implement multiplication fact-level tracking: increment per-fact correct/wrong counts from results
- [x] 4.3 Implement 15-day retention prune: remove used_params entries older than 15 days on each update (multiplication facts are never pruned)
- [x] 4.4 Implement `--rebuild` mode: replay all sessions chronologically to rebuild summary.json from scratch
- [x] 4.5 Create `analyze.py` CLI entry point: parse date argument, read generated + results, call progress update

## 5. Session Composition

- [x] 5.1 Create `src/session.py` with topic selection algorithm: read summary.json, compute priority scores from correct_rate + staleness + times_practiced (all topics from kita4 available, no "current topic" config)
- [x] 5.2 Implement session structure builder: allocate warmup (3) + main (4-5) + secondary (1-2) based on priority scores and total count
- [x] 5.3 Implement bootstrapping mode: sensible defaults when no summary.json exists (diagnostic session)
- [x] 5.4 Implement CLI override logic: --topics, --count, --difficulty bypass automatic selection

## 6. Question Generation

- [x] 6.1 Create `src/generator.py` that orchestrates template engine for deterministic questions
- [x] 6.2 Implement signature-based dedup: check generated signature against summary.json used_params (within 15-day window), reject if found
- [x] 6.3 Implement weakness-aware selection: wrong answers → similar parameters next time, right answers → new parameters
- [x] 6.4 Implement Claude CLI fallback: call `claude -p <prompt> --output-format json` only for word problems, geometry, data/probability, or when template engine can't produce non-duplicate after 10 attempts
- [x] 6.5 Word problem signatures follow pattern `wordproblem:{category}:{level}`
- [x] 6.6 Implement JSON response parsing for Claude fallback with raw text fallback on parse failure

## 7. WhatsApp Formatter

- [x] 7.1 Create `src/formatter.py`: takes generated session → outputs numbered Hebrew list with block headers
- [x] 7.2 Handle date formatting (DD/MM/YYYY), plain text fractions, Unicode × for multiplication

## 8. Practice Skill

- [x] 8.1 Create `/practice` Claude Code skill definition (skill YAML + instruction markdown)
- [x] 8.2 Skill reads summary.json, shows one-line progress context ("Focus today: multiplication 58%, fractions 40%")
- [x] 8.3 Skill runs generate.py with computed args, displays WhatsApp-ready output
- [x] 8.4 Handle overwrite: if today's session exists, ask "show existing or regenerate?"
- [x] 8.5 Accept optional overrides: `/practice fractions 10 hard`

## 9. Results Skill

- [x] 9.1 Create `/results` Claude Code skill definition (skill YAML + instruction markdown)
- [x] 9.2 Skill reads generated.json for today (or specified date), knows all questions + correct answers + answer types
- [x] 9.3 Skill guides parent through reporting: accepts natural language, compares against correct answers (numeric and categorical), asks for clarification on skipped/ambiguous
- [x] 9.4 Skill writes results.json (with overwrite protection — warn if exists)
- [x] 9.5 Skill runs `python analyze.py {date}` and displays progress summary (total correct, per-topic breakdown, notable changes, tomorrow's focus)

## 10. CLI Entry Point

- [x] 10.1 Create `generate.py`: argparse for --topics, --count, --difficulty, --date, --force; orchestrates session composition → generation → save → format → print
- [x] 10.2 End-to-end test: run generate.py, verify generated.json saved with signatures and WhatsApp text printed
