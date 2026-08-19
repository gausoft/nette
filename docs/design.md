# Design: nette v0.1

Phase 4 of the [roadmap](vision.md). This document turns the research
(phases 1-3) into a buildable design: architecture, public API, output
formats, config schema, and the v0.1 scope cut. Implementation starts only
after this document is reviewed.

Constraints inherited from [.ai/architecture.md](../.ai/architecture.md):
one AST, deterministic runtime, diff-first, sub-second verdict, explicit
opt-in, per-rule timing, declarative tier stays declarative, dogfooding,
actionable findings, agent-consumable output.

## Pipeline

```
paths/diff ──> discover ──> cache? ──hit──> findings
                              │miss
                              v
                       parse (ast + tokenize)
                              v
                       run rules (single pass)
                              v
                       store in cache
                              v
                    render (concise|full|agent|json)
```

Six stages, each a module under `src/nette/`:

| Stage | Module | Responsibility |
|---|---|---|
| Discover | `discovery.py` | Resolve paths or `--diff` (git) into a file list. |
| Cache | `cache.py` | Per-file result memoization. Key: content hash + config hash + nette version. Skip parse and rules on hit. |
| Parse | `parsing.py` | One `ast.parse` and one `tokenize` stream per file, bundled into a `SourceFile` object. Parse failure produces a finding, never a crash. |
| Run | `engine.py` | Single AST walk. Each node is offered to every active rule via `visit_<node>` dispatch. Rules accumulate findings. |
| Calibrate | `calibration.py` | Builds and reads the repo profile (used by calibrated rules; not in the hot path). |
| Render | `output/` | One renderer per format, all consuming the same `Finding` list. |

Execution model: sequential by default. `ProcessPoolExecutor` above a file
threshold (default 20, configurable). The engine core is written
mypyc-friendly (strict annotations, `Final`, no dynamic dispatch tricks);
compilation is a release optimization, not a design dependency.

## Data model

```python
@dataclass(frozen=True)
class Finding:
    code: str            # stable rule code, e.g. "NET102"
    message: str         # the claim: what is wrong
    grounds: str         # the why: threshold or calibrated baseline violated
    help: str            # the resolution: concrete fix direction
    severity: Severity   # error | warning | info
    file: Path
    line: int
    column: int
    end_line: int
    end_column: int
    fixable: bool = False
```

The claim/grounds/resolution split is load-bearing (FSE 2018 research,
phase 3). For calibrated rules, `grounds` carries the repo baseline:
"repo p90 is 34 lines, this function has 120". No finding ships a number
without its context.

Rule codes are stable and never renumbered. Ranges: `NET0xx` engine and
parse, `NET1xx` shape (length, nesting, args, returns), `NET2xx` naming,
`NET3xx` defensiveness and error handling, `NET4xx` comments and docs,
`ORGxxx` reserved for user plugins.

## Rules

Two threshold families (phase 2 result):

- **Universal**: function length, nesting depth, argument count, returns
  per function. Defaults derived from the phase 2 corpus benchmark
  (p90 across httpx, pydantic, fastapi, attrs, curated stdlib).
  Overridable in TOML.
- **Calibrated**: annotation rate, docstring rate, comment density,
  defensiveness (try/getattr/isinstance density), naming style. These have
  no absolute threshold; the rule fires on deviation from the repo profile.

A rule is a class implementing the public API (tier 3). Built-in rules use
the same API (dogfooding):

```python
from nette import Rule, Context

class FunctionLength(Rule):
    code = "NET101"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        limit = ctx.threshold("function_length")  # TOML override or default
        ...
        ctx.report(node, message=..., grounds=..., help=...)
```

`Context` exposes: thresholds, the repo profile (calibration data), the
current `SourceFile` (AST, tokens, lines), and `report()`. It does not
expose I/O; rules that want the network or subprocess get neither.

Suppression: `# nette: allow(NET101) reason` on the offending line or the
line above. The reason is mandatory; a bare `allow` is itself a finding
(NET001). `nette allows` lists every suppression in the tree for audit.
This is the anti-Goodhart mechanism from phase 3: honest exemption is a
first-class move, silent gaming is not.

## Calibration

