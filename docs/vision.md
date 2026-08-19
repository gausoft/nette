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
5. **Nothing looks above the file.** All tools stop at file boundaries.
   Project structure — file size norms, file naming conventions, folder
   depth, where a new file belongs — is unmeasured, and it is precisely
   where AI agents drift (catch-all 800-line files, `utils2.py`, files
   dropped in the wrong folder). Repo calibration applies here too: learn
   the repo's structural signature, flag new files that deviate.

## Key design lessons (from ecosystem research)

- Extensibility is what makes a tool win (ESLint's 2,900 plugins vs Biome).
- ruff's plugin issue (#283) has been open since 2022, blocked by its Rust
  core. Pure Python resolves this structurally.
- Single AST shared by all rule tiers (avoid the two-parser trap).
- Explicit opt-in for plugins (avoid flake8's auto-activation trap).
- Per-rule timing exposed to the user (avoid silent slow-rule rot).
- The declarative tier stays declarative. No shell escape hatches (security).

## Roadmap phases

### Research

- **Phase 0**: Vision & requirements (this document). Done.
- **Phase 1**: Foundations research: how ruff, uv and pydantic-core achieve
  performance; tree-sitter vs stdlib ast; mypyc and Cython options; state of
  the art in metrics. Done: stdlib `ast` + `tokenize`, file-level result
  cache, single-pass rule engine, mypyc-friendly core, repo-calibrated
  detections over absolute scores.
- **Phase 2**: "Beautiful code" benchmarking: extract measurable patterns
  from exemplary Python codebases (CPython stdlib, FastAPI, pydantic, httpx,
  attrs). Scientific basis for the rules. Done: two threshold families
  (universal shape metrics with benchmark-derived defaults; repo-calibrated
  style metrics), scope-aware naming rule, FastAPI-aware profile from v1. Done: universal thresholds
  (function length, nesting, args, returns) vs repo-calibrated dimensions
  (annotations, docstrings, comments, defensiveness); framework awareness
  proven necessary by FastAPI's endpoint signatures.
- **Phase 3**: DX & visualization research: error output design (ruff, elm,
  rust), TUI (rich/textual), agent-oriented output formats. Done: one
  diagnostic model feeding every renderer (human in the Elm/rustc style,
  agent output — signal-only, deterministic, with composed instructions —
  SARIF deferred to v0.2), stable rule codes with `--explain`, calibrated
  findings show the repo baseline in the message, affirmative suggestions
  with confidence levels, tested finding catalog with golden outputs.

### Design

- **Phase 4**: Design doc: architecture (engine, rule tiers, calibration,
  cache), public API surface, output formats (human and agent), config
  schema, v0.1 scope cut. Reviewed before any implementation starts.
  Done: [design.md](design.md), reviewed and frozen for v0.1.

### Implementation

TDD throughout: each step starts with failing tests, ends green. Every
phase preserves the two core invariants: extensible (three rule tiers,
single shared AST) and fast (diff-aware, file-level cache, single pass).

- **Phase 5**: Core engine: file discovery, `ast` + `tokenize` parsing,
  rule runner, diagnostics model. The minimal loop: files in, findings out.
- **Phase 6**: First rule set: the universal-threshold rules from Phase 2
  (function length, nesting depth, argument count, returns per function).
- **Phase 7**: Calibration: `nette calibrate` produces the repo profile
  (p50/p90/p99 per metric); calibrated rules judge deviation from it.
- **Phase 8**: Diff-aware mode and file-level result cache: judge only
  changed code, re-runs near-free.
- **Phase 9**: Extensibility tiers: TOML thresholds, YAML declarative
  patterns, Python plugin API (dogfooded by our own rules).
- **Phase 10**: Output & integration: agent-oriented output, human CLI
  output, MCP server, framework profiles (FastAPI first).

### Release

- **Phase 11**: Prototype on a real production codebase; fix what reality
  breaks.
- **Phase 12**: v0.1 on PyPI: packaging, docs, benchmark numbers published.
