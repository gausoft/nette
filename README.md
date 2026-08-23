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

nette init                   # calibrate the repo, ignore the cache, print the next step
nette check                  # judge the current tree
nette check --diff           # judge only what changed (the agent loop)
nette explain over-guarded   # long-form doc for any rule
```

## Any agent, no plugin

The integration surface is a shell command and an exit code, so every
agent already supports it: Claude Code, Cursor, Copilot, Codex, Aider,
your CI. There is nothing to install on their side.

```bash
nette agent-rules >> AGENTS.md    # or CLAUDE.md, or .cursorrules
```

That writes the loop your agent has to follow: run
`nette check --diff --format agent` after editing Python, read the exit
code, fix, rerun.

The machine format carries its own contract, so an agent that never read
a line of documentation still knows what to do:

```json
{
  "schema_version": 2,
  "run": {
    "rerun": "nette check --diff --format agent",
    "exit": {
      "0": "clean, nothing to fix",
      "1": "findings below, fix them and rerun",
      "2": "nette could not run, read stderr"
    },
    "suppress": "# nette: allow(CODE) reason (...)",
    "explain": "nette explain CODE"
  },
  "summary": { "total": 1, "by_severity": { "error": 0, "warning": 1, "info": 0 } },
  "findings": [
    {
      "code": "duplicated-sibling",
      "file": "src/notify.py",
      "line": 25,
      "message": "`send_email_change` is a near-copy of `send_password_reset` in the same scope",
      "instruction": "warning: ... To resolve: edit src/notify.py:25 - extract what they share into one function and pass what differs as arguments."
    }
  ]
}
```

That envelope was tested on an agent given no documentation at all: it
produced the correct refactor from the JSON alone. The `run` block exists
because the same test showed it had to guess how to rerun the check and
whether a warning was blocking.

Identical input produces identical bytes, so agent runs cache and diff
cleanly.

On a large tree, `--format summary` answers a different question: where
the debt lives.

```
$ nette check --format summary

127 findings in 42 files

services/accounts  87 findings in 24 files
  http_client.py  9
  serializers.py  6
  filters.py  4
```

## Calibration, and why it only tightens

`nette calibrate` measures five style dimensions on your tree (annotation
rate, guard density, `try` density, camelCase leakage, file size p90) and
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
| shape | `branch-density` | a function makes too many branching decisions |
| shape | `nesting-depth` | code nests too deeply to follow |
| shape | `argument-count` | a function takes too many required arguments |
| shape | `return-count` | a function exits from too many places |
| naming | `short-name-long-scope` | a one-letter name lives too long |
| naming | `naming-drift` | an identifier breaks the repo's own convention |
| defensiveness | `over-guarded` | a file guards far more than the rest of the repo |
| structure | `file-naming` | a file name breaks snake_case |
| structure | `file-size` | a file dwarfs the repo's norm |
| structure | `mixed-module` | data types pile up in a module that also holds logic |
| duplication | `duplicated-sibling` | a function is a near-copy of a sibling function |
| engine | `parse-error`, `bare-allow`, `unused-allow` | a file cannot be judged; a suppression has no reason or silences nothing |

Two threshold kinds, and the distinction is measured, not aesthetic. We
profiled five exemplary codebases (httpx, pydantic, fastapi, attrs, curated
stdlib): they agree tightly on code *shape* (median function: 8-13 lines,
2 arguments, near-flat nesting), so shape rules ship universal defaults.
The same codebases diverge up to 12x on *style* (comment density, guard
density, file size) while all being exemplary, so style rules compare your
code to your repo's own baseline (`nette calibrate`), never to an absolute.

A third kind never touches the profile: *convention* rules, for a decision
a repo makes once and then has to keep (whether the same function may exist
twice, where a type belongs). Calibrating those would teach the tool that
the drift is the house style. Measured on a production monorepo: 82% of its
data types already lived mixed with behaviour, so a calibrated rule would
have gone silent on exactly the debt it exists to catch.

Suppression is explicit and auditable:

```python
def decode_frame(raw):  # nette: allow(function-length) flat wire decoder, one case per opcode
```

The reason is mandatory. `nette allows` lists every suppression in the
tree.

## Configuration

One place: `[tool.nette]` in `pyproject.toml` (or `nette.toml`). nette looks
for it by walking up from the paths you check, so running it from a
subdirectory or on a path outside the current directory finds the same
configuration and the same `.nette/profile.json`. `--profile PATH` points at
another profile file, for CI and multi-root setups.

```toml
[tool.nette]
select = ["shape", "naming", "defensiveness", "structure"]
ignore = ["return-count"]
profile = "fastapi"        # exempts route endpoints from signature rules

[tool.nette.thresholds]
function_length = 60
nesting_depth = 4
```

## In CI, and before every commit

The most reliable integration does not depend on the agent remembering.

```yaml
# .github/workflows/nette.yml
- run: pip install nette
- run: nette check --diff origin/main --format concise
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: nette
        name: nette
        entry: nette check --diff
        language: system
        pass_filenames: false
```

An agent whose commit is rejected learns to run the check itself. That is
how black and ruff became habits.

## Promises

| # | Promise | Meaning |
|---|---------|---------|
| 1 | **Judges new code, not legacy** | Diff mode. A 10-year-old repo is never "all red". |
| 2 | **Calibrated on YOUR repo** | Learns the local style (annotations, guards, file size) and flags deviation. The baseline ratchets: it can tighten, never loosen by accident. |
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

## Known gaps

- FastAPI is the only framework profile. Django and SQLAlchemy signatures
  are judged by the generic rules.
- One profile per repository. A monorepo whose boundary modules guard for
  good reasons has no way to give them their own baseline yet.
- The YAML pattern tier, external Python plugins and SARIF output are
  designed but not shipped. An MCP server is not planned: it would expose
  nothing the shell does not already expose, and every agent has a shell.

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
