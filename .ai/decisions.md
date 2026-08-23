# Decisions

Short records of choices already made. Read before questioning a past
choice; append a new entry when a significant choice is made.

## 001: Pure Python implementation

Rust-based tools (ruff) cannot offer a plugin API their users can write
(issue astral-sh/ruff#283, open since 2022). nette's users are Python
developers; they extend it in Python. Performance targets are met through
architecture (caching, incremental analysis, parallelism), not language.

## 002: Deterministic runtime, no LLM

LLM reviewers are non-reproducible and share the generator's blind spots.
A check that gives different verdicts on the same code cannot gate a
commit. LLMs may appear in optional, clearly separated layers later, never
in the check path.

## 003: Diff-aware by default

Legacy codebases would be "all red" under whole-repo judgment, which kills
adoption and buries the signal. The unit of judgment is the change.
Whole-repo analysis serves calibration and audit.

## 004: Three-tier extensibility

TOML for thresholds, YAML for declarative patterns, Python for deep rules.
Modeled on what worked (ESLint plugins, semgrep rule registry) while
avoiding known traps: flake8's silent plugin activation, ESLint's config
maze, the two-parser incoherence.

## 005: Python first, one language at a time

Depth beats breadth: framework-aware rules (FastAPI, Pydantic, SQLAlchemy)
require deep single-language investment. Other languages come later as
sibling products, not as a shallow multi-language mode. Scope is stated
once in the README; the product identity is the mission, not the language.

## 006: Prose quality is part of the product

A tool that fights AI slop in code cannot ship AI slop in prose. Writing
rules live in writing.md and apply to every sentence in the repository.

## 007: stdlib ast as the parser

Measured on 3,131 files (~4.2M nodes): CPython `ast` parses at 89 files/s
vs 48 for tree-sitter-python (which also failed one file) and 13 for
LibCST. mypy's own parser research reached the same conclusion: tree-sitter
is too slow to justify. `ast` is hand-optimized C, always current with the
Python grammar, and honors the zero-dependency promise. tree-sitter only
pays off for intra-file incremental parsing (LSP case, not v1).

## 008: single-pass engine with cache and multiprocessing

ruff's speed comes from architecture, not just Rust: read each file once,
parse once, run every rule over the same tree in one traversal. flake8 is
slow because each plugin re-parses. Pipeline: git diff selects files, a
per-file cache (content hash + config version) skips unchanged ones,
remaining files are analyzed in multiprocessing workers (threads lose to
the GIL on CPU-bound work; a documented case got 17x by switching to fork
processes and deleting redundant parses). Diff mode plus cache makes the
nominal agent case (2-3 edited files) far below the 1-second budget.

## 009: mypyc is a future option, never a foundation

mypyc breaks Python stack traces and complicates packaging. Documented
pure-Python wins (pylint fast-path checks, custom ast.walk) show 2-200x
gains are available first. Compilation may come later as an optional
accelerated wheel, and must never shape the architecture.

## 010: speaking rule slugs, not numeric codes

Rule identifiers are kebab-case slugs naming the detected problem
(`function-length`, `over-guarded`, `file-naming`), grouped into families
for config selection (`shape`, `naming`, `defensiveness`, `structure`,
`engine`). Numeric codes (NET101) are dropped before first release. The
primary audience is an AI agent: a slug is understood inside the finding
message itself, with no `explain` lookup, no extra tokens. ESLint and
Clippy validated this at scale; ruff's numeric codes are inherited flake8
legacy. Stability rule unchanged: a published slug is never renamed.
Third-party plugin rules are prefixed (`org/no-print-in-prod`).

## 011: the calibrated profile is a ratchet

`nette calibrate` never writes a looser baseline than the committed one.
Each metric keeps its stricter side (higher annotation rate, lower guard,
try, camelCase and file-size values); only `--reset` accepts a relaxation.
Without this, an agent that degrades a repo and recalibrates turns the
degradation into the norm, which is the exact entropy the tool exists to
stop. The escape hatch stays because a legitimate style change (dropping
annotations from a generated module, a deliberate framework migration)
must remain possible, and it lands as a visible diff on `.nette/profile.json`.
A metric the new measure cannot see (calibrating a subtree with no
functions in it) keeps its previous value rather than disappearing, since
a dropped baseline is a relaxation like any other.

## 012: convention rules are declared, never calibrated

A third rule kind joins shape (universal) and intensity (calibrated):
convention, for a decision a repository makes once and then has to keep,
such as where a type lives or whether the same function may exist twice.
Convention rules never read `.nette/profile.json` and leave `Rule.baseline`
empty. The field test measured why: on a 879-file monorepo, 82% of the data
types declared outside tests already lived mixed with behaviour, so a
calibrated `mixed-module` rule would have learned that mixing is the house
style and gone silent on the debt it exists to catch. The same trap applies
to duplication. A convention rule earns its default threshold by staying
quiet on exemplary code (`duplicated-sibling`: 15 findings across 642 stdlib
modules), and remains switchable off by family in `ignore`.

## 013: the integration surface is the shell, never a protocol

nette integrates with agents through a command and an exit code, and
nothing else. `nette agent-rules` prints the block to paste into the file
the harness reads; the agent envelope carries a `run` block naming how to
rerun, what each exit code means and how to suppress honestly. An MCP
server is dropped from the roadmap: it would expose nothing the shell does
not already expose, it only reaches the clients that implement MCP, and it
adds a process and a protocol to maintain forever. Every agent has a shell.
The claim was tested: an agent handed the agent-format JSON with no
documentation at all produced the correct refactor, and named exactly two
gaps (how to rerun, whether a warning blocks), which is what the `run`
block now answers.
