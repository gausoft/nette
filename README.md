<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo-light.svg" alt="nette" width="96">
</picture>

# nette

**AI writes code. nette keeps it clean.**

A code readability checker for the AI-agent era. Deterministic, diff-aware,
calibrated on your codebase, fast enough to live inside the agent's
write-check-fix loop.

[![status](https://img.shields.io/badge/status-pre--release-f97316)](docs/vision.md)
[![python](https://img.shields.io/badge/python-%E2%89%A53.11-18181b)](pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-18181b)](LICENSE)
[![style](https://img.shields.io/badge/deps-zero-18181b)](pyproject.toml)

</div>

> [!NOTE]
> **Pre-release.** The engine, rules, calibration, and CLI work today from a
> source checkout. First PyPI release coming as v0.1.

## Why

AI agents now write most of the code. It works, but it is often hard to
read: too long, over-defensive, over-abstracted, inconsistent with the rest
of the repo. Classic linters like ruff and pylint check syntax and surface
style. They say nothing about readability or repo consistency, so debt
accumulates at machine speed.

nette lives in the agent loop: the agent writes code, runs nette, gets a
compact actionable verdict, fixes, re-checks. Like tests, but for
readability.

```
$ nette check src/api.py

warning[argument-count] src/api.py 1:1
  function `sync_users` takes too many arguments to call safely
  why: it takes 7 required arguments; the configured limit is 6
  fix: group related arguments into a dataclass, or split the function
```

Every finding names the problem, the reason, and the fix direction. No
bare numbers.

## Quickstart

```bash
git clone https://github.com/gausoft/nette && cd nette
pip install -e .

nette check                  # judge the current tree
nette check --diff           # judge only what changed (the agent loop)
nette calibrate              # learn this repo's style baseline
nette explain over-guarded   # long-form doc for any rule
```

In an agent loop, use the machine format:

```bash
nette check --diff --format agent
```

It emits a deterministic JSON envelope: summary counts, flat findings,
and a ready-to-act instruction per finding. Identical input produces
identical bytes, so agent runs cache and diff cleanly.

## Rules

Rule names say what they detect. No lookup tables.

| Family | Rule | Fires when |
|---|---|---|
| shape | `function-length` | a function is too long to take in at one glance |
| shape | `nesting-depth` | code nests too deeply to follow |
| shape | `argument-count` | a function takes too many required arguments |
| shape | `return-count` | a function exits from too many places |
| naming | `short-name-long-scope` | a one-letter name lives too long |
| naming | `naming-drift` | an identifier breaks the repo's own convention |
| defensiveness | `over-guarded` | a file guards far more than the rest of the repo |
| structure | `file-naming` | a file name breaks snake_case |
| structure | `file-size` | a file dwarfs the repo's norm |
| engine | `parse-error`, `bare-allow` | a file cannot be judged; a suppression has no reason |

Two threshold kinds, and the distinction is measured, not aesthetic. We
profiled five exemplary codebases (httpx, pydantic, fastapi, attrs, curated
stdlib): they agree tightly on code *shape* (median function: 8-13 lines,
2 arguments, near-flat nesting), so shape rules ship universal defaults.
The same codebases diverge up to 12x on *style* (comment density, guard
density, file size) while all being exemplary, so style rules compare your
code to your repo's own baseline (`nette calibrate`), never to an absolute.

Suppression is explicit and auditable:

```python
def decode_frame(raw):  # nette: allow(function-length) flat wire decoder, one case per opcode
```

The reason is mandatory. `nette allows` lists every suppression in the
tree.

## Configuration

One place: `[tool.nette]` in `pyproject.toml` (or `nette.toml`).

```toml
[tool.nette]
select = ["shape", "naming", "defensiveness", "structure"]
ignore = ["return-count"]
profile = "fastapi"        # exempts route endpoints from signature rules

[tool.nette.thresholds]
function_length = 60
nesting_depth = 4
```

## Promises

| # | Promise | Meaning |
|---|---------|---------|
| 1 | **Judges new code, not legacy** | Diff mode. A 10-year-old repo is never "all red". |
| 2 | **Calibrated on YOUR repo** | Learns the local style, flags deviations. No universal style imposed. |
| 3 | **Verdict in under a second** | Deterministic: same code, same verdict, zero LLM at runtime. |
| 4 | **Findings say what to do** | Not "complexity 12 > 9" but the problem, the reason, and the fix direction. |
| 5 | **Pure Python, zero deps** | `pip install nette` just works. nette's own code is the showcase. |
| 6 | **Extensible in 3 tiers** | Thresholds in TOML, pattern rules in YAML, deep rules in Python. |

## Not in scope

- Security ([bandit](https://github.com/PyCQA/bandit) exists), types
  ([mypy](https://github.com/python/mypy) exists), surface style
  ([ruff](https://github.com/astral-sh/ruff) exists).
- Multi-language support. Python only, done deeply. TypeScript comes later
  as a sibling product.
- LLM review. Deterministic or nothing.

## Documentation

- [Design: how nette works](docs/design.md)
- [Rules reference](docs/rules/README.md)
- [Vision & requirements](docs/vision.md)
- [Extensibility design](docs/extensibility.md)

## Contributing

Design feedback and issue reports are welcome. Code contributions open
after the v0.1 release; until then the surface moves fast.

Agents contributing here follow [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
