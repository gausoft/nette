# NET0xx: engine and parse

Findings about nette's own ability to judge the code, rather than about
the code's readability.

## NET000: file does not parse

**Severity: error.**

nette parses every file with the standard `ast` module. When a file is not
valid Python, no rule can run on it, so the parse failure itself becomes
the finding, anchored at the line the parser reported.

```
error[NET000] src/api.py:14:8 cannot judge this file
```

A file that does not parse cannot be reviewed by anyone, human or agent.
Fix the syntax error first; every other finding for the file will appear
on the next run.

nette never crashes on broken input. An unparsable file produces exactly
one NET000 finding and the run continues with the remaining files.

**Not suppressible.** Suppressions live in comments, and comments in a
file that does not parse cannot be trusted.

## NET001: suppression without a reason

**Severity: warning.** *(planned for v0.1, not yet implemented)*

`# nette: allow(CODE)` without a reason is itself a finding. The
suppression mechanism exists for honest exemptions: code that a human
judged acceptable despite the rule. Recording why is what separates an
exemption from silent gaming of the numbers.

Bad:

```python
def sync_everything(a, b, c, d, e, f, g):  # nette: allow(NET103)
```

Good:

```python
def sync_everything(a, b, c, d, e, f, g):  # nette: allow(NET103) mirrors the vendor API signature
```

The reason is free text. It is displayed by `nette allows`, which audits
every suppression in the tree.
