# nette

**AI writes code. nette keeps it clean.**

A code readability tool for Python, built for the AI-agent era. It is
deterministic, diff-aware, calibrated on your codebase, and fast enough to
live inside the agent's write-check-fix loop.

> Status: design phase. Nothing to install yet.

## Why

AI agents now write most of the code. It works, but it is often hard to read:
too long, over-defensive, over-abstracted, inconsistent with the rest of the
repo. Classic linters like ruff and pylint check syntax and surface style.
They say nothing about readability or repo consistency, so debt accumulates
at machine speed.

nette lives in the agent loop: the agent writes code, runs nette, gets a
compact actionable verdict, fixes, re-checks. Like tests, but for readability.

## Promises (non-negotiable)

1. **Judges new code, not legacy.** Diff mode by default: only the lines you
   just wrote count. A 10-year-old repo is never "all red".
2. **Calibrated on YOUR repo.** nette learns the local style (naming,
   structure, patterns) and flags deviations instead of imposing a universal
   style.
3. **Verdict in under a second.** Fast enough to run on every agent edit.
   Deterministic: same code, same verdict, zero LLM at runtime.
4. **Every finding says what to do.** Not "complexity 12 > 9" but "this
   function does 3 things: extract X and Y". An agent can act on it directly.
5. **Pure Python, zero exotic dependencies.** `pip install nette` just works.
   nette's own code is the showcase of the standard it enforces.
6. **Extensible in 3 tiers, in YOUR language.** Thresholds in TOML, pattern
   rules in YAML, deep rules in Python, all through the same public API that
   nette's built-in rules use.

## Not in scope (v1)

- Security (bandit exists), types (mypy exists), surface style (ruff exists).
- Multi-language support. Python only, done deeply. TypeScript comes later
  as a sibling product.
- LLM review. Deterministic or nothing.

## Interfaces (v1)

- **CLI**: `nette check`, diff-aware, compact output.
- **MCP server**: first-class integration into AI-agent loops.
- A rich visual report for humans will come in v2.

## Documentation

- [Vision & requirements](docs/vision.md)
- [Extensibility design](docs/extensibility.md)
