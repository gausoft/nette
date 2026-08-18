<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo-light.svg" alt="nette" width="96">
</picture>

# nette

**AI writes code. nette keeps it clean.**

A code readability tool for the AI-agent era. Deterministic, diff-aware,
calibrated on your codebase, fast enough to live inside the agent's
write-check-fix loop.

[![status](https://img.shields.io/badge/status-design_phase-f97316)](docs/vision.md)
[![python](https://img.shields.io/badge/python-%E2%89%A53.11-18181b)](pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-18181b)](LICENSE)
[![style](https://img.shields.io/badge/deps-zero-18181b)](pyproject.toml)

</div>

> [!WARNING]
> **Work in progress.** nette is in the design phase. Nothing to install yet.
> The vision and architecture are public so they can be challenged early.

## Why

AI agents now write most of the code. It works, but it is often hard to read:
too long, over-defensive, over-abstracted, inconsistent with the rest of the
repo. Classic linters like ruff and pylint check syntax and surface style.
They say nothing about readability or repo consistency, so debt accumulates
at machine speed.

nette lives in the agent loop: the agent writes code, runs nette, gets a
compact actionable verdict, fixes, re-checks. Like tests, but for readability.

```console
$ nette check
✗ services/booking.py:42  function does 3 things: extract validate_fare and persist_order
✗ routers/search.py:118   narrative comment restates the code below it
✓ 14 files clean · 2 findings · 0.4s
```

## Promises

| # | Promise | Meaning |
|---|---------|---------|
| 1 | **Judges new code, not legacy** | Diff mode by default. A 10-year-old repo is never "all red". |
| 2 | **Calibrated on YOUR repo** | Learns the local style, flags deviations. No universal style imposed. |
| 3 | **Verdict in under a second** | Deterministic: same code, same verdict, zero LLM at runtime. |
| 4 | **Findings say what to do** | Not "complexity 12 > 9" but "this function does 3 things: extract X and Y". |
| 5 | **Pure Python, zero deps** | `pip install nette` just works. nette's own code is the showcase. |
| 6 | **Extensible in 3 tiers** | Thresholds in TOML, pattern rules in YAML, deep rules in Python. |

## Not in scope (v1)

- Security ([bandit](https://github.com/PyCQA/bandit) exists), types
  ([mypy](https://github.com/python/mypy) exists), surface style
  ([ruff](https://github.com/astral-sh/ruff) exists).
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

## Contributing

The project is not ready for code contributions yet. Design feedback is
welcome: open an issue and challenge the [vision](docs/vision.md).

Agents contributing here follow [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
