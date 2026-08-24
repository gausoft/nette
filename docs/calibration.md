# Calibration

Style rules have no universal right answer. `nette calibrate` measures your
tree and writes the answer your repo already gave.

## What gets measured

Five style dimensions: annotation rate, guard density, `try` density,
camelCase leakage, file size p90. They land in `.nette/profile.json`, which
you commit. Style rules then judge new code against those numbers rather
than against a universal ideal.

Other tools calibrate ceilings on code *size*. nette calibrates the style
an agent has to stay consistent with.

```
$ nette calibrate
profile written to .nette/profile.json (964 files measured)
kept the stricter baseline for annotated_function_rate (--reset to relax)
```

## The profile is a ratchet

Recalibrating on a tree that has drifted keeps the stricter of the two
values per dimension, so a repo's baseline can improve and never quietly
rot. Relaxing takes `nette calibrate --reset`, an explicit human act,
visible in the diff of the committed profile.

This is the difference with a baseline file. `rubocop --auto-gen-config`
raises the limit to match your worst file, so a repo that drifted locks the
drift into its config.

## One baseline per repo is wrong for a monorepo

A repository whose boundary modules guard on purpose gets punished by its
own average. Measured on a 7-service monorepo: the repo-wide guard rate is
12%, dominated by CRUD modules, and it is then used to judge Celery tasks
that guard 88% of their functions because an escaping exception kills the
worker. Both were right, and `over-guarded` fired forever.

Give that subtree its own baseline:

```bash
nette calibrate services/adapters --local
```

The profile lands in `services/adapters/.nette/profile.json`. Every file is
judged against the nearest profile walking up to the project root, so the
adapters answer to theirs and the rest of the repo keeps the global one.
Both are committed, both ratchet independently.

## Which rules read the profile

Calibrated rules only: `over-guarded`, `guard-density`, `under-annotated`,
`file-size`, `naming-drift`. Shape rules ship universal defaults measured on
exemplary codebases, and convention rules never read the profile at all. The
reasoning behind the three kinds is in the [rules reference](rules/README.md).
