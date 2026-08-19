# Vision & Requirements

## Problem

AI agents write most code today. It works but is often illegible: too long,
over-defensive, over-abstracted, inconsistent with the surrounding repo.
Existing linters check syntax and surface style, not readability or local
consistency. Technical debt now accumulates at machine speed.

## Solution

A readability tool that lives inside the agent loop: write,
check, fix, re-check. Deterministic, sub-second, diff-aware, calibrated on
the target repository.

## Primary audience

Teams coding with AI agents (Claude Code, Cursor, Copilot and friends), from
solo developers to large-scale engineering organizations.

## Success metric (v1)

On a real production backend: an agent using nette produces code the
maintainer judges readable without line-by-line review, and the repo's global
score can no longer degrade (ratchet effect).

## Market gaps nette targets

A 2026 survey of existing tools (kiss, agent-slop-lint, lipstyk, eigenhelm,
radon, lizard) identified four open gaps:

1. **Size metrics are not readability.** Nobody measures naming quality,
   local pattern consistency, defensive-code smell or narrative comments,
   which are the things that actually make AI code painful.
2. **No framework awareness.** Nothing understands FastAPI, Pydantic or
   SQLAlchemy idioms. A tool focused on one language can go deep here.
3. **No local-style calibration.** No tool learns a repo's conventions and
   flags deviation from them. This is nette's core differentiator.
4. **Poor DX.** No diff mode in kiss, rudimentary visualization everywhere,
   no output designed for agent consumption.

## Key design lessons (from ecosystem research)

- Extensibility is what makes a tool win (ESLint's 2,900 plugins vs Biome).
- ruff's plugin issue (#283) has been open since 2022, blocked by its Rust
  core. Pure Python resolves this structurally.
- Single AST shared by all rule tiers (avoid the two-parser trap).
- Explicit opt-in for plugins (avoid flake8's auto-activation trap).
- Per-rule timing exposed to the user (avoid silent slow-rule rot).
- The declarative tier stays declarative. No shell escape hatches (security).

## Roadmap phases

- **Phase 0**: Vision & requirements (this document). Done.
- **Phase 1**: Foundations research: how ruff, uv and pydantic-core achieve
  performance; tree-sitter vs stdlib ast; mypyc and Cython options; state of
  the art in metrics. Done: stdlib `ast` + `tokenize`, file-level result
  cache, single-pass rule engine, mypyc-friendly core, repo-calibrated
  detections over absolute scores.
- **Phase 2**: "Beautiful code" benchmarking: extract measurable patterns
  from exemplary Python codebases (CPython stdlib, FastAPI, pydantic, httpx,
  attrs). Scientific basis for the rules.
- **Phase 3**: DX & visualization research: error output design (ruff, elm,
  rust), TUI (rich/textual), agent-oriented output formats.
- **Phase 4**: Design doc: architecture, output format, v0.1 roadmap.
- **Phase 5**: Prototype on a real production codebase.
