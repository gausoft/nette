# Changelog

## Unreleased

### Added

- `branch-density`, the rule for the gap 0.1 shipped with: a long flat
  `if/elif` chain passes under `function-length` and `nesting-depth` while
  being the least readable thing in the file. A decision is an `if`, an
  `elif`, a `match` case or a ternary; boolean operators do not count, and
  branches of a nested function belong to it. Default `branch_density` 12,
  measured against the exemplary corpora: p99 is 8 to 16, and the default
  fires on 1.1% of stdlib functions.
- `mixed-module`, a convention rule for data types piling up in a module
  that also holds behaviour. A module declaring at least
  `data_types_per_module` (default 2) pure data types beside a function or a
  class with methods is flagged, and the message names the destination.
  Destination modules (`schemas.py`, `models.py`, `enums.py` and friends) and
  private classes are exempt. Measured: 3.5% of a 879-file monorepo, 6
  findings across 642 stdlib modules.
- `check --profile PATH` judges against a profile file of your choosing,
  for CI and multi-root setups.
- `duplicated-sibling`, a rule for the blind spot that matters most on
  agent-written code: a function that is a near-copy of another function in
  the same scope. Each function is reduced to the sequence of its AST node
  types, docstring excluded, and compared to its siblings; names, literals
  and attribute paths do not count. Defaults `duplication_similarity` 85
  (percent) and `duplication_min_lines` 20. Measured on a 879-file monorepo:
  37 near-copy pairs in 12 files, in files where every other rule scored
  zero. Quiet on exemplary code: 15 findings across 642 stdlib modules.

### Fixed

- Configuration, profile and cache are resolved by walking up from the paths
  under check to the nearest project root (`nette.toml`, `pyproject.toml`,
  `.nette` or `.git`), instead of being read from the current directory.
  Checking a path in another worktree used to silently use the caller's
  profile, or none, which meant copying `.nette/profile.json` by hand into
  every worktree. `calibrate` writes at that same root.
- A threshold below 1 is refused, and a percentage threshold above 100 is
  refused. `duplication_similarity = 150` used to disable the rule in silence.
- `check` refuses a path that does not exist, instead of walking nothing and
  exiting 0. A typo used to look like a clean tree.
- `check` refuses paths belonging to different projects in one run, instead of
  judging all of them with the first path's configuration.
- `--profile PATH` pointing at a missing file is refused, instead of running
  with no profile at all.

## 0.1.1

Fixes from a field test on a production FastAPI monorepo (879 files, 7
services). They all concern trust in the tool: a diff that reported files the
branch never touched, and suppressions that stopped working without saying so.

### Fixed

- `check --diff REF` computes the file set against `git merge-base REF HEAD`
  instead of the tip of `REF`. A branch is no longer judged on files that
  moved on the base branch since the branch point. Measured on a two-week-old
  branch of a 879-file monorepo: 103 files reported before, 21 after.
  Uncommitted work stays in the set, so the write-check-fix loop is unchanged.
- `check --diff` resolves paths from the git root (`git rev-parse
  --show-toplevel`) instead of the current directory, so running it from a
  subdirectory no longer produces paths that do not exist. When `REF` shares no
  history with `HEAD`, the run falls back to the tip of `REF` and says so on
  stderr.
- A suppression marker for a file-scoped rule (`file-size`, `file-naming`,
  `over-guarded`, `naming-drift`) is accepted anywhere in the file. Those
  findings anchor on whichever construct comes first, so adding an import
  used to move the anchor and silently break the marker.
- A suppression marker is read from comment tokens only. `# nette: allow(...)`
  written inside a string literal no longer counts as a suppression.

### Added

- engine: `unused-allow`, a warning for a suppression marker that silences
  nothing. Markers naming a rule the current configuration does not run, or a
  calibrated rule whose baseline is absent from the profile, are left alone.
- `Rule.baseline` names the profile metric a calibrated rule reads, so the
  engine knows which rules can fire on the current profile.

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
