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

[![status](https://img.shields.io/badge/status-v0.2-f97316)](https://github.com/gausoft/nette/blob/main/CHANGELOG.md)
[![python](https://img.shields.io/badge/python-%E2%89%A53.11-18181b)](https://github.com/gausoft/nette/blob/main/pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-18181b)](https://github.com/gausoft/nette/blob/main/LICENSE)
[![style](https://img.shields.io/badge/deps-zero-18181b)](https://github.com/gausoft/nette/blob/main/pyproject.toml)

</div>

<br>

## Contents

- [Why](#why)
- [Quickstart](#quickstart)
- [In your agent's loop](#in-your-agents-loop)
- [Calibrated on your repo](#calibrated-on-your-repo)
- [Rules](#rules)
- [Configuration](#configuration)
- [Where the pain actually is](#where-the-pain-actually-is)
- [What nette does not do](#what-nette-does-not-do)
- [Documentation](#documentation)

<br>

## Why

AI agents now write most of the code. It works, and it is often hard to
read: too long, over-defensive, over-abstracted, inconsistent with the rest
of the repo. Linters like ruff and pylint check syntax and surface style.
They say nothing about readability or repo consistency, so debt accumulates
at machine speed.

nette lives in the agent loop. The agent writes code, runs nette, gets a
compact verdict, fixes, re-checks. Like tests, but for readability.

```
$ nette check src/api.py

warning[argument-count] src/api.py 1:1
  function `sync_users` takes too many arguments to call safely
  why: it takes 7 required arguments; the configured limit is 6
  fix: group related arguments into a dataclass, or split the function
```

Every finding names the problem, the reason, and the fix direction. No bare
numbers.

<br>

## Quickstart

```bash
pip install nette
```

Python 3.11 or later, zero dependencies, nothing else lands in your
environment.

```bash
nette init                   # calibrate the repo, ignore the cache, print the next step
nette check                  # judge the current tree
nette check --diff           # judge only the lines you touched
nette explain over-guarded   # long-form doc for any rule
```

`--diff` is the one that matters day to day: it judges the lines you
touched, not the files you touched, so a 10-year-old repo is never all red.

<details>
<summary><b>All commands</b></summary>

<br>

| Command | What it does |
|---|---|
| `nette init` | Calibrate, ignore the cache, print the next step. Once per repo. |
| `nette check` | Judge the current tree. |
| `nette check --diff` | Judge only what changed. |
| `nette calibrate` | Measure the repo's style, write `.nette/profile.json`. |
| `nette explain RULE` | Long-form documentation for any rule slug. |
| `nette allows` | List every suppression in the tree, with its reason. |
| `nette hotspots` | Rank findings by how often the file changes. |
| `nette agent-rules` | Print the loop to append to AGENTS.md. |

</details>

<br>

## In your agent's loop

The integration surface is a shell command and an exit code, so every agent
already supports it: Claude Code, Cursor, Copilot, Codex, Aider, your CI.
There is nothing to install on their side.

```bash
nette agent-rules >> AGENTS.md    # or CLAUDE.md, or .cursorrules
```

That writes the loop the agent follows: run
`nette check --diff --format agent` after editing Python, read the exit
code, fix, rerun.

| Exit code | Meaning |
|---|---|
| `0` | Clean, nothing to fix. |
| `1` | Findings on stdout, fix them and rerun. |
| `2` | nette could not run, read stderr. |

`--format agent` emits JSON that carries its own contract: how to rerun,
what each exit code means, how to suppress. An agent given the envelope and
no documentation at all produced the correct refactor from the JSON alone.
Identical input produces identical bytes, so agent runs cache and diff
cleanly.

**→ [The envelope, the other formats, and why there is no MCP server](docs/agents.md)**

<br>

## Calibrated on your repo

Five exemplary codebases diverge up to 12x on style while all being
exemplary. An absolute threshold would be wrong for four of them. So
`nette calibrate` measures your tree (annotation rate, guard density, `try`
density, camelCase leakage, file size p90) and commits the numbers to
`.nette/profile.json`. Style rules judge new code against that, never
against a universal ideal.

```
$ nette calibrate
profile written to .nette/profile.json (964 files measured)
kept the stricter baseline for annotated_function_rate (--reset to relax)
```

The profile is a ratchet. Recalibrating on a tree that has drifted keeps the
stricter value per dimension, so a baseline can improve and never quietly
rot. A monorepo can give one subtree its own baseline with
`nette calibrate services/adapters --local`, and every file is then judged
against the nearest profile.

**→ [What gets measured, the ratchet, and the monorepo case](docs/calibration.md)**

<br>

## Rules

Rule names say what they detect. An agent reading a finding knows what to do
without a round-trip to the docs.

| Family | Rules | Threshold |
|---|---|---|
| `shape` | function length, branch density, nesting, arguments, returns | universal |
| `naming` | short names in long scopes, drift from the repo's convention | mixed |
| `defensiveness` | files that over-guard, functions that stack guards | calibrated |
| `annotations` | files that drop the annotations the repo keeps | calibrated |
| `structure` | file naming, file size, data types mixed into logic | mixed |
| `duplication` | a function that is a near-copy of a sibling | convention |
| `engine` | unparsable files, suppressions with no reason or no effect | none |

Universal thresholds ship as numbers because exemplary codebases agree on
code shape. Calibrated ones compare a file to your profile. Convention rules
never read the profile: on a production monorepo 82% of data types already
lived mixed with behaviour, so a calibrated `mixed-module` would have gone
silent on exactly the debt it exists to catch.

**→ [All fifteen rules, one page per family](docs/rules/README.md)**

<br>

## Configuration

One place: `[tool.nette]` in `pyproject.toml`, or `nette.toml`.

```toml
[tool.nette]
select = ["shape", "naming", "defensiveness", "structure"]
ignore = ["return-count"]

[tool.nette.thresholds]
function_length = 60
```

Suppression is explicit and auditable. The reason is mandatory, and
`nette allows` lists every one in the tree.

```python
def decode_frame(raw):  # nette: allow(function-length) flat wire decoder, one case per opcode
```

**→ [Config discovery, framework profiles, CI and pre-commit](docs/configuration.md)**

<br>

## Where the pain actually is

A file that is structurally borderline and changes every week costs more
than a file that is borderline and never touched.

```
$ nette hotspots --since 12.months

changes  findings  file
     37         9  services/accounts/api/http_client.py
     18         6  services/accounts/serializers.py
```

It is a separate command on purpose. Git history is environment state, and
`nette check` stays a pure function of the code, the config and the profile.
Hotspots only rank, never change a severity, and always exit 0.

<br>

## What nette does not do

- **Security, types, surface style.** [bandit](https://github.com/PyCQA/bandit),
  [mypy](https://github.com/python/mypy) and [ruff](https://github.com/astral-sh/ruff)
  already do those. Run them alongside.
- **Other languages.** Python only, done deeply. TypeScript comes later as a
  sibling product.
- **LLM review.** Deterministic or nothing.
- **Not shipped yet.** The YAML pattern tier, external Python plugins and
  SARIF output are designed but not built. FastAPI is the only framework
  profile.

<br>

## Documentation

| | |
|---|---|
| [Agents](docs/agents.md) | The envelope, output formats, exit codes |
| [Calibration](docs/calibration.md) | The profile, the ratchet, monorepos |
| [Configuration](docs/configuration.md) | Config, suppression, CI, pre-commit |
| [Rules reference](docs/rules/README.md) | Every rule, with its threshold kind |
| [Design](docs/design.md) | How the engine works |
| [Benchmark](docs/benchmark.md) | Speed, thresholds, field results |
| [FAQ](docs/faq.md) | What nette does not do, and the experiments that say so |
| [Vision](docs/vision.md) | The research behind every choice |
| [Changelog](CHANGELOG.md) | What shipped when |

<br>

## Contributing

Design feedback and issue reports are welcome. Code contributions are open
from 0.1 on. Read [docs/design.md](docs/design.md) first: a rule that does
not fit the three-tier engine or the calibration model will be declined on
shape, not on merit. Agents contributing here follow [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
