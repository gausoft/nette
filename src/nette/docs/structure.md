# Family: project structure

Structure rules judge the file, not the code inside it: what it is named
and how big it is relative to the repository. Linters traditionally stop
at file boundaries; these rules exist because AI agents drift most exactly
there (catch-all files that keep growing, `utils2.py`, modules dropped in
the wrong place).

Both rules are planned for v0.1 and not yet implemented.

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
