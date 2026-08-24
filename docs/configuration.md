# Configuration

One place: `[tool.nette]` in `pyproject.toml`, or `nette.toml` if you prefer
a separate file.

```toml
[tool.nette]
select = ["shape", "naming", "defensiveness", "structure"]
ignore = ["return-count"]
profile = "fastapi"        # exempts route endpoints from signature rules

[tool.nette.thresholds]
function_length = 60
nesting_depth = 4
```

`select` takes rule families, `ignore` takes families or single rule slugs.
The families are listed in the [rules reference](rules/README.md).

## How the config is found

nette walks up from the paths you check, so running it from a subdirectory
or on a path outside the current directory finds the same configuration and
the same `.nette/profile.json`. `--profile PATH` points at another profile
file, for CI and multi-root setups.

## Suppression

Put `# nette: allow(rule-slug) reason` on the offending line or the line
above.

```python
def decode_frame(raw):  # nette: allow(function-length) flat wire decoder, one case per opcode
```

The reason is mandatory. A suppression without one is itself a finding
(`bare-allow`), and one that silences nothing is another (`unused-allow`).
`nette allows` lists every suppression in the tree.

## In CI

```yaml
# .github/workflows/nette.yml
- run: pip install nette
- run: nette check --diff origin/main --format concise
```

## Before every commit

The most reliable integration does not depend on the agent remembering.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gausoft/nette
    rev: v0.2.1
    hooks:
      - id: nette
```

An agent whose commit is rejected learns to run the check itself. That is
how black and ruff became habits.

## Framework profiles

`profile = "fastapi"` exempts route endpoints from the signature rules: a
FastAPI handler declares its dependencies as parameters, so `argument-count`
would fire on correct code. FastAPI is the only framework profile so far.
Django and SQLAlchemy signatures are judged by the generic rules.
