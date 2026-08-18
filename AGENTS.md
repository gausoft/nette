# nette: agent guide

nette is a code readability tool for the AI-agent era: deterministic,
diff-aware, calibrated on the target repo, fast enough to live inside the
agent's write-check-fix loop. See [README.md](README.md) for the product
pitch and [docs/vision.md](docs/vision.md) for scope.

Read the file matching your task before planning or editing:

| Working on                        | Read first           |
| --------------------------------- | -------------------- |
| Any prose (docs, README, commits) | .ai/writing.md       |
| Any Python code                   | .ai/code-style.md    |
| Engine or rule design             | .ai/architecture.md  |
| Tests                             | .ai/testing.md       |
| Questioning a past choice         | .ai/decisions.md     |

## Commands

- Test: `pytest`
- Build: `pip install -e .`

## Boundaries

- **Always:** follow .ai/writing.md for every sentence you write; update
  the relevant .ai/ file in the same change when a rule or decision evolves.
- **Ask first:** new dependencies, changes to the public API, changes to
  .ai/architecture.md invariants.
- **Never:** commit secrets; add an LLM, network call or nondeterminism to
  the check path.
