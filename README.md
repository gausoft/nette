<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/gausoft/nette/main/assets/logo-dark.svg">
  <img src="https://raw.githubusercontent.com/gausoft/nette/main/assets/logo-light.svg" alt="nette" width="96">
</picture>

# nette

**AI writes code. nette keeps it clean.**

A code readability checker for the AI-agent era. Deterministic, diff-aware,
calibrated on your repo's own style, fast enough to live inside the agent's
write-check-fix loop.

[![status](https://img.shields.io/badge/status-v0.1-f97316)](https://github.com/gausoft/nette/blob/main/CHANGELOG.md)
[![python](https://img.shields.io/badge/python-%E2%89%A53.11-18181b)](https://github.com/gausoft/nette/blob/main/pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-18181b)](https://github.com/gausoft/nette/blob/main/LICENSE)
[![style](https://img.shields.io/badge/deps-zero-18181b)](https://github.com/gausoft/nette/blob/main/pyproject.toml)

</div>

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
pip install nette

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

## Calibration, and why it only tightens

`nette calibrate` measures five style dimensions on your tree — annotation
rate, guard density, `try` density, camelCase leakage, file size p90 — and
writes them to `.nette/profile.json`, which you commit. Style rules then
judge new code against those numbers rather than against a universal ideal.
Other tools calibrate ceilings on code *size*; nette calibrates the style
an agent has to stay consistent with.

The profile is a ratchet. Recalibrating on a tree that has drifted keeps
the stricter of the two values per dimension, so a repo's baseline can
improve but never quietly rot:

```
$ nette calibrate
profile written to .nette/profile.json (964 files measured)
kept the stricter baseline for annotated_function_rate (--reset to relax)
```

Relaxing takes `nette calibrate --reset`, an explicit human act, visible in
the diff of the committed profile.

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
| engine | `parse-error`, `bare-allow`, `unused-allow` | a file cannot be judged; a suppression has no reason or silences nothing |

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
| 2 | **Calibrated on YOUR repo** | Learns the local style — annotations, guards, file size — and flags deviation. The baseline ratchets: it can tighten, never loosen by accident. |
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

## Known gaps in 0.1

- A dense flat `if/elif` chain passes under the length and nesting
  thresholds. Field testing found two such files. A branch-density rule is
  planned for 0.2.
- FastAPI is the only framework profile. Django and SQLAlchemy signatures
  are judged by the generic rules.
- The YAML pattern tier, external Python plugins, SARIF output and the MCP
  server are designed but not shipped.

## Documentation

- [Changelog](https://github.com/gausoft/nette/blob/main/CHANGELOG.md)
- [Design: how nette works](https://github.com/gausoft/nette/blob/main/docs/design.md)
- [Rules reference](https://github.com/gausoft/nette/blob/main/docs/rules/README.md)
- [Vision & requirements](https://github.com/gausoft/nette/blob/main/docs/vision.md)
- [Extensibility design](https://github.com/gausoft/nette/blob/main/docs/extensibility.md)

## Contributing

Design feedback and issue reports are welcome. Code contributions are open
from 0.1 on. Read [docs/design.md](https://github.com/gausoft/nette/blob/main/docs/design.md) first: a rule that does
not fit the three-tier engine or the calibration model will be declined on
shape, not on merit.

Agents contributing here follow [AGENTS.md](https://github.com/gausoft/nette/blob/main/AGENTS.md).

## License

[MIT](https://github.com/gausoft/nette/blob/main/LICENSE)
