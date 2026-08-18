# Code style

Rules for all Python code in this repository. nette's own code is the
showcase of the standard it enforces.

## Naming and structure

- Evocative names, short functions, explicit types. The signature (name,
  parameters, types) should tell the whole story.
- One module, one responsibility. Prefer small modules over god files.
- A blank line separates each group of statements doing the same logical
  step (setup, conversion, call, output). The final `return` never sticks
  to the previous block.

## Comments and docstrings

- Comments are prohibited. If code needs a comment, rewrite the code.
- Docstrings are prohibited by default, tests included. The only exception
  is a docstring with external contract value (e.g. a CLI help text).
- A test name tells the scenario. No test docstrings.

## Defensive code

- No defensive `getattr`/`hasattr` on internal objects. Direct attribute
  access. Illegal states should be unrepresentable instead.
- Catch exceptions at boundaries (I/O, subprocess, parsing user input),
  not around every call.

## Dependencies

- Standard library first. A new dependency needs a reason the stdlib
  cannot answer, and approval before adding it.

## Tests

- Every non-trivial behavior ships with a test in the same change.
- See testing.md for commands and conventions.
