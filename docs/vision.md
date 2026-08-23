# Vision & Requirements

## Problem

AI agents write most code today. It works but is often illegible: too long,
over-defensive, over-abstracted, inconsistent with the surrounding repo.
Existing linters check syntax and surface style, not readability or local
consistency. Technical debt now accumulates at machine speed.

## Solution

A readability tool that lives inside the agent loop: write,
check, fix, re-check. Deterministic, sub-second, diff-aware, calibrated on
the target repository.

## Primary audience

Teams coding with AI agents (Claude Code, Cursor, Copilot and friends), from
solo developers to large-scale engineering organizations.

## Success metric (v1)

On a real production backend: an agent using nette produces code the
maintainer judges readable without line-by-line review, and the repo's global
score can no longer degrade (ratchet effect).

## Market gaps nette targets

A 2026 survey of existing tools (kiss, agent-slop-lint, lipstyk, eigenhelm,
radon, lizard) identified four open gaps:

1. **Size metrics are not readability.** Nobody measures naming quality,
   local pattern consistency, defensive-code smell or narrative comments,
   which are the things that actually make AI code painful.
2. **No framework awareness.** Nothing understands FastAPI, Pydantic or
   SQLAlchemy idioms. A tool focused on one language can go deep here.
3. **No local-style calibration.** No tool learns a repo's conventions and
   flags deviation from them. This is nette's core differentiator.
4. **Poor DX.** No diff mode in kiss, rudimentary visualization everywhere,
   no output designed for agent consumption.
5. **Nothing looks above the file.** All tools stop at file boundaries.
   Project structure (file size norms, file naming conventions, folder
   depth, where a new file belongs) is unmeasured, and it is precisely
   where AI agents drift (catch-all 800-line files, `utils2.py`, files
   dropped in the wrong folder). Repo calibration applies here too: learn
   the repo's structural signature, flag new files that deviate.

## Key design lessons (from ecosystem research)

