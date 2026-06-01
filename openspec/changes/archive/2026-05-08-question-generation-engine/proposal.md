## Why

A 4th grader nearing end of year is struggling with multiplication table recall and just starting fractions and division with remainder. She needs daily 15-30 minute practice sessions to build confidence and close gaps. There's no tool that generates curriculum-aligned Hebrew math questions from the official Israeli Ministry of Education kita4 document, tracks progress per topic, and adapts to weak spots.

## What Changes

- New Python project at `~/workspace/ayala_math/`
- CLI to generate daily practice sessions (5-10 Hebrew math questions) — mostly deterministic via template engine, Claude CLI only for word problems and creative phrasing
- Structured JSON state: per-topic/subtopic progress with individual item tracking (correct/wrong counts, used parameters with signatures, last-seen dates)
- Claude Code `/results` skill: guided conversation where parent reports child's answers, skill determines correctness against generated.json, writes results.json, and updates progress
- CLI `analyze.py` as underlying engine for progress updates
- WhatsApp-friendly output formatting
- Curriculum knowledge extracted from kita4 PDF via CandleKeep into `src/curriculum_knowledge.md`, referenced in CLAUDE.md as the authoritative source
- Template engine with Hebrew question templates per subtopic, constrained number generation from valid pools, and signature-based deduplication against recent history
- Session composition engine: warmup (multiplication weak facts) + main (current school topic) + secondary (weakest topic from progress)
- Multiplication table tracked as 55 unique facts (commutative), each with individual correct/wrong counts

## Capabilities

### New Capabilities
- `curriculum-knowledge`: Extract structured curriculum knowledge from the kita4 PDF via CandleKeep — all topics, subtopics, skills, pedagogical constraints, competency indicators. Saved as `src/curriculum_knowledge.md` and referenced in CLAUDE.md so every Claude Code session and generation skill has the full curriculum context
- `curriculum-model`: Topic tree data structure extracted from kita4 — topics, subtopics, hour weights, pedagogical constraints, and rule-based difficulty tiers (easy/medium/hard defined as number range constraints, not enumerated lists)
- `template-engine`: Deterministic question generation via Hebrew templates + constrained randomization from rule-based parameter generation + signature-based deduplication against recent history. Handles ~75% of question types (multiplication, arithmetic, fractions, order of operations, divisibility, primes) without any LLM calls. Supports non-numeric answer types (yes/no, categorical) for geometry/probability/primes
- `session-composition`: Logic to read structured progress state and decide session structure — all topics available from kita4, prioritized by weakness/staleness/coverage, no "current topic" config needed
- `question-generation`: Orchestrates template engine for deterministic questions and Claude CLI for creative questions (word problems, geometry descriptions, data/probability scenarios). Word problem signatures: `wordproblem:{category}:{level}`. Falls back to Claude when template constraints can't produce a non-duplicate
- `progress-tracking`: Structured JSON state with per-topic correct rates, per-item correct/wrong counts, used parameter signatures with dates and correctness, multiplication fact-level tracking. 15-day retention prune on used_params
- `practice-skill`: Claude Code skill (`/practice`) — reads progress, decides session args, runs generate.py, formats and displays WhatsApp-ready output
- `results-skill`: Claude Code skill (`/results`) — guided conversational flow where parent reports child's answers per question, skill compares against correct answers from generated.json (including non-numeric), asks for clarification if needed, writes results.json, runs analyze.py, shows progress summary
- `whatsapp-formatter`: Format generated questions as WhatsApp-ready Hebrew text (numbered list, plain text fractions, copy-paste ready)

### Modified Capabilities

None — this is a greenfield project.

## Impact

- New project directory `~/workspace/ayala_math/` with Python source and wiki data directory
- Claude CLI dependency is optional — only needed for word problems and creative question types
- No external Python dependencies beyond standard library (random, json, argparse, pathlib, subprocess, datetime)
