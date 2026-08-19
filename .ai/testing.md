# Testing

## Commands

- Run the suite: `pytest`
- Run one test: `pytest tests/test_<module>.py -k <name>`

## Conventions

- Tests live in `tests/`, in four layers (see `tests/README.md`):
  `unit/` mirrors `src/nette/` module names (`src/nette/parsing.py` ->
  `tests/unit/test_parsing.py`), `rules/` has one file per rule code,
  `golden/` diffs rendered output against committed golden files,
  `corpus/` keeps exemplary code quiet.
- Shared fixtures live in `tests/conftest.py` (e.g. `write_file`). No
  per-file `write` helpers.
- A test name tells the scenario: `test_check_flags_function_over_threshold`,
  not `test_check_1`.
- No docstrings in tests. No mocks when a real object is cheap.
- Rule tests use small inline code snippets as fixtures, one snippet per
  behavior.
- A bug fix ships with the regression test that would have caught it.
