# Family: project structure

Structure rules judge the file, not the code inside it: what it is named,
how big it is relative to the repository, and whether it keeps its data
types and its behaviour in the same place. Linters traditionally stop
at file boundaries; these rules exist because AI agents drift most exactly
there (catch-all files that keep growing, `utils2.py`, modules dropped in
the wrong place).

## `file-naming`

**Severity: warning. Universal, no threshold.**

```
warning[file-naming] src/UserService.py:1:1 file name does not follow snake_case
```

Across every exemplary corpus measured, module naming was fully uniform:
snake_case, no exceptions beyond dunder files (`__init__.py`,
`__main__.py`). A `UserService.py` or `parseHelpers.py` in a Python tree
is a strong signal of code transplanted from another language's
conventions, usually by an agent porting an example.

**Fix**: rename to snake_case (`user_service.py`) and update imports.

**Legitimate suppression**: a file whose name is imposed from outside,
such as a generated protocol module that must match an external artifact.

## `file-size`

**Severity: warning. Calibrated: compares the file's line count to the
repository's file-size profile.**

```
warning[file-size] src/models.py:1:1 this file is far larger than the rest of the repo
  grounds: it has 1840 lines; the repo p90 is 310 lines
```

File size is a repo signature, not a universal constant: the exemplary
corpora range from a 40-line median (fastapi) to 248 (httpx), and each
tolerates a few deliberate large hub files. What is worth flagging is a
file that dwarfs its own repository's norm, because that is where the
catch-all accumulation pattern shows up: the module every agent iteration
found easiest to append to.

The rule reads the file-size percentiles from `.nette/profile.json` and
fires when a file exceeds the calibrated deviation. Without a profile it
stays silent.

**Fix**: split along the seams that are already visible in the file's
section comments or class groupings. A 1800-line `models.py` is usually
four cohesive modules wearing one filename.

**Legitimate suppression**: a deliberate hub file whose size is a known,
accepted trade (a generated client, a single-file public API facade).

```python
# nette: allow(file-size) generated OpenAPI client, regenerated wholesale
```

## `mixed-module`

**Severity: warning. Convention rule, never calibrated. Threshold
`data_types_per_module`, default 2.**

```
warning[mixed-module] src/api/accounts.py:31:1
  this module holds data types and behaviour at once
  why: it declares 4 pure data types (`AccountIn`, `AccountOut`, `Segment`, `Plan`) beside its logic
  fix: move the types to a sibling module of their own (schemas.py, models.py, enums.py) and import them here
```

Nothing stops an agent from dropping five Pydantic models in the middle of
a router. Each model is individually fine, so no shape rule fires, and the
router slowly becomes the place where types live. Six months later the
types are imported from a module named after an HTTP concern.

A class counts as a pure data type when it declares no method and either
carries a data decorator (`@dataclass`, `@define`, `@frozen`), inherits a
data base (`BaseModel`, `TypedDict`, `NamedTuple`, `Enum` and friends), or
declares annotated fields only. A class whose name starts with an
underscore never counts: a private accumulator is a local implementation
detail, not a type that belongs in a shared module.

The rule fires when a module declares at least `data_types_per_module` of
them and also declares behaviour, meaning a module-level function or a
class whose methods are more than stubs. A `Protocol` of empty methods is
neither data nor behaviour. Destination modules are exempt by name, and so
is any module sitting in a destination package: `schemas.py`, `models.py`,
`enums.py`, `dto.py`, `types.py`, `constants.py`, `entities.py`,
`__init__.py`, and `schemas/anything.py`.

The default of 2 is measured. On a 879-file production monorepo it fires
on 3.5% of files, and the list is qualitatively right (a router holding 6
request and response models, a use-case file holding 7 view models). A
threshold of 1 would punish the legitimate pattern of a `Command`
declared next to the single use case that consumes it. On exemplary code
the rule is nearly silent: 6 findings across 642 stdlib modules.

**Threshold kind: convention.** On that same monorepo, 82% of the data
types declared outside tests already lived mixed with behaviour. A
calibrated version of this rule would learn that mixing is the house
style and go quiet on the debt it exists to catch.

**Fix**: move the types to a sibling module and import them back. The
message names the destination on purpose; a finding that only names the
problem gets suppressed.

**Legitimate suppression**: a command or event declared next to the single
handler that consumes it, and generated modules that must keep their
shape.

```python
# nette: allow(mixed-module) the commands belong next to their handler
```
