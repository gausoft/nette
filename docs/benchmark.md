# Benchmark

Every number here is measured, reproducible, and dated. When a figure
comes from a private codebase, the shape of the codebase is described so
the result can be judged even though the source cannot be published.

## Speed

Measured on a 964-file FastAPI monorepo (microservices, external API
integrations), Python 3.14, M-series laptop, August 2026.

| Run | Time |
|---|---|
| `nette calibrate`, 964 files measured | 1.65 s |
| `nette check`, whole tree, cold cache | 3.1 s |
| `nette check`, whole tree, warm cache | 0.17 s |
| `nette check --diff`, the normal agent loop | under the cold number, proportional to the diff |

The cold run is the worst case: it parses every file in the repository.
The agent loop never pays it, because `--diff` judges only what changed.

CI enforces the budget on nette's own tree at every push: 1000 ms cold,
300 ms warm, and the job fails if either is exceeded. The gate is in
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml), so the number
cannot rot between releases.

## Where the thresholds come from

Five codebases the Python community treats as exemplary: httpx, pydantic,
fastapi, attrs, and a curated selection of recent stdlib modules. 183
files, about 93 000 lines, measured in 1.4 s with the same parsing path
nette uses today.

They agree on shape:

| Dimension | Across the five |
|---|---|
| Median function length | 8 to 13 lines |
| p90 function length | 35 to 55 lines |
| Arguments per function | 2 typically, rarely above 4 |
| Nesting depth | almost never above 3 |
| Returns per function | rarely above 3 |
| Single-letter names | under 10%, nearly always inside short loops |

They diverge on style, while all being exemplary:

| Dimension | Lowest | Highest |
|---|---|---|
| Functions annotated | 9% (stdlib) | 100% (httpx) |
| Functions with a docstring | 15% (fastapi) | 63% (attrs) |
| Comment density | 1x | 6x |
| Defensive density (`try` per kLOC) | 1x (fastapi) | 9x (stdlib) |

That gap is the whole argument for calibration. A universal annotation
rate would either fail httpx or excuse the stdlib. nette compares a file
to its own repository instead, which is what `nette calibrate` measures
and `.nette/profile.json` records.

## Signal density in the field

Same 964-file monorepo, judged against its own calibrated profile.

- 127 findings, on 13% of the files. A tree the team could work through,
  not a wall of red.
- 87 of the 127 sat in one service, and 9 of them in one file: a
  1224-line XML client with 25 `try` blocks for 20 functions. One
  god-file to split, reported as one cluster.
- Zero naming findings. The repository is disciplined there, and nette
  invented nothing.
- Zero false positives on FastAPI endpoint signatures, thanks to the
  framework profile.

## Cross-checked against ground truth

A readability tool that flags files nobody ever has to fix is measuring
nothing. The chosen ground truth: the 15 files most touched by `fix`
commits over 12 months, the best objective proxy for code that hurts.

- 9 of those 15 files were flagged.
- Of the 6 missed, 4 are structurally sound (configuration, schemas,
  short helpers). Their churn comes from the product moving, not from
  their shape, and flagging them would have been noise.

## Rule quietness

A rule earns its default threshold by staying quiet on code that is
already good.

| Rule | Measured |
|---|---|
| `branch-density` | fires on 1.1% of stdlib functions at the default of 12 |
| `duplicated-sibling` | 15 findings across 642 stdlib modules |
| `mixed-module` | 6 findings across 642 stdlib modules, 3.5% of an 879-file monorepo |
| `guard-density` | 2 findings across 201 stdlib modules calibrated on themselves |

## Reproducing

```bash
pip install -e .
nette calibrate path/to/repo
nette check path/to/repo --format summary
```

The measurement scripts used for the exemplary corpora live in
`docs/private/` and are not shipped, because they hardcode local paths to
the cloned corpora.
