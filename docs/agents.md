# Agents

nette's primary audience is the agent writing the code, not the human
reviewing it later. The integration surface is a shell command and an exit
code, so every agent already supports it: Claude Code, Cursor, Copilot,
Codex, Aider, your CI. There is nothing to install on their side.

## Wire the loop once

```bash
nette agent-rules >> AGENTS.md    # or CLAUDE.md, or .cursorrules
```

That writes the loop your agent has to follow: run
`nette check --diff --format agent` after editing Python, read the exit
code, fix, rerun.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Clean, nothing to fix. |
| `1` | Findings on stdout, fix them and rerun. |
| `2` | nette could not run, read stderr. |

## The machine envelope

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

## The other formats

| Format | For |
|---|---|
| `--format full` | Humans at a terminal. The default. |
| `--format concise` | CI logs, one line per finding. |
| `--format agent` | The JSON envelope above. |
| `--format summary` | Where the debt lives on a large tree. |

```
$ nette check --format summary

127 findings in 42 files

services/accounts  87 findings in 24 files
  http_client.py  9
  serializers.py  6
  filters.py  4
```

## Why no MCP server

An MCP server would expose nothing the shell does not already expose, and
every agent has a shell. The design note is in
[design.md](design.md).
