# Family: annotations

Annotation rules judge how a file carries type information compared to
the rest of its repository. They are calibrated rules: no absolute rate
is defensible, because a fully annotated codebase and a deliberately
untyped one are both coherent choices. The deviation worth reporting is a
file that opts out of the decision its repository already made.

Calibrated rules need a profile. Run `nette calibrate` to write
`.nette/profile.json`; without it, annotation rules stay silent.

## `under-annotated`

**Severity: warning. Baseline: `annotated_function_rate` from the repo
profile. Fires when the file annotates less than half the repo rate, with
at least 3 functions, and only in a repo that annotates at least 60% of
its functions.**

```
warning[under-annotated] src/sync.py:12:1 this file is far less annotated than the rest of the repo
  grounds: 6 of its 7 functions carry no type annotation (14% annotated); across this
  repo 92% of functions are. Bare here: `load`, `parse`, `store`, `retry`, `flush` and 1 more
```

The bare functions are named so a partial fix is possible, the same way
`over-guarded` names the guarded ones.

An agent writing a new helper in a typed module rarely annotates it: the
code runs, the tests pass, and nothing in the toolchain objects. mypy only
speaks about the code it can see types for, so an unannotated function is
precisely the one it stops checking. The debt compounds silently, one
helper at a time, until the module the team believed was typed is half
dynamic.

The rule measures the fraction of functions in the file carrying at least
one annotation, on a parameter or on the return, and compares it to the
same fraction measured across the repository at calibration time. Three
guards keep it quiet where it would be wrong:

- The repository must annotate at least 60% of its functions. Below that,
  annotating is not the local convention and the rule has nothing to
  enforce.
- The file must hold at least 3 functions. A two-function module proves
  nothing about a style.
- The file must sit under half the repo rate. A file that annotates two
  functions out of three in a 92% repo is not the problem.

Test modules (`test_*.py`, `*_test.py`, `conftest.py`) sit outside the
rule, and outside the measurement. Their functions are called by the test
runner, never by other code, so an annotation there buys no checking, and
counting them would drag the repository baseline below the convention
floor in any repo with as many test files as source files.

The baseline ratchets upward: `nette calibrate` on a tree that has drifted
keeps the higher of the two rates, so a repository's typing discipline can
improve but never quietly rot. Relaxing takes `nette calibrate --reset`.

**Fix**: annotate the parameters and the return type. Start with the
functions other modules call, they are the ones whose types propagate.

**Legitimate suppression**: a module of dynamic glue whose signatures
genuinely cannot be typed.

```python
# nette: allow(under-annotated) dynamic plugin loader, signatures come from the registry
```
