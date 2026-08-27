# Family: defensiveness and error handling

Defensiveness rules judge how much a file guards against its own inputs:
try blocks, `isinstance` checks, `getattr` with fallbacks. These are
calibrated rules. The exemplary corpora diverge on defensive density by an
order of magnitude (the stdlib wraps 13 try blocks per kLOC because it
parses hostile input; fastapi wraps 1.5), so no absolute threshold is
defensible. What is measurable is deviation: a file that guards far more
than the rest of its own repository.

Calibrated rules need a profile. Run `nette calibrate` to write
`.nette/profile.json`; without it, defensiveness rules stay silent.

A module that guards because it sits at a boundary (a background worker task, an outbound API
adapter, anything wrapping the network) is right to guard, and a repo-wide
baseline drawn from CRUD modules will punish it forever. Give that subtree
its own baseline with `nette calibrate path/to/subtree --local`: every file
is judged against the nearest profile found walking up to the project root.

## `over-guarded`

**Severity: warning. Baseline: `guarded_function_rate` from the repo
profile. Fires when the file's rate exceeds 3x the baseline, with at
least 3 guarded functions.**

```
warning[over-guarded] src/client.py:12:1 this file guards far more than the rest of the repo
  grounds: 9 of its 12 functions wrap code in try blocks (75%); the repo baseline is
  18% of functions. Guarded here: `fetch`, `parse`, `send`, `retry`, `close` and 4 more
```

The guarded functions are named so a partial fix is possible. Without the
names, the only actionable move on a 40-function adapter is a whole-file
suppression, which then also hides future over-guarding in that file.

Over-defensiveness is the signature failure mode of AI-generated code: a
try/except around every call, `isinstance` checks on values the type
system already guarantees, fallbacks for states that cannot occur. Each
guard adds a branch the reader must consider and, worse, hides real bugs
by converting them into silent fallbacks.

It also arrives from the other direction. A principal engineer running an
AI reviewer across 2900 pull requests a quarter reports that the tool
"actively steers less experienced engineers to write more convoluted
overly defensive code". So the guards come both from the agent that writes
and from the agent that reviews, and neither of them counts how many are
already there.

The rule measures the fraction of functions in the file containing at
least one `try` block, and compares it to the same fraction measured
across the repository at calibration time. The 3x factor and the
3-function floor keep small files and legitimately defensive files (a
retry wrapper module, a boundary adapter) from firing.

**Fix**: trust internal data and let unexpected errors surface. Keep try
blocks for real boundaries: I/O, parsing, network, subprocess. A
`KeyError` on a dict your own code built two lines above is a bug you
want loudly, at the line it happens, not silently converted to `None`
three frames later.

**Legitimate suppression**: a module whose whole job is to be a boundary.

```python
# nette: allow(over-guarded) this module wraps every vendor SDK call, guarding is its purpose
```

## `guard-density`

**Severity: warning. Baseline: `try_per_kloc` from the repo profile.
Fires when the file wraps more than 3x the repo rate of try blocks per
1000 lines, with at least 3 try blocks, and only when `over-guarded` does
not already cover the file.**

```
warning[guard-density] src/sync.py:12:1 this file stacks guards far tighter than the rest of the repo
  grounds: it wraps 9 try blocks in 256 lines (35 per 1000 lines); across this repo the
  rate is 10.59 per 1000
```

`over-guarded` counts how many functions guard. It cannot see the other
shape of the same problem: one long function wrapping every second
statement in its own try block. That file has a single guarded function,
sits below the three-function floor, and stays silent under `over-guarded`
no matter how dense it gets. `guard-density` measures the guards against
the lines instead of against the functions, so the concentration shows up.

The two rules partition the space. When a file has at least three guarded
functions and exceeds the guarded rate baseline, `over-guarded` owns it
and `guard-density` steps aside, so a dense defensive file is reported
once, not twice.

Measured on 201 stdlib modules calibrated on themselves: 2 findings.
`json/scanner.py` (3 try blocks in 73 lines) and `linecache.py` (9 in
256), both files where the density is real.

**Fix**: guard the boundary call once. A read that succeeded two lines
above does not need its own guard on the line that uses the value, and a
failure there is the same failure the first guard already describes.

**Legitimate suppression**: a module that adapts a vendor SDK call by
call, where each call fails in its own way.

```python
# nette: allow(guard-density) one guard per remote operation, each returns a different fault
```
