# Decisions

Short records of choices already made. Read before questioning a past
choice; append a new entry when a significant choice is made.

## 001: Pure Python implementation

Rust-based tools (ruff) cannot offer a plugin API their users can write
(issue astral-sh/ruff#283, open since 2022). nette's users are Python
developers; they extend it in Python. Performance targets are met through
architecture (caching, incremental analysis, parallelism), not language.

## 002: Deterministic runtime, no LLM

LLM reviewers are non-reproducible and share the generator's blind spots.
A check that gives different verdicts on the same code cannot gate a
commit. LLMs may appear in optional, clearly separated layers later, never
in the check path.

## 003: Diff-aware by default

Legacy codebases would be "all red" under whole-repo judgment, which kills
adoption and buries the signal. The unit of judgment is the change.
Whole-repo analysis serves calibration and audit.

## 004: Three-tier extensibility

TOML for thresholds, YAML for declarative patterns, Python for deep rules.
Modeled on what worked (ESLint plugins, semgrep rule registry) while
avoiding known traps: flake8's silent plugin activation, ESLint's config
maze, the two-parser incoherence.

## 005: Python first, one language at a time

Depth beats breadth: framework-aware rules (FastAPI, Pydantic, SQLAlchemy)
require deep single-language investment. Other languages come later as
sibling products, not as a shallow multi-language mode. Scope is stated
once in the README; the product identity is the mission, not the language.

## 006: Prose quality is part of the product

A tool that fights AI slop in code cannot ship AI slop in prose. Writing
rules live in writing.md and apply to every sentence in the repository.
