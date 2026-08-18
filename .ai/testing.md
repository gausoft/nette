# Testing

## Commands

- Run the suite: `pytest`
- Run one test: `pytest tests/test_<module>.py -k <name>`

## Conventions

- Tests live in `tests/`, mirroring `src/nette/` module names
  (`src/nette/parser.py` -> `tests/test_parser.py`).
- A test name tells the scenario: `test_check_flags_function_over_threshold`,
  not `test_check_1`.
- No docstrings in tests. No mocks when a real object is cheap.
- Rule tests use small inline code snippets as fixtures, one snippet per
  behavior.
- A bug fix ships with the regression test that would have caught it.
