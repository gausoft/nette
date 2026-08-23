# Family: naming

Naming rules judge identifiers: the names of variables, functions, and
classes. Research on code comprehension is unambiguous here. Naming
quality is one of the few signals that correlates with measured
understanding (narrow-meaning identifiers nearly double comprehension
odds; single-letter identifiers take measurably longer to read), while no
size or complexity metric does on its own.

## `short-name-long-scope`

**Severity: warning. Threshold: `short_name_scope`, default 15 lines.
Universal.**

```
warning[short-name-long-scope] src/billing.py:30:5 name `r` lives too long to stay one letter
```

A one-letter name is fine where its whole life is visible at a glance: a
loop index, a comprehension target, a two-line lambda. The same name
becomes a comprehension tax when it survives across 30 lines, because
every reader who meets `r` at line 60 must scroll back to learn what it
was.

The rule measures the span between an identifier's binding and its last
use. One-letter names (except `_`) whose span exceeds the threshold fire.
Comprehension targets, loop variables of short loops, and `self`/`cls`
never fire.

**Fix**: name the thing after what it holds (`response`, `rate`, `row`).
The point is not length; `r` is a better name than
`the_http_response_object` is. The point is that a name's precision must
match its lifetime.

**Legitimate suppression**: established domain notation, such as
mathematical code where `q`, `k`, `v` are the published names of the
algorithm's terms.

```python
q, k, v = project(x)  # nette: allow(short-name-long-scope) attention notation from the paper
```

## `naming-drift`

**Severity: warning. Calibrated: compares identifier style to the repo
profile.**

```
warning[naming-drift] src/sync.py:12:1 `getUserData` breaks this repo's naming convention
  grounds: the repo names functions in snake_case (98% of 1,204 functions); this one is camelCase
```

Every exemplary corpus measured is internally consistent about naming
style. Mixed styles inside one repository are the classic transplant
signature: an agent pasted code from a tutorial, another language, or
another project, and the seam shows. Style mixing costs every future
reader a small double-take, and it compounds.

The rule reads the dominant convention per identifier kind (functions,
variables, classes, constants) from the repo profile and flags
identifiers that break it. It judges consistency with the repo, never a
style in the absolute: a fully camelCase codebase is internally fine and
produces no findings.

**Fix**: rename to the repository's convention.

**Legitimate suppression**: an identifier whose shape is imposed from
outside, such as a method overriding a third-party base class or a field
mirroring an external API payload.

```python
def visitBinOp(self, node):  # nette: allow(naming-drift) name required by the vendor visitor API
```
