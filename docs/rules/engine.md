# Family: engine and parse

Findings about nette's own ability to judge the code, rather than about
the code's readability.

## `parse-error`

**Severity: error.**

nette parses every file with the standard `ast` module. When a file is not
valid Python, no rule can run on it, so the parse failure itself becomes
the finding, anchored at the line the parser reported.

```
error[parse-error] src/api.py:14:8 cannot judge this file
```

A file that does not parse cannot be reviewed by anyone, human or agent.
Fix the syntax error first; every other finding for the file will appear
on the next run.

nette never crashes on broken input. An unparsable file produces exactly
one parse-error finding and the run continues with the remaining files.

**Not suppressible.** Suppressions live in comments, and comments in a
file that does not parse cannot be trusted.

## `bare-allow`

**Severity: warning.**

`# nette: allow(rule-slug)` without a reason is itself a finding. The
suppression mechanism exists for honest exemptions: code that a human
judged acceptable despite the rule. Recording why is what separates an
exemption from silent gaming of the numbers.

Bad:

```python
def sync_everything(a, b, c, d, e, f, g):  # nette: allow(argument-count)
```

Good:

```python
def sync_everything(a, b, c, d, e, f, g):  # nette: allow(argument-count) mirrors the vendor API signature
```

The reason is free text. It is displayed by `nette allows`, which audits
every suppression in the tree.

## `unused-allow`

**Severity: warning.**

A suppression marker that silences nothing is reported. Either the finding
it exempted is gone, or the code it names moved and the marker no longer
sits on the right line.

```python
# nette: allow(function-length) generated parser table
def small():
    return 1
```

```
warning[unused-allow] src/parser.py:1:0 allow(function-length) suppresses nothing
```

A stale suppression is worse than no suppression: the reason text stays in
the file, so a reader believes the case was judged and handled. This
finding is what turns a silent failure into a visible one after a
refactor.

Markers naming a rule that the current configuration does not run are left
alone, so a partial `select` does not flood the output. The same holds for a
calibrated rule when `.nette/profile.json` is missing the baseline it reads:
the rule cannot fire, so its suppressions are not judged.

For rules whose scope is the whole file (`file-size`, `file-naming`,
`over-guarded`, `naming-drift`), the marker is accepted anywhere in the
file. Those rules produce one finding per file, anchored on whatever
construct happens to come first, and that anchor moves when the file is
edited.
