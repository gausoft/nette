# Family: shape

Shape rules judge the geometry of a function: how long it is, how deep it
nests, how many arguments it takes, how many exits it has. These are
universal thresholds. Five exemplary codebases (httpx, pydantic, fastapi,
attrs, a curated stdlib selection) agree on them within a narrow band, so
the defaults come from their measured 90th percentiles, with headroom.
Every default is overridable under `[tool.nette.thresholds]`.

Shape rules measure functions, not files. All four apply to `def` and
`async def` alike, including methods.

## `function-length`

**Severity: warning. Threshold: `function_length`, default 100 lines.**

```
warning[function-length] src/sync.py:42:1 function `sync_users` is hard to take in at one glance
```

Length is counted as lines actually covered by code statements: the
docstring does not count, blank lines inside the body do not inflate the
number. A 100-line function is far beyond what exemplary code does (the
corpus median is 8 to 13 lines, p90 is 33 to 55); at that size a reader
can no longer hold the whole function in mind.

AI agents produce this failure mode constantly: one function that
accumulates fetching, validation, transformation, and persistence because
each iteration appended a step.

**Fix**: split by logical step, one step per function. The function's
comments often mark the seams; a line like `# now update the cache` is a
function boundary announcing itself.

**Legitimate suppression**: a long flat dispatch table or protocol
decoder whose steps are trivially uniform.

```python
def decode_frame(raw: bytes) -> Frame:  # nette: allow(function-length) flat wire-format decoder, one case per opcode
```

## `nesting-depth`

**Severity: warning. Threshold: `nesting_depth`, default 5 levels.**

```
warning[nesting-depth] src/sync.py:42:1 function `sync_users` nests too deeply to follow
```

Depth counts nested `if`, `for`, `while`, `with`, and `try` blocks inside
the function. Each level is a condition the reader must keep active in
working memory. Exemplary code is flat: corpus p90 is 2 to 3 levels, and
even p99 stays at 5 to 7.

**Fix**: flatten with early returns (guard clauses), or extract the inner
block into its own function. Inverting a condition and returning early
removes a level with no behavior change.

```python
# before: three levels
if user:
    if user.active:
        for order in user.orders:
            ...

# after: one
if not user or not user.active:
    return
for order in user.orders:
    ...
```

## `argument-count`

**Severity: warning. Threshold: `argument_count`, default 6 required
arguments.**

```
warning[argument-count] src/report.py:10:1 function `build_report` takes too many arguments to call safely
```

Only required arguments count: parameters with defaults are excluded, and
`self`/`cls` never count. A call site with many positional arguments is
where argument-order bugs live, and every new required parameter forces
every caller to change.

The corpus median is 2 required arguments, p90 is 3 to 5. The notable
exception is framework signatures: FastAPI endpoints measured p90 = 20
arguments because each one is injected and documented API surface. That
is what the `fastapi` profile overlay is for; with it enabled,
route-decorated functions are exempt.

**Fix**: group arguments that travel together into a dataclass, or split
the function. Three arguments that always appear together are one concept
asking to be named.

## `return-count`

**Severity: warning. Threshold: `return_count`, default 5 returns.**

```
warning[return-count] src/serializers.py:77:1 function `quote` exits from too many places
```

Counts `return` statements belonging to the function itself (nested
functions and lambdas are excluded). Guard clauses at the top are healthy;
returns scattered through the middle of a long body mean the reader must
scan everything to know what the function can produce. Corpus p90 is 2 to
3 returns.

**Fix**: converge the branches toward one or two exit points, or split
the function so each piece has an obvious single result.

return-count interacts with nesting-depth: flattening nesting with early returns adds
returns. The defaults leave room for that pattern (guard clauses plus one
main exit); a function that exceeds both limits at once is simply doing
too much.
