# Test layout

Four layers, from the design doc's test strategy (docs/design.md):

| Directory | Layer | What lives here |
|---|---|---|
| `unit/` | Unit | One file per engine module (`test_engine.py` mirrors `src/nette/engine.py`). Fast, isolated, table-driven. |
| `rules/` | Rules | One file per rule code (`test_net101.py`). Small inline snippets in, findings out. |
| `golden/` | Golden | One file per output format, diffing rendered output byte-for-byte against committed `.golden` files. |
| `corpus/` | Corpus | Regression suite over the phase 2 exemplary corpus: exemplary code must stay quiet (zero error-severity findings). |

Shared fixtures live in `conftest.py` at this level.

Run everything: `pytest`. One layer: `pytest tests/unit`.
