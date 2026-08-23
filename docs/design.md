# nette v0.1 design

nette is a code readability checker for Python, built to live inside an AI
agent's write-check-fix loop. It is deterministic, diff-aware, and
calibrated on the repository it checks. This document is the buildable
design for the first release: how the engine works, what rules ship, what
the tool looks like from the command line, and what is deliberately left
out.

The research behind every choice here lives in [vision.md](vision.md).
The architecture invariants (one AST, deterministic runtime, diff-first,
sub-second verdict) live in [.ai/architecture.md](../.ai/architecture.md)
and are assumed throughout.

## The short version

- One pipeline: discover files, check the cache, parse once, run all rules
  in a single pass, render.
- Two kinds of thresholds: universal ones (function length, nesting) with
  defaults measured on exemplary codebases, and calibrated ones (comment
  density, file size) that compare code to the repository's own profile.
- One finding model. Every output format is a thin renderer over it.
- Agents are the primary audience. The agent output format is designed
  for token economy and deterministic re-runs, not adapted from the human
  one as an afterthought.

## How a check runs

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

Each stage is a module under `src/nette/`.

**Discover** (`discovery.py`). Resolve explicit paths or `--diff` (via
git) into a file list.

**Cache** (`cache.py`). Per-file result memoization. The key is the file's
content hash plus the config hash plus the nette version. On a hit, parse
and rules are skipped entirely; the stored findings are returned.

**Parse** (`parsing.py`). One `ast.parse` and one `tokenize` stream per
file, bundled into a `SourceFile` object shared by every rule. A parse
failure produces a finding, never a crash.

**Run** (`engine.py`). A single AST walk. Each node is offered to every
active rule through `visit_<node>` dispatch. Rules accumulate findings.

**Calibrate** (`calibration.py`). Builds and reads the repo profile. Used
by calibrated rules; not in the hot path.

**Render** (`output/`). One renderer per format, all consuming the same
finding list.

Execution is sequential by default and switches to a
`ProcessPoolExecutor` above a file-count threshold (default 20,
configurable). The engine core is written mypyc-friendly: strict
annotations, `Final` constants, no dynamic dispatch tricks. Compilation
with mypyc is a release optimization, never a design dependency.

## The finding model

Everything nette reports is a `Finding`:

```python
@dataclass(frozen=True)
class Finding:
    code: str            # stable rule slug, e.g. "nesting-depth"
    message: str         # the claim: what is wrong
    grounds: str         # the why: threshold or baseline violated
    help: str            # the resolution: concrete fix direction
    severity: Severity   # error | warning | info
    file: Path
    line: int
    column: int
    end_line: int
    end_column: int
    fixable: bool = False
```

The claim/grounds/resolution split is load-bearing. For calibrated rules,
`grounds` carries the repo baseline: "repo p90 is 34 lines, this function
has 120". No finding ships a number without its context.

Rule identifiers are speaking slugs naming the detected problem, so a
finding is understandable (by a human or an agent) without a lookup. A
published slug is never renamed. Rules group into families, which is the
unit of selection in config:

| Family | Rules |
|---|---|
| `engine` | `parse-error`, `bare-allow`, `unused-allow` |
| `shape` | `function-length`, `branch-density`, `nesting-depth`, `argument-count`, `return-count` |
| `naming` | `short-name-long-scope`, `naming-drift` |
| `defensiveness` | `over-guarded`, `guard-density` |
| `annotations` | `under-annotated` |
| `docs` | reserved for v0.2 (comments and docstrings) |
| `structure` | `file-naming`, `file-size`, `mixed-module` |
| `duplication` | `duplicated-sibling` |

Third-party plugin rules (v0.2+) are prefixed with their package name
(`org/no-print-in-prod`); native slugs are never prefixed.

## Rules and thresholds

Rules fall into three threshold families. The first two came out of
measuring five exemplary codebases (httpx, pydantic, fastapi, attrs,
curated stdlib). The third came out of the field.

**Universal rules** cover code shape: function length, nesting depth,
argument count, returns per function. The exemplary corpora agree on
these within a narrow band, so the defaults are their measured p90 values.
Every default is overridable in TOML.

**Calibrated rules** cover style intensity: annotation rate, docstring
rate, comment density, defensiveness (try/getattr/isinstance density),
naming style, file size. The same corpora diverge on these by up to 12x
while all being exemplary, so no absolute threshold is defensible. A
calibrated rule fires on deviation from the repository's own profile.

**Convention rules** cover decisions a repository makes once and then has
to keep: where a type belongs, whether the same function may exist twice.
They are declared, never learned. A convention rule must not read the
profile, and `Rule.baseline` stays empty on it.

The reason is measured. On the 879-file monorepo of the field test, 82% of
the data types declared outside tests already lived mixed with behaviour
and only 18% lived in a destination module. A calibrated `mixed-module`
rule would learn that mixing is the house style and go quiet, enshrining
the exact debt the user installed the tool to stop. Duplication behaves
the same way: a repository full of near-copies would teach the rule that
near-copies are normal. Calibration answers "how intense is this repo's
style", and a convention is not an intensity.

