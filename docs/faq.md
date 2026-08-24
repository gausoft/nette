# FAQ

Short answers, with the evidence behind them. Where an answer rests on a
measurement, the measurement is named and the script that produced it is
in the repository.

## What is nette for?

Making your agent write code that matches the style your repository
already chose, and checking it in under a second on the code that just
changed.

`nette calibrate` measures five numbers on your tree (annotation rate,
guard density, `try` per kLOC, camelCase leakage, file size p90) and
writes them to a committed `.nette/profile.json`. Style rules then judge a
file against those numbers. Shape rules ship universal defaults measured
on httpx, pydantic, fastapi, attrs and a curated slice of the stdlib.

## Does nette predict bugs?

No, and we have measured it.

In August 2026 we ran a controlled ablation on five public repositories
(scrapy, poetry, celery, sqlalchemy, django, 1755 source files). Ground
truth: the 15 files per repository most touched by correction commits over
24 months. We compared nette against four other predictors.

| Predictor | precision@15 | AUC |
|---|---|---|
| nette calibrated | 0.413 | 0.829 |
| nette without profile | 0.440 | 0.802 |
| **lines of code** | **0.613** | **0.938** |
| cyclomatic complexity | 0.547 | 0.902 |
| random | 0.080 | 0.489 |

Ranking files by line count predicts correction churn better than nette
does, and within size bands the two are tied. If your goal is to guess
which files will need fixing, count the lines.

## Then what does nette measure?

Deviation from your repository's own choices, plus a set of shape limits
whose defaults were measured on exemplary code rather than invented.

We also checked whether nette's findings track what humans call readable,
using the Dorn dataset: 119 real Python snippets, each rated by around 220
developers in 2012, thousands of raters in total, none of whom knew nette
would ever exist.

The result was inconclusive, for a mechanical reason worth knowing before
you install anything: **nette said nothing at all on 88 of the 90 usable
snippets**. Its default thresholds fire on the tail of real files, and a
30-line snippet never reaches them. The longest function in the whole
corpus was 50 lines against a limit of 100.

Measured continuously, without thresholds, none of the dimensions nette
looks at correlated with the human ratings. The one dimension that did
correlate is average line length, which nette does not measure and leaves
to ruff.

## So why would I run it?

Three claims, all verifiable in ten seconds on your own tree, none of them
statistical.

**It is local.** No other linter in any language judges a file against
numbers measured on your repository. We checked fifteen languages. detekt
freezes a baseline of existing violations, `rubocop --auto-gen-config`
raises limits to match your worst file, Credo compares a file to the
codebase for spaces and tabs. None of them learns annotation rate, guard
density or file size norms, and none of them commits the result where code
review can see it move.

**Findings are actionable.** Every one names the problem, the reason and
the fix direction. Not `complexity 12 > 9`.

**It fits an agent loop.** Deterministic, cached, diff-aware, exit codes,
JSON with a ready-to-act instruction per finding, SARIF for code scanning.
Same bytes, same verdict, so runs cache and diff cleanly.

Whether the first claim actually produces better code is the experiment we
have not run yet. It is next, and its result will be published here
whatever it says.

## How is this different from ruff?

ruff checks syntax and surface style, faster than anything else, and you
should keep it. It has no notion of what your repository decided about
annotations, guards or file size. nette has no notion of import sorting or
unused variables. They run together, and nette's own CI runs both.

## How is this different from radon, lizard or SonarQube?

Those compute complexity metrics against absolute thresholds. The
disagreement is not about the arithmetic, it is about what a threshold
compares to. SonarQube also focuses on new code, which is the same
instinct as our diff mode, at server scale and commercial pricing.

## Is this an AI slop detector?

No. Slop detectors match fixed patterns of machine-written code. nette
does not know or care whether a human or an agent wrote the file, it
compares the file to the repository around it.

## Is there an MCP server?

No, and it is not planned. `nette agent-rules` prints the block you paste
into `AGENTS.md` or `CLAUDE.md`, and `--format agent` emits deterministic
JSON with a `run` block naming how to rerun and what each exit code means.
An MCP server would expose nothing the shell does not, and it only reaches
clients that speak MCP. Every agent has a shell.

## Does it call an LLM?

Never, at any point of the check path. A readability tool that returns a
different verdict on the same bytes cannot live in a fix loop and cannot
be cached.

## When not to use nette

- **You want to know which files are risky.** Count lines, or use churn
  data. Our own measurement says nette is the wrong tool for that.
- **Your repository has no consistent style yet.** Calibration measures
  what exists. On a tree with no convention it will record the absence of
  one, and the style rules will have nothing to enforce.
- **You want a quality score.** There is none, deliberately. The research
  literature has tested 121 metrics against how well developers actually
  understand code and found none that works. A single number would be a
  lie with a decimal point.
- **You need security, type or surface-style checks.** bandit, mypy and
  ruff exist and are better at their jobs than any single tool that tried
  to do all four.
- **Your code is not Python.** There is no port, and multi-language tools
  are shallow in every language, which is exactly what we are trying not
  to be.

## Where are the numbers from?

- Speed and threshold derivation: [benchmark](benchmark.md).
- Rule behaviour and suppression: [rules reference](rules/README.md).
- The two experiments above: their pre-registrations were written before
  the runs, and both are reproducible from the scripts in the repository.
