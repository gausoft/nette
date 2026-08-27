# Family: local

Rules you declare for your own repository. nette ships with rules that
apply to any Python codebase; this family is for the conventions that
apply to yours, the ones a general tool cannot know about.

They live in `.nette/rules.toml`, next to the profile, and they are picked
up automatically. A file you wrote in your own repository is already an
explicit act, so there is no configuration key to turn them on.

TOML rather than YAML, for the same reason nette has no dependencies: the
standard library reads TOML and does not read YAML. It also means house
rules use the same format as the rest of your configuration.

## Three kinds

### `forbid-call`

A call nobody on the team should write.

```toml
[[rule]]
id = "no-raw-getattr"
kind = "forbid-call"
call = "getattr"
message = "getattr on an internal object hides a typo until runtime"
why = "internal objects have known attributes, direct access fails loudly"
fix = "access the attribute directly, or fix the type that made it optional"
```

`call` matches the dotted path of the callee. A bare name matches the tail
of a path, so `task` covers `celery.task` and `app.task`. A name that
carries a dot matches exactly, so `click.command` does not cover
`vendor.click.command`.

### `name-must-match`

A naming convention, enforced where it applies.

```toml
[[rule]]
id = "descriptive-test-names"
kind = "name-must-match"
target = "function"
files = "tests/*"
pattern = "^test_[a-z0-9_]+_when_[a-z0-9_]+$"
message = "a test name should say the scenario, not the function it calls"
why = "the name is what a failing run shows first"
fix = "rename to test_<action>_when_<condition>"
```

`target` is `function` or `class`. `pattern` is a regular expression
matched against the name. `files` is optional and restricts the rule to
paths matching a shell-style glob, taken relative to the project root,
where `*` crosses directory boundaries.

### `import-boundary`

A layer that must not reach into another.

```toml
[[rule]]
id = "services-do-not-import-api"
kind = "import-boundary"
from = "*services*"
forbid = "src.api"
message = "the service layer must not import the presentation layer"
why = "it makes the service untestable without the web framework"
fix = "pass what the service needs as an argument"
```

`from` selects the files the rule watches, same glob as above. `forbid` is
a module path; the rule fires on that module and anything under it, so
`src.api` covers `src.api.views` and leaves `src.apiary` alone.

## The three sentences are mandatory

Every rule declares `message`, `why` and `fix`. A file that omits one is
rejected at load time, naming the rule and the missing field.

This is the one place nette is deliberately inconvenient. The promise that
every finding names the problem, the reason and the fix direction is worth
nothing if the first rule a team writes reports `complexity 12 > 9`. The
friction is the point.

## How they behave

They belong to the `local` family, so `select = ["local"]` enables all of
them and `ignore = ["no-raw-getattr"]` silences one. A typo in an id is
rejected with a suggestion, like any other rule name.

They are suppressed the same way, with a reason:

```python
return getattr(payload, "total", 0)  # nette: allow(no-raw-getattr) vendor payload, keys vary
```

They show up in `nette check --timings`, so a slow house rule is visible.

Changing a rule invalidates the result cache, so editing a pattern does
not leave stale verdicts behind.

An id that collides with a built-in rule, or with another house rule, is a
configuration error rather than a warning.

## What a house rule can never do

No shell command, no evaluated Python, no network call. A rules file that
can run code turns cloning a repository into a risk, which is the lesson
of the `custom` transformer debate in ast-grep.

No regular expression over raw source text. Patterns match identifiers and
paths, never lines of code. A rule that greps the source does not need
nette.

One syntax tree, the one the engine already parsed. Never a second parser.

The one thing a rules file can still cost you is time: a pathological
regular expression on a large tree is slow. `.nette/rules.toml` carries
the same trust as `pyproject.toml`, it is written by the team that runs
nette, and `--timings` shows what each rule costs.
