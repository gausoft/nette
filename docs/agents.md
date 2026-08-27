# Agents

Code review does not scale to the volume an agent produces. What replaces
it is a set of constraints the agent has to pass, and each one has a
moment: before the work starts, while it is being done, and at the
boundary where the change tries to become production.

nette occupies one dimension of that set, comprehensibility, at all three
moments. The integration surface is a shell command and an exit code, so
every agent already supports it: Claude Code, Cursor, Copilot, Codex,
Aider, your CI. There is nothing to install on their side.

## Before: give the agent the rule

```bash
nette agent-rules >> AGENTS.md    # or CLAUDE.md, or .cursorrules
```

That writes the loop your agent has to follow: run
`nette check --diff --format agent` after editing Python, read the exit
code, fix, rerun. It also states the two things an agent otherwise
invents, that a suppression needs a written reason, and that the check is
never to be silenced to make a run pass.

The committed profile does the rest of the framing. It is the repository
telling the agent what normal looks like here, in numbers, before a line
is written.

## During: the feedback the agent acts on

```bash
nette check --diff --format agent
```

The verdict lands in under a second on a warm cache and covers only the
lines that changed, so the loop stays tight enough to run on every edit.

Measured on twelve flagged files from five public repositories, handed to
a model with nothing but this output: all twelve reached zero findings,
eleven of them in a single turn, none of the loops oscillated, and no
public function or parameter was lost. The numbers and their limits are in
[benchmark.md](benchmark.md).

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Clean, nothing to fix. |
| `1` | Findings on stdout, fix them and rerun. |
| `2` | nette could not run, read stderr. |

### The machine envelope

`--format agent` emits JSON that carries its own contract, so an agent that
never read a line of documentation still knows what to do with it.

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

The envelope was tested on an agent given no documentation at all: it
produced the correct refactor from the JSON alone. The `run` block exists
because the same test showed it had to guess how to rerun the check and
whether a warning was blocking.

Identical input produces identical bytes, so agent runs cache and diff
cleanly.

## At the boundary: the gate that does not depend on memory

An agent that forgets to run the check is the normal case. The constraint
that holds is the one it cannot skip.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gausoft/nette
    rev: v0.2.1
    hooks:
      - id: nette
```

```yaml
# .github/workflows/nette.yml
- run: pip install nette
- run: nette check --diff origin/main --format sarif > nette.sarif
  continue-on-error: true
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: nette.sarif
```

SARIF puts the findings in the pull request instead of in a log nobody
opens, and the document is deterministic, so code scanning stops reporting
the same finding as new on every push. The full CI setup, including the
`continue-on-error` the upload needs, is in
[configuration.md](configuration.md).

## The other formats

| Format | For |
|---|---|
| `--format full` | Humans at a terminal. The default. |
| `--format concise` | CI logs, one line per finding. |
| `--format agent` | The JSON envelope above. |
| `--format sarif` | GitHub code scanning. |
| `--format summary` | Where the debt lives on a large tree. |

```
$ nette check --format summary

127 findings in 42 files

services/accounts  87 findings in 24 files
  http_client.py  9
  serializers.py  6
  filters.py  4
```

## Where to relax

Every gate creates back-pressure, and a gate that fires on everything gets
turned off. Three levers, in the order to reach for them.

`--diff` judges the lines that changed, so a legacy tree never lights up
at once. `ignore` drops a rule or a whole family in `pyproject.toml`, which
is the right move when a rule does not match how your repository works. A
suppression marker with a written reason handles the single case, and
`nette allows` lists every one of them in the tree.

## Why no MCP server

An MCP server would expose nothing the shell does not already expose, and
every agent has a shell. The design note is in [design.md](design.md).