- Extensibility is what makes a tool win (ESLint's 2,900 plugins vs Biome).
- ruff's plugin issue (#283) has been open since 2022, blocked by its Rust
  core. Pure Python resolves this structurally.
- Single AST shared by all rule tiers (avoid the two-parser trap).
- Explicit opt-in for plugins (avoid flake8's auto-activation trap).
- Per-rule timing exposed to the user (avoid silent slow-rule rot).
- The declarative tier stays declarative. No shell escape hatches (security).

## Roadmap phases

### Research

- **Phase 0**: Vision & requirements (this document). Done.
- **Phase 1**: Foundations research: how ruff, uv and pydantic-core achieve
  performance; tree-sitter vs stdlib ast; mypyc and Cython options; state of
  the art in metrics. Done: stdlib `ast` + `tokenize`, file-level result
  cache, single-pass rule engine, mypyc-friendly core, repo-calibrated
  detections over absolute scores.
- **Phase 2**: "Beautiful code" benchmarking: extract measurable patterns
  from exemplary Python codebases (CPython stdlib, FastAPI, pydantic, httpx,
  attrs). Scientific basis for the rules. Done: two threshold families
  (universal shape metrics with benchmark-derived defaults; repo-calibrated
  style metrics), scope-aware naming rule, FastAPI-aware profile from v1. Done: universal thresholds
  (function length, nesting, args, returns) vs repo-calibrated dimensions
  (annotations, docstrings, comments, defensiveness); framework awareness
  proven necessary by FastAPI's endpoint signatures.
- **Phase 3**: DX & visualization research: error output design (ruff, elm,
  rust), TUI (rich/textual), agent-oriented output formats. Done: one
  diagnostic model feeding every renderer (human in the Elm/rustc style,
  agent output that is signal-only, deterministic and carries a composed
  instruction per finding,
  SARIF deferred to v0.2), stable rule codes with `--explain`, calibrated
  findings show the repo baseline in the message, affirmative suggestions
  with confidence levels, tested finding catalog with golden outputs.

### Design

- **Phase 4**: Design doc: architecture (engine, rule tiers, calibration,
  cache), public API surface, output formats (human and agent), config
  schema, v0.1 scope cut. Reviewed before any implementation starts.
  Done: [design.md](design.md), reviewed and frozen for v0.1.

### Implementation

TDD throughout: each step starts with failing tests, ends green. Every
phase preserves the two core invariants: extensible (three rule tiers,
single shared AST) and fast (diff-aware, file-level cache, single pass).

- **Phase 5**: Core engine: file discovery, `ast` + `tokenize` parsing,
  rule runner, diagnostics model. The minimal loop: files in, findings out.
  Done: five modules (discovery, parsing, engine, findings, rules.base),
  syntax and encoding errors become findings instead of crashes.
- **Phase 6**: First rule set: the universal-threshold rules from Phase 2
  (function length, nesting depth, argument count, returns per function).
  Done: the four shape rules, defaults validated against the exemplary
  corpus (docstrings excluded from length, only required arguments counted).
- **Phase 7**: Calibration: `nette calibrate` produces the repo profile;
  calibrated rules judge deviation from it. Done: versioned
  `.nette/profile.json` and `over-guarded` (over-defensiveness vs repo
  baseline).
  Percentile profiles (p50/p90/p99) deferred until more calibrated rules
  need them.
- **Phase 8**: Diff-aware mode and file-level result cache: judge only
  changed code, re-runs near-free. Done: cache keyed on content, config,
  profile and version, corrupt entries self-heal; `--diff [REF]` in the CLI.
- **Phase 9**: Extensibility tiers: TOML thresholds done (strict key and
  type validation, `nette.toml` precedence). YAML declarative patterns and
  external Python plugin loading deferred to v0.2 (the rule API they will
  use already exists and is dogfooded by every built-in rule).
- **Phase 10**: Output & integration: agent-oriented output, human CLI
  output, framework profiles. Done: four renderers (concise, full, agent,
  json) and `nette check` / `nette calibrate` with `--fail-on`. MCP server
  deferred to v0.2. Remaining for v0.1: suppressions with `nette allows`,
  `nette explain`, `--timings`, FastAPI profile.

### Release

- **Phase 11**: Prototype on a real production codebase; fix what reality
  breaks. Done: 964-file FastAPI monorepo. Calibration 1.7s, full check
  3.1s cold / 0.17s warm. 127 findings, zero crashes, zero endpoint false
  positives. Cross-checked against 12 months of git fix-churn: 9 of the 15
  most bug-fixed files flagged; 4 of the 6 missed are structurally sound
  (churn from product change, silence correct). Two v0.2 candidates born
  from the field: branch-density rule (flat if/elif chains evade length
  and nesting thresholds) and churn-weighted hotspots.
- **Phase 12**: v0.1 on PyPI: packaging, docs, benchmark numbers published.

### v0.2 candidates (from field testing)

- Branch-density rule: decisions per function, orthogonal to length and
  nesting. Target: dense flat converter/driver files.
- Churn-weighted hotspots: cross findings with git history; a borderline
  file that changes weekly outranks one never touched.
- Per-service/folder aggregated view: field findings clustered heavily by
  service; the report should surface that shape.

### v0.2 candidates (from the cross-language survey, 23 August 2026)

Surveyed the reference linter of fifteen languages (see
`docs/private/cross-language-competitors-2026-08.md`). Four gaps worth
closing, each with the prior art that exposed it.

- Profile as agent context: emit the calibrated profile as a block an
  agent reads before writing (`nette profile --format agent`, pasteable
  into AGENTS.md, later served over MCP). A whole category now exists to
  derive repo conventions and feed them to agents (Codehabits, chameleon,
  style-dna), non-deterministic and verdict-less. We already compute the
  numbers; only the formatter is missing. Puts nette on both sides of the
  loop: prevention, then verdict.
- Line-level diff, with `--whole-files` to opt out. `changed_files()` is
  file-granular today, so touching one line of an old file can light it up
  entirely, which contradicts promise 1. golangci-lint hit exactly this and
  defaults to changed lines with `--whole-files` as the escape hatch. Our
  merge-base handling already matches their recommended setup.
- Generalise framework awareness into config: `exempt_decorated_by`, a
  list of decorators whose signatures are out of the author's control.
  Checkstyle solves the same problem with `ignoreAnnotatedBy` on
  `ParameterNumber`. Closes the "FastAPI is the only profile" gap without
  shipping a profile per framework (Django, SQLAlchemy, Celery, click).
- File-level aggregate threshold, to arbitrate against branch-density: PMD
  reports a class once the sum of its method complexities reaches 80, even
  when no single method exceeds its own limit. That is the shape of the
  flat `if/elif` miss found in the field: not one function overflowing but
  a file dying of a thousand cuts. Decide which of the two rules ships,
  or whether the aggregate subsumes the per-function one.

Two calibrated rule candidates from the same survey, lower priority:
docstring-style consistency (Google, NumPy and reST mixed in one repo;
already a listed calibration dimension, not yet a rule) and exception
naming convention. Both mirror Credo's Consistency checks, the only
majority-wins mechanism found in any language.

Rejected on purpose, with the reason: a detekt-style baseline (diff mode
replaces it, and it freezes debt), a maintainability index (CA1505,
`maintidx`: the bare number the tool refuses on principle), and
warning/error severity tiers (SwiftLint): configuration surface, no gain.