| Kind | Example | Baseline source |
|---|---|---|
| shape | `function-length`, `nesting-depth` | universal, measured on exemplary corpora |
| intensity | `over-guarded`, `file-size` | calibrated on the repo, ratcheted |
| convention | `duplicated-sibling` | declared in TOML, never learned |

A convention rule ships on by default with a threshold conservative
enough that exemplary code stays quiet (measured, not guessed), and stays
switchable off by family in `ignore`.

Project structure rules span the families: file naming is universal
(snake_case was invariant across every corpus measured), file size is
calibrated. Both operate on the file list and the profile; neither needs
an import graph, which keeps them inside the single-pass pipeline. Deeper
structure signals (folder depth, grab-bag file growth) wait for v0.2.

### Writing a rule

A rule is a class implementing the public API. Built-in rules use the same
API as third-party ones; if the API cannot express a rule we need, the API
gets fixed.

```python
from nette import Rule, Context

class FunctionLength(Rule):
    code = "function-length"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        limit = ctx.threshold("function_length")  # TOML override or default
        ...
        ctx.report(node, message=..., grounds=..., help=...)
```

`Context` exposes thresholds, the repo profile, the current `SourceFile`
(AST, tokens, lines), and `report()`. It exposes no I/O: rules that want
the network or a subprocess get neither.

### Suppressions

`# nette: allow(function-length) reason` on the offending line or the line above
suppresses a finding. For rules whose scope is the whole file (`file-size`,
`file-naming`, `over-guarded`, `naming-drift`) the marker is accepted anywhere
in the file, since those findings are anchored on whichever construct happens
to come first and that anchor moves when the file is edited. The reason is
mandatory; a bare `allow` is itself a finding (`bare-allow`). A marker that
suppresses nothing is reported as `unused-allow`, so a suppression cannot go
stale in silence. `nette allows` lists every suppression in the tree for
audit. Honest exemption is a first-class move; silent gaming is not.

## Calibration

`nette calibrate` walks the repository (or a `--ref` baseline), computes
p50/p90/p99 for every calibrated metric, and writes
`.nette/profile.json`. The profile is committed, so CI and every agent
share the same baseline. Calibrated rules read it; when it is missing they
fall back to corpus defaults and say so in `grounds`.

The profile is resolved per file, not per run: each file is judged against
the nearest `.nette/profile.json` found walking up to the project root.
`nette calibrate PATH --local` writes one inside a subtree, so a monorepo
can give its boundary modules a baseline of their own without loosening the
repository's. Files sharing a profile are checked as one group, and the
cache key already carries the profile, so two subtrees never read each
other's cached findings.

Framework profiles are calibration overlays. `profile = "fastapi"` exempts
route-decorated functions from signature thresholds, because FastAPI
endpoints measured at args p90 = 20 in the corpus study: those parameters
are API surface, not clutter. v0.1 ships the FastAPI overlay only.

## Diff-aware mode

`nette check --diff [REF]` restricts findings to files touched by the
diff, and within them to findings whose span intersects changed lines.
The file set is computed against `git merge-base REF HEAD`, so a branch is
judged on its own commits plus the working tree, never on what moved on the
base branch since the branch point. Default `REF` is `HEAD`, which resolves to
uncommitted work. One exception: a
calibrated rule may cite whole-file context in `grounds` while anchoring
the finding to a changed line. Whole-repo mode stays available
(`nette check .`) for audit and calibration.

## Configuration

One surface: `[tool.nette]` in `pyproject.toml`, or `nette.toml` with the
same schema taking precedence. No other mechanism, no plugin
auto-discovery.

```toml
[tool.nette]
select = ["shape", "naming", "defensiveness", "structure"]  # families, explicit opt-in
ignore = ["over-guarded"]
profile = "fastapi"           # framework overlay, optional
yaml-rules = ["rules/"]       # tier 2 pattern files
plugins = ["myorg.nette_rules"]  # tier 3 modules, explicit

[tool.nette.thresholds]       # universal-family overrides
function_length = 60
nesting_depth = 4

[tool.nette.output]
format = "full"               # always explicit; no tty auto-detection
```

The YAML tier keeps the schema described in
[extensibility.md](extensibility.md); its engine compiles patterns to AST
matchers at load time. No shell, no eval, ever.

## Output formats

Five renderers over the same finding list.

**`concise`**: one line per finding, for grep and editor jump-to-error.

```
warning[function-length] src/api.py:42:1 function 'sync_users' is 120 lines long
```

**`full`**: annotated source frame in the Rust style, default for humans.
The offending code is shown as written, the problem underlined, the
grounds and fix direction below.