`nette calibrate` walks the repo (or a `--ref` baseline), computes
p50/p90/p99 per metric, and writes `.nette/profile.json` (committed, so CI
and every agent share the same baseline). The phase 2 measurement script is
the embryo of this module. Calibrated rules read the profile; when it is
missing they fall back to corpus defaults and say so in `grounds`.

Framework profiles are calibration overlays: `profile = "fastapi"` exempts
route-decorated functions from signature thresholds (phase 2 measured
args p90 = 20 on FastAPI endpoints; they are API surface, not clutter).
v0.1 ships the FastAPI overlay only.

## Diff-aware mode

`nette check --diff [REF]` (default `REF` = merge-base with the target
branch) restricts findings to files touched by the diff, and within them to
findings whose span intersects changed lines, with one exception: a
calibrated rule may cite whole-file context in `grounds` while still
anchoring the finding to a changed line. Whole-repo mode stays available
(`nette check .`) for audit and calibration.

## Config

Single surface: `[tool.nette]` in `pyproject.toml` (or `nette.toml`, same
schema, taking precedence). No other mechanism, no plugin auto-discovery.

```toml
[tool.nette]
select = ["NET"]              # rule families to enable (explicit opt-in)
ignore = ["NET301"]
profile = "fastapi"           # framework overlay, optional
yaml-rules = ["rules/"]       # tier 2 pattern files
plugins = ["myorg.nette_rules"]  # tier 3 modules, explicit

[tool.nette.thresholds]       # universal-family overrides
function_length = 60
nesting_depth = 4

[tool.nette.output]
format = "full"               # always explicit; no tty auto-detection
```

The YAML tier (pattern rules) keeps the schema shown in
[extensibility.md](extensibility.md); its engine compiles patterns to AST
matchers at load time. No shell, no eval, ever.

## Output formats

Four renderers over the same `Finding` list (phase 3 decisions):

- `concise`: one line per finding, `severity[CODE] file:line:col message`,
  space separators (editor hyperlink compatibility).
- `full`: annotated source frame (the Rust/ruff style), default for humans.
- `agent`: JSON envelope with `schema_version`, summary counts, flat
  findings list; each finding carries a mechanically templated
  `instruction` string, `fixable`, and grounds inline. Token budget:
  `--max-output-tokens N` degrades deterministically (drop help text
  first, then grounds detail, never the location or code).
- `json`: the raw `Finding` list, no reshaping.

`--explain NETxxx` prints the long-form rule doc. Exit codes: 0 clean,
1 findings at error severity, 2 tool failure.

## CLI surface (v0.1, complete)

```
nette check [PATHS|--diff [REF]] [--format F] [--timings] [--no-cache]
nette calibrate [PATH] [--ref REF]
nette allows
nette explain CODE
```

## MCP server

Deferred to v0.2. The agent format over stdout covers the agent loop in
v0.1; MCP adds a persistent-process convenience, not a capability. Keeping
v0.1 CLI-only cuts a dependency and a protocol surface from the first
release.

## v0.1 scope cut

In: engine, cache, diff mode, universal rules (shape family), calibration
plus two calibrated rules (defensiveness, naming), TOML tier, four output
formats, suppressions, FastAPI overlay, `--timings`.

Out (v0.2+): YAML pattern tier, Python plugin loading from config (the API
exists and built-ins use it; external loading waits), MCP server, SARIF,
autofix, watch mode, free-threading/InterpreterPool backends.

The YAML tier and external plugins are deferred for scope, not design:
the rule API and config schema above already account for them, so adding
them later breaks nothing.

## Test strategy (TDD)

Every implementation phase starts red. Test layers:

- Unit: each rule gets table-driven tests (snippet in, findings out).
- Golden: each output format has golden files diffed byte-for-byte.
- Corpus: the phase 2 corpus runs as a regression suite; exemplary code
  must stay quiet (false-positive budget: zero findings at error severity
  on httpx/attrs/stdlib picks).
- Property: cache correctness (hit output identical to cold output),
  determinism (two runs, identical bytes).

Performance gate in CI: `nette check` on its own repo under 500 ms cold,
under 100 ms warm, measured before every release.
