# Family: duplication

Duplication rules look at the relationship between functions, not at any
function on its own. They exist because that is where agent-written code
rots first: asked for a sixth notification sender, an agent copies the
fifth and changes three strings. Each copy is individually well shaped, so
every length, nesting and argument rule stays quiet. The debt sits between
the functions, where nothing else looks.

Measured on a 879-file production monorepo: 37 near-copy pairs across 12
files, several byte-for-byte identical in structure. The two worst files
scored zero findings from every other rule.

## `duplicated-sibling`

**Severity: warning. Universal thresholds: `duplication_similarity` (85,
a percentage) and `duplication_min_lines` (20).**

```
warning[duplicated-sibling] src/notify.py:64:1
  `send_email_change` is a near-copy of `send_password_reset` in the same scope
  why: the two share 98% of their structure over 27 lines; only names and values differ
  fix: extract what they share into one function and pass what differs as arguments
```

The rule compares functions that are siblings: declared side by side in
the same module body, or in the same class body. A function is reduced to
the sequence of its AST node types, docstring excluded, so names, string
literals, numbers and attribute paths do not count. Two functions match
when that sequence is at least `duplication_similarity` percent similar
and both are at least `duplication_min_lines` lines of code long.

Each function is reported at most once, against its closest earlier twin.
Five clones produce four findings, not ten pairs.

Comparison stops at the module boundary. Cross-module clone detection
needs an index of the whole tree, which the single-file engine does not
have, and the copy-paste-the-neighbour pattern happens inside one file.

**Test modules are exempt**: a file whose name follows the convention
(`test_*.py`, `*_test.py`, `tests.py`, `conftest.py`), or any file under a
`tests` directory of the project. Parallel test methods are near-copies by
design, the same arrange, act and assert skeleton with different data.
Measured on five public repositories, 1188 of this rule's 1201 findings
landed in test files, on scopes holding up to 255 sibling test methods. A
controlled experiment on code regularity shows that repeating one
structure improves comprehension and can compensate for length and
complexity, so those reports described a virtue. After the exemption the
rule speaks 23 times across the same five repositories.

The directory rule takes `tests` in the plural only, and reads it relative
to the project root. `test` and `testing` are the names of packages that
ship to users (`django/test`, `sqlalchemy/testing`), and an absolute path
can carry a `tests` segment far above the repository.

**Threshold kind: convention, never calibrated.** This is a convention
rule. Learning the repo's own duplication level would silence the rule on
exactly the repositories that need it most.

**Fix**: extract the shared body into one function and pass what differs
as arguments. When the difference is a behaviour rather than a value, pass
a function or use a small dispatch table.

**Legitimate suppression**: two functions whose shapes coincide by
accident (an arithmetic identity, a protocol that forces the same
skeleton), or generated code that must mirror an external artifact.
On exemplary code the rule is quiet: 15 findings across 642 stdlib
modules, all of them real near-copies such as `Decimal.min` against
`Decimal.max`.
