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