**`agent`**: a JSON envelope with `schema_version`, summary counts, and a
flat findings list. Each finding carries a mechanically templated
`instruction` string (composed from severity, message, location, and fix
availability), `fixable`, and grounds inline. Output is sorted and
deterministic: identical input produces identical bytes, which enables
prompt caching and meaningful diffs between agent runs.
`--max-output-tokens N` degrades deterministically: help text is dropped
first, then grounds detail, never the location or the code.

**`summary`**: one block per directory, worst first, with the three worst
files inside each. Findings cluster: on the monorepo of the field test, 87
of 127 findings sat in one service and 9 of them in one file. A flat list
reads as 127 problems; the summary reads as one integration god-file to
split.

```
127 findings in 42 files

services/accounts  87 findings in 24 files
  http_client.py  9
  serializers.py  6
  filters.py  4
```

**`json`**: the raw finding list, no reshaping.

Exit codes: `0` clean, `1` findings at error severity, `2` tool failure.

## CLI

Six subcommands. Two of them exist only to get nette into the agent's
loop: `init` and `agent-rules`.

### `nette init`

Calibrates the tree, writes `.nette/.gitignore` so the result cache never
reaches a commit, and prints the next step. One command between `pip
install` and the first verdict.

### `nette agent-rules`

Prints the block to append to `AGENTS.md`, `CLAUDE.md`, `.cursorrules` or
whatever the harness reads: when to run nette, how to read the exit code,
how to suppress honestly. The integration surface is a shell command and
an exit code, which every agent supports without a plugin. No MCP server,
no editor extension, no protocol to maintain.


### `nette check`

The core command: run the rules, print the findings.

```
nette check [PATHS...] [OPTIONS]

  PATHS                  Files or directories. Default: current directory.

  --diff [REF]           Judge only files and lines changed since REF.
                         Default REF: merge-base with the target branch.
  --format FORMAT        concise | full | summary | agent | json.
                         Default: full, or the value from config.
  --select RULES         Comma-separated rule slugs or families to run,
                         overriding config for this invocation.
  --ignore RULES         Comma-separated rule slugs to skip.
  --max-output-tokens N  Agent format only: degrade output to fit N tokens.
  --no-cache             Bypass the result cache (read and write).
  --timings              Print per-rule wall time after the report.
  --explain RULE         Print the long-form doc for one rule and exit.
```

Typical invocations:

```
nette check                        # whole tree, human output
nette check --diff                 # what did my change break
nette check --diff --format agent  # the agent loop
nette check src/api.py --timings   # one file, with rule costs
```

### `nette calibrate`

Build or refresh the repository profile.

```
nette calibrate [PATH] [OPTIONS]

  PATH          Root to measure. Default: current directory.

  --ref REF     Measure a git ref instead of the working tree, so the
                baseline can be pinned to a known-good state.
  --dry-run     Print the profile to stdout without writing it.
```

Writes `.nette/profile.json`. Commit it: the point of the profile is that
CI, every developer, and every agent judge against the same baseline.

### `nette allows`

Audit every suppression in the tree.

```
nette allows [PATHS...]
```

Lists each `# nette: allow(...)` with its file, line, rule slug, and
reason. A suppression without a reason shows up here and as a `bare-allow`
finding in `check`. A suppression that no longer silences anything shows up
in `check` as an `unused-allow` finding.

### `nette explain`

```
nette explain RULE
```

Prints the long-form documentation for a rule: what it detects, why it
matters, how the threshold or baseline works, examples that trigger it,
and how to fix or legitimately suppress it. Same content as
`check --explain`, available without running a check.

## What v0.1 ships, what it does not

**In**: the engine, the cache, diff mode, the universal shape rules,
calibration plus two calibrated rules (defensiveness, naming), two
structure rules (`file-naming`, `file-size` vs profile), the
TOML config tier, four output formats, suppressions with audit, the
FastAPI overlay, `--timings`.

**Out, deferred to v0.2+**: the YAML pattern tier, loading external Python
plugins from config (the API exists and built-ins use it; external loading
waits), the MCP server, SARIF export, autofix, watch mode,
free-threading and InterpreterPool execution backends, structure rules
beyond naming and size.

The deferrals are scope cuts, not design cuts: the rule API and the config
schema above already account for every deferred feature, so adding them
later breaks nothing. The MCP server in particular adds a
persistent-process convenience over the agent format, not a capability,
which is why the first release is CLI-only.

## Test strategy

TDD throughout; every implementation phase starts red.

- **Unit**: each rule gets table-driven tests, snippet in, findings out.
- **Golden**: each output format has golden files diffed byte-for-byte.
- **Corpus**: the exemplary corpora from the research phase run as a
  regression suite. Exemplary code must stay quiet: zero error-severity
  findings on httpx, attrs, and the stdlib picks is a hard budget.
- **Property**: cache correctness (a warm run's output is identical to a
  cold run's) and determinism (two runs produce identical bytes).

Performance gate in CI, measured before every release: `nette check` on
its own repository under 500 ms cold, under 100 ms warm.
