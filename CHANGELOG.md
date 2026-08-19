# Changelog

## 0.1.0

First release. A readability checker for Python that runs inside the agent
loop: deterministic, diff-aware, calibrated on the repo it judges.

### Rules

Rules are named, never numbered. A published name is never renamed.

- shape: `function-length`, `nesting-depth`, `argument-count`,
  `return-count`. Universal defaults derived from five exemplary codebases
  (httpx, pydantic, fastapi, attrs, curated stdlib).
- naming: `short-name-long-scope`, `naming-drift`.
- defensiveness: `over-guarded`, judged against the repo's own guard density.
- structure: `file-naming`, `file-size`.
- engine: `parse-error`, `bare-allow`.

### Commands

- `nette check [PATHS]` with `--diff [REF]`, `--fail-on`, `--timings`,
  `--no-cache`, and four output formats (concise, full, agent, json).
- `nette calibrate` writes `.nette/profile.json`, the repo style baseline.
  Re-calibrating keeps the stricter side of every metric, so the baseline
  cannot drift looser by accident. `--reset` accepts the new measure as is.
- `nette allows` lists every suppression and its reason.
- `nette explain RULE` prints the long-form doc for a rule.

### Behaviour

- Suppression through `# nette: allow(rule) reason`. The reason is
  mandatory; a bare marker is itself a finding.
- Per-file result cache keyed on content, config, profile and version.
  Corrupt entries are discarded instead of raising.
- Config in `[tool.nette]` of `pyproject.toml` or in `nette.toml`, with
  strict key and type validation. An unknown rule name is refused with the
  closest match suggested; a malformed file names itself. Config mistakes
  are diagnostics on stderr with exit code 2, never tracebacks.
- `profile = "fastapi"` exempts route endpoints from signature rules.
- Syntax and encoding errors become findings, never crashes.

### Measured

On a 964-file FastAPI monorepo: calibration 1.7 s, full check 3.1 s cold
and 0.17 s warm, 127 findings, zero endpoint false positives. Cross-checked
against 12 months of fix commits, nette flagged 9 of the 15 most-fixed
files.

### Known gaps

- Dense flat `if/elif` chains pass under the length and nesting thresholds.
  A branch-density rule is planned for 0.2.
- FastAPI is the only framework profile. Django and SQLAlchemy signatures
  are judged by the generic rules.
- The YAML pattern tier, external Python plugins, SARIF output and the MCP
  server are designed but not shipped.
